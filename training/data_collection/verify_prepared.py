"""Independently validate exported files, labels, accounting and split boundaries."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2] / "data" / "plant" / "prepared"


def verify(folder):
    report = json.loads((folder / "preparation_report.json").read_text(encoding="utf-8"))
    inventory = [json.loads(line) for line in (folder / "inventory.jsonl").read_text(encoding="utf-8").splitlines()]
    manifest = [json.loads(line) for line in (folder / "training_manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    check(len(inventory) == report["source_image_files"], "Inventory count disagrees with acquisition count")
    check(len({r["id"] for r in inventory}) == len(inventory), "Source IDs are not unique")
    check(len(manifest) == report["exports"], "Export count mismatch")
    check({r["id"] for r in inventory if r["status"] == "eligible"} == {r["id"] for r in manifest}, "Eligible/manifest IDs disagree")
    check(all(r["status"] in {"eligible", "quarantine", "duplicate_omitted"} for r in inventory), "Unaccounted disposition")
    global_groups = defaultdict(set)
    flights = defaultdict(set)
    source_images = defaultdict(set)
    expected_paths = set()
    counted = defaultdict(Counter)
    boxes_count = Counter()
    labels = {task: json.loads((folder / task / "labels.json").read_text(encoding="utf-8"))["names"] for task in report["tasks"]}
    for i, row in enumerate(manifest, 1):
        path = (folder / row["export_path"]).resolve()
        check(path.is_relative_to(folder.resolve()), f"Export path escapes its directory: {row['id']}")
        if not path.is_file():
            errors.append(f"Missing image: {row['id']}")
            continue
        check(row["split"] in ("train", "val", "test"), f"Invalid split: {row['id']}")
        check(all(label in labels[row["task"]] for label in row["labels"]), f"Unknown class: {row['id']}")
        expected_paths.add(path)
        counted[row["task"]][row["split"]] += 1
        for key in ("sha256", "pixel_sha256", "leakage_group"):
            global_groups[(key, row[key])].add(row["split"])
        if row["task"].startswith("aerial_"):
            flights[row["flight_group"]].add(row["split"])
            source_images[row["source_image_group"]].add(row["split"])
        raw = path.read_bytes()
        check(hashlib.sha256(raw).hexdigest() == row["export_sha256"], f"Export checksum mismatch: {row['id']}")
        if row["task"] != "ground_detection" or row["exif_orientation"] == 1:
            check(row["export_sha256"] == row["sha256"], f"Unexpected image mutation: {row['id']}")
        with Image.open(path) as image:
            oriented = ImageOps.exif_transpose(image)
            check(oriented.size == (row["oriented_width"], row["oriented_height"]), f"Export geometry mismatch: {row['id']}")
            oriented.load()
        if "export_label_path" in row:
            label_path = folder / row["export_label_path"]
            check(label_path.is_file(), f"Missing label: {row['id']}")
            if label_path.is_file():
                lines = [line for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]
                check(len(lines) == len(row["prepared_boxes"]), f"Box count mismatch: {row['id']}")
                boxes_count[row["task"]] += len(lines)
                for line, source_box in zip(lines, row["prepared_boxes"]):
                    values = line.split()
                    check(len(values) == 5, f"Malformed YOLO line: {row['id']}")
                    if len(values) != 5:
                        continue
                    cls, x, y, w, h = map(float, values)
                    check(cls.is_integer() and 0 <= cls < len(labels[row["task"]]), f"Invalid class ID: {row['id']}")
                    expected_label = re.sub(r"[^a-z0-9]+", "_", source_box["source_class"].lower()).strip("_")
                    check(cls == labels[row["task"]][expected_label], f"Class mapping mismatch: {row['id']}")
                    check(all(math.isfinite(v) for v in (x, y, w, h)), f"Nonfinite box: {row['id']}")
                    check(w > 0 and h > 0 and x-w/2 >= -1e-8 and y-h/2 >= -1e-8 and x+w/2 <= 1+1e-8 and y+h/2 <= 1+1e-8,
                          f"Invalid exported box: {row['id']}")
                    recovered = [x-w/2, y-h/2, x+w/2, y+h/2]
                    check(max(abs(a-b) for a,b in zip(recovered, source_box["xyxy"])) <= 1e-8, f"Box round trip mismatch: {row['id']}")
        if i % 2000 == 0:
            print(f"Verified exported images: {i}/{len(manifest)}", flush=True)
    for kind, values in (("visual/hash", global_groups), ("flight", flights), ("source photograph", source_images)):
        for group, splits in values.items():
            check(len(splits) == 1, f"Cross-split {kind} leakage: {group}: {sorted(splits)}")
    for task, info in report["tasks"].items():
        check(sum(info["status_counts"].values()) == info["source_images"], f"Unreconciled source count: {task}")
        for split, counts in info["splits"].items():
            check(counted[task][split] == counts["images"], f"Reported split count mismatch: {task}/{split}")
        actual_images = {p.resolve() for p in (folder / task).rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}}
        expected = {p for p in expected_paths if p.is_relative_to((folder / task).resolve())}
        check(actual_images == expected, f"Untracked or missing images: {task}")
        if "detection" in task:
            paths = list((folder / task / "labels").rglob("*.txt"))
            check(len(paths) == sum(counted[task].values()), f"Image-label pairing count mismatch: {task}")
            check(boxes_count[task] == sum(c["boxes"] for c in info["splits"].values()), f"Total box count mismatch: {task}")
        else:
            for label in labels[task]:
                for split in ("train", "val", "test"):
                    check(info["class_counts"][label][split] > 0, f"Empty classifier class needs loader policy: {task}/{split}/{label}")
    result = {"passed": not errors, "verified_images": len(manifest), "source_images_accounted": len(inventory),
              "checked": ["source/export counts", "export checksums", "full image decode", "orientation/geometry",
                          "paired labels", "box bounds and coordinate round trip", "class coverage",
                          "global exact/pixel/visual split isolation", "aerial flight/source-photo isolation"],
              "errors": errors,
              "limitations": ["Does not validate biological labels", "Does not prove all visual duplicates were found",
                              "Does not establish independent farms/trees or deployment accuracy"]}
    (folder / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    if not args.version or not all(c.isalnum() or c in "_-" for c in args.version):
        parser.error("Use a simple version directory name")
    raise SystemExit(verify(ROOT / args.version))
