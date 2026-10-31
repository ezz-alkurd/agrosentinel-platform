"""Create conservative, reproducible research exports; never change source archives.

Dependencies: Pillow, numpy, openpyxl. No model training or biological relabeling.
Example: python training/data_collection/prepare_public.py --version v1
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from PIL import Image, ImageOps

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / "data" / "plant"
SEED = 42
SPLITS = ("train", "val", "test")
TASKS = {
    "plantwild-v2": "ground_classification",
    "plantdoc": "ground_detection",
    "gymnsa": "aerial_pear_detection",
    "potato-uav": "aerial_potato_special_sensor",
}


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def slug(value):
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")


class Groups:
    def __init__(self, size):
        self.parent = list(range(size))

    def find(self, index):
        if self.parent[index] != index:
            self.parent[index] = self.find(self.parent[index])
        return self.parent[index]

    def join(self, left, right):
        left, right = self.find(left), self.find(right)
        if left != right:
            self.parent[max(left, right)] = min(left, right)


def fingerprint(raw):
    with Image.open(io.BytesIO(raw)) as source:
        orientation = source.getexif().get(274, 1)
        image = ImageOps.exif_transpose(source).convert("RGB")
        width, height = image.size
        pixel = hashlib.sha256(f"{width}x{height}:RGB:".encode() + image.tobytes()).hexdigest()
        thumb = np.asarray(image.resize((16, 16), Image.Resampling.LANCZOS), dtype=np.float32)
        gray = np.asarray(image.convert("L").resize((32, 32), Image.Resampling.LANCZOS), dtype=np.float64)
        k = np.arange(8)[:, None]
        x = np.arange(32)[None, :]
        transform = np.cos(np.pi * (2 * x + 1) * k / 64)
        transform[0] *= 1 / math.sqrt(2)
        coeffs = (transform @ gray @ transform.T).ravel()[1:]
        bits = coeffs > np.median(coeffs)
        phash = sum(int(bit) << i for i, bit in enumerate(bits))
        small = np.asarray(image.convert("L").resize((9, 8), Image.Resampling.LANCZOS))
        dbits = (small[:, 1:] > small[:, :-1]).ravel()
        dhash = sum(int(bit) << i for i, bit in enumerate(dbits))
        return {"pixel_sha256": pixel, "phash": phash, "dhash": dhash,
                "oriented_width": width, "oriented_height": height,
                "exif_orientation": orientation}, thumb


def read_gym_metadata(archive):
    name = next(n for n in archive.namelist() if n.endswith(".xlsx"))
    workbook = load_workbook(io.BytesIO(archive.read(name)), read_only=True, data_only=True)
    joined = defaultdict(list)
    sheets = []
    for sheet in workbook:
        if sheet.title == "Structure":
            continue
        rows = iter(sheet.values)
        header = [str(v).strip() if v is not None else "" for v in next(rows)]
        count = 0
        for values in rows:
            row = dict(zip(header, values))
            if not row.get("Image_ID"):
                continue
            keep = {key: row.get(key) for key in ("Image_ID", "DateTimeOriginal", "CreateDate",
                    "Model", "RelativeAltitude", "GroundSamplingDistance")}
            keep["source_sheet"] = sheet.title
            joined[str(row["Image_ID"])].append(keep)
            count += 1
        sheets.append({"sheet": sheet.title, "metadata_rows": count})
    workbook.close()
    return joined, {"archive_member": name, "sheets": sheets,
                    "duplicate_image_ids": [k for k, v in joined.items() if len(v) > 1]}


def near_groups(rows, archives, groups):
    """Conservative candidate grouping, not near-duplicate deletion or proof of independence."""
    bands = defaultdict(list)
    pixels = {}
    byte_groups = {}
    fingerprints, thumbs, matches = [], [], []
    for i, row in enumerate(rows):
        raw = archives[row["archive"]].read(row["archive_member"])
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise RuntimeError(f"Source bytes changed: {row['id']}")
        info, thumb = fingerprint(raw)
        row.update(info)
        sha = row["sha256"]
        if sha in byte_groups:
            groups.join(i, byte_groups[sha])
        else:
            byte_groups[sha] = i
        if info["pixel_sha256"] in pixels:
            groups.join(i, pixels[info["pixel_sha256"]])
        else:
            pixels[info["pixel_sha256"]] = i
        # Five bands cover 63 pHash bits. <=4 bit differences guarantee one unchanged band.
        keys = [(band, (info["phash"] >> offset) & ((1 << length) - 1))
                for band, (offset, length) in enumerate(((0, 13), (13, 13), (26, 13), (39, 12), (51, 12)))]
        candidates = set(j for key in keys for j in bands[key])
        for j in sorted(candidates):
            other = fingerprints[j]
            if info["pixel_sha256"] == other["pixel_sha256"]:
                continue
            ratio = info["oriented_width"] / info["oriented_height"]
            ratio2 = other["oriented_width"] / other["oriented_height"]
            if abs(ratio / ratio2 - 1) > 0.02:
                continue
            hamming = (info["phash"] ^ other["phash"]).bit_count()
            if hamming > 4 or (info["dhash"] ^ other["dhash"]).bit_count() > 6:
                continue
            mse = float(np.mean((thumb - thumbs[j]) ** 2))
            if mse <= 200:
                groups.join(i, j)
                matches.append({"left": rows[j]["id"], "right": row["id"],
                                "phash_distance": hamming, "thumbnail_rgb_mse": round(mse, 4)})
        for key in keys:
            bands[key].append(i)
        fingerprints.append(info)
        thumbs.append(thumb)
        if (i + 1) % 1000 == 0:
            print(f"Fingerprint checks: {i + 1}/{len(rows)}", flush=True)
    return matches


def validate_pd(row, fixes):
    annotations = row["source_annotations"]
    if not annotations:
        return "missing_annotation_table_entry"
    dims = {(int(b["width"]), int(b["height"])) for b in annotations}
    target = row["oriented_width"], row["oriented_height"]
    if len(dims) != 1 or any(w <= 0 or h <= 0 for w, h in dims):
        return "inconsistent_or_zero_annotation_dimensions"
    source = next(iter(dims))
    if source != target and abs((source[0] / source[1]) / (target[0] / target[1]) - 1) > 0.005:
        return "annotation_geometry_requires_visual_review"
    if row["exif_orientation"] != 1:
        # Source coordinates must already refer to oriented dimensions. Otherwise do not guess.
        if source != target:
            return "exif_annotation_reference_requires_review"
        fixes.append({"id": row["id"], "action": "exif_transpose_image_to_annotation_frame",
                      "orientation": row["exif_orientation"], "source_dimensions": source,
                      "export_dimensions": target})
    boxes = []
    for number, b in enumerate(annotations, 1):
        coords = [float(b[k]) for k in ("xmin", "ymin", "xmax", "ymax")]
        x1, y1, x2, y2 = coords
        if not all(math.isfinite(v) for v in coords) or not (0 <= x1 < x2 <= source[0] and 0 <= y1 < y2 <= source[1]):
            return "invalid_source_box_requires_review"
        normalized = [x1 / source[0], y1 / source[1], x2 / source[0], y2 / source[1]]
        boxes.append({"source_class": b["class"], "xyxy": normalized})
    if source != target:
        fixes.append({"id": row["id"], "action": "rescale_boxes_from_source_dimensions",
                      "source_dimensions": source, "export_dimensions": target,
                      "assumption": "same framing; aspect ratios match within 0.5%; visual sign-off pending"})
    row["prepared_boxes"] = boxes
    return None


def validate_gym(row, archive, fixes):
    boxes = []
    for number, line in enumerate(archive.read(row["annotation_member"]).decode("utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            return "invalid_yolo_row"
        cls, x, y, w, h = map(float, parts)
        if cls != 0 or not all(math.isfinite(v) for v in (x, y, w, h)) or w <= 0 or h <= 0:
            return "invalid_yolo_values"
        before = [x - w / 2, y - h / 2, x + w / 2, y + h / 2]
        after = [max(0.0, before[0]), max(0.0, before[1]), min(1.0, before[2]), min(1.0, before[3])]
        excursion = max(abs(a - b) for a, b in zip(before, after))
        if excursion > 0.001 or not (after[0] < after[2] and after[1] < after[3]):
            return "box_requires_visual_review"
        if excursion > 0.000002:
            fixes.append({"id": row["id"], "action": "clip_small_boundary_excursion",
                          "source_line": number, "before_xyxy": before, "after_xyxy": after,
                          "maximum_pixels_clipped": excursion * row["width"]})
        boxes.append({"source_class": "pear_rust", "xyxy": after})
    row["prepared_boxes"] = boxes
    return None


def ground_splits(rows):
    """Joint splits protect shared ground-source images across both experiments."""
    buckets = defaultdict(list)
    supports = defaultdict(set)
    totals = Counter()
    for row in rows:
        buckets[row["leakage_group"]].append(row)
        for label in row["labels"]:
            key = f"{row['task']}:{label}"
            supports[key].add(row["leakage_group"])
            totals[key] += 1
    order = lambda key: digest(f"{SEED}:{key}")
    assignment = {}
    # Ensure training coverage first, then reserve val/test examples where independent groups permit.
    for split in SPLITS:
        for label in sorted(supports, key=lambda k: (len(supports[k]), k)):
            available = supports[label]
            if split != "train" and len(available) < 3:
                continue
            if any(assignment.get(g) == split for g in available):
                continue
            candidate = next((g for g in sorted(available, key=order) if g not in assignment), None)
            if candidate is not None:
                assignment[candidate] = split
    current = {s: Counter() for s in SPLITS}
    labels_by_group = {}
    for group, members in buckets.items():
        labels_by_group[group] = Counter(f"{r['task']}:{label}" for r in members for label in r["labels"])
        if group in assignment:
            current[assignment[group]].update(labels_by_group[group])
    ratios = {"train": 0.8, "val": 0.1, "test": 0.1}
    for group in sorted(buckets, key=order):
        if group in assignment:
            continue
        labels = labels_by_group[group]
        # Weighted normalized deficit: aim for 80/10/10, never break a group to hit exact counts.
        scores = {s: sum((ratios[s] * totals[k] - current[s][k]) / max(1, ratios[s] * totals[k])
                         * v for k, v in labels.items()) for s in SPLITS}
        chosen = max(SPLITS, key=lambda s: scores[s])
        assignment[group] = chosen
        current[chosen].update(labels)
    for row in rows:
        row["split"] = assignment[row["leakage_group"]]


def export_row(row, out, archive, label_ids):
    task = out / row["task"]
    raw = archive.read(row["archive_member"])
    suffix = Path(row["archive_member"]).suffix.lower()
    if row["task"] in {"ground_classification", "aerial_potato_special_sensor"}:
        relative = Path(row["task"]) / row["split"] / row["labels"][0] / (row["id"] + suffix)
    else:
        relative = Path(row["task"]) / "images" / row["split"] / (row["id"] + suffix)
    path = out / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if row["task"] == "ground_detection" and row["exif_orientation"] != 1:
        path = path.with_suffix(".jpg")
        relative = relative.with_suffix(".jpg")
        with Image.open(io.BytesIO(raw)) as image:
            ImageOps.exif_transpose(image).convert("RGB").save(path, quality=95)
    else:
        path.write_bytes(raw)
    row["export_path"] = relative.as_posix()
    row["export_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    if "prepared_boxes" in row:
        lines = []
        for box in row["prepared_boxes"]:
            x1, y1, x2, y2 = box["xyxy"]
            cls = label_ids[row["task"]][slug(box["source_class"])]
            lines.append(f"{cls} {(x1+x2)/2:.9f} {(y1+y2)/2:.9f} {x2-x1:.9f} {y2-y1:.9f}")
        label_path = task / "labels" / row["split"] / (row["id"] + ".txt")
        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        row["export_label_path"] = label_path.relative_to(out).as_posix()


def run(version):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", version):
        raise ValueError("Version must be a simple directory name")
    out = ROOT / "prepared" / version
    if out.exists():
        raise RuntimeError(f"Refusing to overwrite existing export: {out}")
    rows = []
    for name in ("acquired_images.jsonl", "next_batch_images.jsonl"):
        for line in (ROOT / "manifests" / name).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            row["id"] = row["dataset"] + "_" + digest(row["archive"] + "::" + row["archive_member"])[:20]
            row["task"] = TASKS[row["dataset"]]
            rows.append(row)
    archives = {name: zipfile.ZipFile(ROOT / name) for name in sorted({r["archive"] for r in rows})}
    try:
        gym = next(a for n, a in archives.items() if "/gymnsa/" in n)
        metadata, meta_report = read_gym_metadata(gym)
        groups = Groups(len(rows))
        matches = near_groups(rows, archives, groups)
        fixes = []
        for row in rows:
            problem = None
            if row["dataset"] == "plantwild-v2":
                row["labels"] = [slug(row["source_folder_label"])]
            elif row["dataset"] == "plantdoc":
                problem = validate_pd(row, fixes)
                row["labels"] = sorted({slug(b["class"]) for b in row["source_annotations"]})
            elif row["dataset"] == "potato-uav":
                row["labels"] = ["alternaria" if row["source_label"] == "1" else "no_alternaria"]
                if Path(row["archive_member"]).parent.name != row["source_label"]:
                    problem = "folder_and_metadata_label_disagree"
                row["split"] = "test" if "/2022/" in ("/" + row["archive_member"]) else (
                    "val" if row["flight_group"].endswith("20190808") else "train")
            else:
                problem = validate_gym(row, archives[row["archive"]], fixes)
                row["labels"] = ["pear_rust"] if row.get("prepared_boxes") else []
                date = re.search(r"\d{4}_\d{2}_\d{2}", Path(row["archive_member"]).name).group()
                row["flight_group"] = f"gymnsa:{date}"
                joined = metadata.get(Path(row["archive_member"]).name, [])
                row["uav_metadata"] = joined
                row["metadata_join_status"] = "unique" if len(joined) == 1 else "ambiguous" if joined else "missing"
                # Whole date holdouts work even when source-frame metadata is absent/ambiguous.
                row["source_image_group"] = "gymnsa:" + date + ":" + (
                    str(joined[0].get("DateTimeOriginal")) if len(joined) == 1 and joined[0].get("DateTimeOriginal")
                    else "metadata_incomplete_date_group")
                row["split"] = "test" if date in {"2022_08_17", "2023_08_30"} else (
                    "val" if date in {"2022_07_14", "2023_09_05"} else "train")
            row["status"] = "quarantine" if problem else "eligible"
            if problem:
                row["exclusion_reason"] = problem
        # Pixel-identical, conflicting labels/box annotations are ambiguous, not automatically corrected.
        pixels = defaultdict(list)
        for row in rows:
            if row["status"] == "eligible":
                pixels[(row["task"], row["pixel_sha256"])].append(row)
        for members in pixels.values():
            if len(members) < 2:
                continue
            signatures = {json.dumps(sorted((b["source_class"], [round(v, 5) for v in b["xyxy"]])
                                for b in r.get("prepared_boxes", [])), sort_keys=True)
                          if "prepared_boxes" in r else json.dumps(r["labels"]) for r in members}
            if len(signatures) > 1:
                for row in members:
                    row.update(status="quarantine", exclusion_reason="pixel_identical_conflicting_annotations")
            else:
                keeper = min(members, key=lambda r: r["id"])
                for row in members:
                    if row is not keeper:
                        row.update(status="duplicate_omitted", duplicate_of=keeper["id"])
        # Biological aliases across ground tasks are NOT guessed. Group overlap despite differing labels.
        for i, row in enumerate(rows):
            row["leakage_group"] = "visual:" + rows[groups.find(i)]["id"]
        ground = [r for r in rows if r["status"] == "eligible" and r["task"].startswith("ground_")]
        ground_splits(ground)
        # Do not move a source flight between splits to rescue visual matches; quarantine overlap instead.
        fixed = defaultdict(list)
        for row in rows:
            if row["status"] == "eligible" and row["task"].startswith("aerial_"):
                fixed[(row["task"], row["leakage_group"])].append(row)
        for members in fixed.values():
            if len({r["split"] for r in members}) > 1:
                for row in members:
                    row.update(status="quarantine", exclusion_reason="visual_group_crosses_flight_holdout")
        eligible = [r for r in rows if r["status"] == "eligible"]
        label_ids = {}
        for task in sorted(TASKS.values()):
            labels = sorted({label for r in rows if r["task"] == task for label in r["labels"]})
            label_ids[task] = {label: i for i, label in enumerate(labels)}
        out.mkdir(parents=True)
        for task, labels in label_ids.items():
            folder = out / task
            folder.mkdir(parents=True)
            for split in SPLITS:
                if "detection" in task:
                    (folder / "images" / split).mkdir(parents=True)
                    (folder / "labels" / split).mkdir(parents=True)
                else:
                    for label in labels:
                        (folder / split / label).mkdir(parents=True)
            write_json(folder / "labels.json", {"names": labels, "label_status": "source_not_expert_revalidated"})
            if "detection" in task:
                config = f"path: {json.dumps(str(folder.resolve()).replace(chr(92), '/'))}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n"
                config += "".join(f"  {i}: {label}\n" for label, i in labels.items())
                (folder / "data.yaml").write_text(config, encoding="utf-8")
        for i, row in enumerate(eligible, 1):
            export_row(row, out, archives[row["archive"]], label_ids)
            if i % 1000 == 0:
                print(f"Exported: {i}/{len(eligible)}", flush=True)
        summaries = {}
        for task in sorted(TASKS.values()):
            selected = [r for r in rows if r["task"] == task]
            accepted = [r for r in selected if r["status"] == "eligible"]
            counts = {split: {"images": sum(r["split"] == split for r in accepted),
                             "boxes": sum(len(r.get("prepared_boxes", [])) for r in accepted if r["split"] == split),
                             "background_images": sum(not r["labels"] for r in accepted if r["split"] == split)} for split in SPLITS}
            per_label = {label: {split: sum(label in r["labels"] and r["split"] == split for r in accepted)
                                  for split in SPLITS} for label in label_ids[task]}
            summaries[task] = {"source_images": len(selected), "status_counts": dict(Counter(r["status"] for r in selected)),
                "exclusion_reasons": dict(Counter(r.get("exclusion_reason") for r in selected if r["status"] == "quarantine")),
                "splits": counts, "class_counts": per_label,
                "labels_without_all_three_splits": [label for label, c in per_label.items() if not all(c.values())],
                "classes_with_fewer_than_10_test_images": [label for label, c in per_label.items() if c["test"] < 10]}
        report = {"version": version, "seed": SEED, "source_image_files": len(rows), "exports": len(eligible),
                  "tasks": summaries, "near_duplicate_candidate_pairs": len(matches), "metadata": meta_report,
                  "mechanical_actions": dict(Counter(f["action"] for f in fixes)),
                  "policy": "Research candidates, not expert-validated labels or deployment certification"}
        write_json(out / "preparation_report.json", report)
        write_jsonl(out / "inventory.jsonl", rows)
        write_jsonl(out / "training_manifest.jsonl", eligible)
        write_jsonl(out / "review_queue.jsonl", [r for r in rows if r["status"] == "quarantine"])
        write_jsonl(out / "mechanical_actions.jsonl", fixes)
        write_jsonl(out / "near_duplicate_candidates.jsonl", matches)
        write_report(out, report)
        print(json.dumps({"export_directory": str(out), "exports": len(eligible),
                          "tasks": {task: {"status_counts": info["status_counts"], "splits": info["splits"],
                                             "labels_without_all_three_splits": info["labels_without_all_three_splits"]}
                                    for task, info in summaries.items()}}, indent=2), flush=True)
    finally:
        for archive in archives.values():
            archive.close()


def write_report(out, report):
    lines = [f"# Plant training data preparation — {report['version']}", "", "Prepared: 2026-10-05. Research candidates; no models trained.", "",
             "Original archives and acquisition manifests were not changed. Exports copy original images except PlantDoc EXIF-orientation normalization. No blanket resizing, augmentation, synthetic labels or healthy-label inference was applied.", "",
             "## Prepared experiments", "", "| Experiment | Train images | Validation images | Test images | Quarantined | Duplicate copies omitted |", "|---|---:|---:|---:|---:|---:|"]
    for task, info in report["tasks"].items():
        c = info["splits"]
        lines.append(f"| {task} | {c['train']['images']} | {c['val']['images']} | {c['test']['images']} | {info['status_counts'].get('quarantine', 0)} | {info['status_counts'].get('duplicate_omitted', 0)} |")
    lines += ["", "## What these experiments mean", "",
        "- **Ground classification:** PlantWild v2's 115 crop/condition folders, mechanically standardized names only. No healthy class and no biological label review. Many classes have tiny test sets; counts appear in preparation_report.json. This is a closed-set research baseline, not a healthy-versus-disease triage model.",
        "- **Ground detection:** PlantDoc source box classes are preserved separately from classifier labels. Unqualified crop-leaf labels do not mean healthy. Ambiguous source names are not merged with diseases. This experiment detects source leaf categories, not all PlantWild conditions.",
        "- **Aerial pear detection:** RGB GYMNSA pear-rust boxes plus empty background files. All 10 capture dates remain whole. Test: 2022-08-17 positive flight plus 2023-08-30 background flight; validation: 2022-07-14 plus 2023-09-05 background. Other dates train. Test therefore also changes positive camera system (Zenmuse P1); results must be broken down by camera/date and cannot isolate sensor from season. Original-photo metadata was read, but incomplete/ambiguous joins were not guessed.",
        "- **Aerial potato classification:** modified RGB/NIR-sensitive camera patches; train 2019-08-02 and 2019-08-05; validation 2019-08-08; test all 2022 dates. `no_alternaria` is not `healthy`. Repeated plots can occur across dates. This is a temporal/year-domain holdout, not an independent Jordan-farm test or an ordinary RGB-drone benchmark.",
        "", "## Leakage controls and limitations", "",
        f"All {report['source_image_files']:,} archive images were decoded and byte hashes checked against acquisition records. Exact byte and oriented-pixel matches were grouped globally. Conservative pHash/dHash and RGB-thumbnail checks identified {report['near_duplicate_candidate_pairs']:,} near-match pairs; these are kept in one split, not deleted as alleged duplicates. Such checks miss some crops/re-encodings and cannot establish independence of plants/farms.",
        "Ground classification and detection use joint visual groups to protect overlapping public images across experiments. The intended ground ratio is 80/10/10, seed 42, with class coverage taking priority over exact ratios. All eligible images from one visual group receive the same split. Fixed aerial flight/year boundaries are retained; visual groups crossing those boundaries are quarantined. No augmentation precedes splitting. A frozen test set must not be used to select models, epochs, thresholds or label edits.",
        "", "## Repairs and exclusions", "",
        "`mechanical_actions.jsonl` records each orientation adjustment, source-dimension box rescaling and small GYMNSA boundary clip. Rescaling assumes unchanged framing and matching aspect ratio; its small review subset needs visual sign-off before a final detector run. Box excursions over 0.1% are rejected, not clipped automatically. Source labels are intact in the original archives.",
        "`review_queue.jsonl` contains unresolved image labels/geometry, conflicting pixel-identical annotations and cross-flight visual overlaps. All occurrences of conflicting exact annotations within an experiment are quarantined. Identical pixels with identical task annotations retain one representative. The two potato folder/metadata disagreements are excluded without guessing a new label; their separately stored, metadata-consistent counterparts remain eligible.",
        "", "## Files and next training step", "",
        "- `training_manifest.jsonl`: exported image path, source provenance, task, labels, split, grouping, hashes and source annotations.",
        "- `inventory.jsonl`: every acquired image and its disposition, including omitted copies and review items.",
        "- `preparation_report.json`: complete per-class and split counts, repair totals and metadata-join audit.",
        "- Classifiers: `train/<class>`, `val/<class>`, `test/<class>` and `labels.json`. Detector experiments: paired `images/<split>`, `labels/<split>` and `data.yaml`.",
        "", "First run the independent export verifier. Next select a small pretrained-image-backbone baseline with a newly initialized plant head, or a from-random-weights comparison if fresh means no pretrained backbone. Do not reuse old plant checkpoints. Compute normalization/imbalance weights from train only; augment train only; choose hyperparameters on val; open test once for the selected experiment. Add independently sourced healthy, nonplant and unknown-condition examples before healthy/disease triage, then obtain Jordan-field/device validation before deployment.",
        "", "## Sources and license restrictions", "",
        "- [PlantDoc object detection](https://github.com/pratikkayal/PlantDoc-Object-Detection-Dataset), pinned commit 4730a233a555b30ee98e0879c63ad25d82407455. CC BY 4.0; retain attribution and original web-image provenance where available.",
        "- [PlantWild project](https://tqwei05.github.io/PlantWild/) and [pinned dataset repository](https://huggingface.co/datasets/uqtwei2/PlantWild/tree/527a72eb8f00c95e41698bb09d982c7d4625dce3). Repository lists CC BY-NC-ND 4.0. Originals copied unchanged. Local research exports do not authorize redistribution, commercial deployment, or distribution of adaptations; obtain clarification for those uses and any derived-model licensing questions.",
        "- [GYMNSA v1](https://data.mendeley.com/datasets/44kjgc4gkc/1), CC BY 4.0; source UAV metadata workbook preserved inside archive.",
        "- [Potato Alternaria UAV](https://zenodo.org/records/10727413), CC BY 4.0.", ""]
    (out / "PREPARATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v1")
    run(parser.parse_args().version)
