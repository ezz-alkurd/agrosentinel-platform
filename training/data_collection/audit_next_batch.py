"""Check PlantWild v2 and GYMNSA archives without changing source data.

Requires Pillow. Produces a separate acquisition inventory, not training splits.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2] / "data" / "plant"
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def check_yolo(text):
    boxes, problems = [], []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            parts = line.split()
            if len(parts) != 5:
                raise ValueError("expected class and four coordinates")
            cls = int(parts[0])
            x, y, w, h = [float(value) for value in parts[1:]]
            if cls != 0 or not all(math.isfinite(v) for v in (x, y, w, h)):
                raise ValueError("unexpected class or nonfinite coordinate")
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                raise ValueError("invalid normalized coordinates")
            # Tolerate rounding in six-decimal YOLO exports.
            if min(x - w / 2, y - h / 2) < -0.000002 or max(x + w / 2, y + h / 2) > 1.000002:
                raise ValueError("box extends outside image")
            boxes.append([cls, x, y, w, h])
        except ValueError as error:
            problems.append({"line": number, "text": line, "error": str(error)})
    return boxes, problems


def main():
    output = ROOT / "manifests"
    output.mkdir(parents=True, exist_ok=True)
    previous = defaultdict(list)
    old_manifest = output / "acquired_images.jsonl"
    if old_manifest.exists():
        with old_manifest.open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                previous[row["sha256"]].append(f"{row['archive']}::{row['archive_member']}")
    summaries, hashes, overlap = [], defaultdict(list), []
    with (output / "next_batch_images.jsonl").open("w", encoding="utf-8") as manifest:
        for dataset in ("plantwild-v2", "gymnsa"):
            archives = sorted((ROOT / "originals" / dataset).rglob("*.zip"))
            if not archives:
                raise RuntimeError(f"Completed archive not available for {dataset}")
            for path in archives:
                with zipfile.ZipFile(path) as archive:
                    files = [n for n in archive.namelist() if not n.endswith("/") and "__MACOSX/" not in n
                             and not Path(n).name.startswith("._")]
                    file_set = set(files)
                    images = [n for n in files if Path(n).suffix.lower() in EXTS]
                    summary = {"dataset": dataset, "archive": path.relative_to(ROOT).as_posix(),
                               "image_files": len(images), "readable_images": 0, "invalid_images": [],
                               "missing_annotation_files": [], "invalid_yolo_annotations": [],
                               "positive_images": 0, "empty_label_images": 0, "valid_boxes": 0,
                               "metadata_files": [n for n in files if Path(n).suffix.lower() in {".csv", ".xlsx", ".yaml", ".yml", ".json"}]}
                    classes, splits, sizes, groups = Counter(), Counter(), Counter(), Counter()
                    for name in images:
                        raw = archive.read(name)
                        sha = hashlib.sha256(raw).hexdigest()
                        key = f"{path.relative_to(ROOT).as_posix()}::{name}"
                        hashes[sha].append(key)
                        if sha in previous:
                            overlap.append({"new": key, "previous": previous[sha]})
                        record = {"dataset": dataset, "archive": path.relative_to(ROOT).as_posix(),
                                  "archive_member": name, "sha256": sha, "split": "unassigned",
                                  "label_status": "source_annotation_not_expert_revalidated"}
                        try:
                            with Image.open(io.BytesIO(raw)) as image:
                                record.update(width=image.width, height=image.height, mode=image.mode)
                                image.verify()
                            summary["readable_images"] += 1
                            sizes[f"{record['width']}x{record['height']}"] += 1
                        except Exception as error:
                            summary["invalid_images"].append({"file": name, "error": str(error)})
                            record["image_status"] = "invalid"
                        if dataset == "plantwild-v2":
                            label = Path(name).parent.name
                            classes[label] += 1
                            record.update(source_folder_label=label, viewpoint="close_range_or_field",
                                          source_image_group=f"plantwild-v2:{sha}")
                        else:
                            label_name = str(Path(name.replace("/images/", "/labels/")).with_suffix(".txt")).replace("\\", "/")
                            record.update(crop="pear", sensor="RGB", viewpoint="aerial",
                                          condition="pear_rust", annotation_member=label_name)
                            supplied_split = "train" if "/train/" in name else "val" if "/val/" in name else "unrecognized"
                            splits[supplied_split] += 1
                            record["source_split"] = supplied_split
                            # Only the date is inferred here. Source-tree/image joins require Excel metadata review.
                            date = "_".join(Path(name).stem.split("_")[:3])
                            record["capture_date_candidate"] = date
                            record["source_image_group"] = f"gymnsa:{sha}"
                            groups[date] += 1
                            if label_name not in file_set:
                                summary["missing_annotation_files"].append(name)
                                record["label_status"] = "annotation_missing"
                            else:
                                text = archive.read(label_name).decode("utf-8-sig")
                                boxes, problems = check_yolo(text)
                                record["boxes"] = boxes
                                record["annotation_errors"] = problems
                                summary["valid_boxes"] += len(boxes)
                                if text.strip():
                                    summary["positive_images"] += 1
                                else:
                                    summary["empty_label_images"] += 1
                                if problems:
                                    summary["invalid_yolo_annotations"].append({"image": name, "problems": problems})
                    # Track only data image folders, not documentation; parent labels need source-version review.
                        manifest.write(json.dumps(record, ensure_ascii=False) + "\n")
                    summary.update(source_folder_label_counts=dict(classes), source_split_counts=dict(splits),
                                   image_sizes=dict(sizes), capture_date_candidates=dict(groups))
                    summaries.append(summary)
                    print(f"{dataset}: {summary['readable_images']} readable images; "
                          f"{len(classes)} source image folders; {summary['valid_boxes']} valid boxes", flush=True)
    report = {"archives": summaries, "exact_duplicate_groups": [v for v in hashes.values() if len(v) > 1],
              "exact_overlap_with_first_batch": overlap, "unique_image_byte_hashes": len(hashes),
              "limitations": ["No biological label revalidation", "Only byte-identical duplicates detected",
                              "No training splits assigned", "Aerial source-image/tree grouping still needs metadata review"]}
    with (output / "next_batch_audit.json").open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(f"Reports: {output}")


if __name__ == "__main__":
    main()
