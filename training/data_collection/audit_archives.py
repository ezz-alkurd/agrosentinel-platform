"""Inventory acquired ZIPs without altering originals or assigning training splits.

Uses Pillow to verify image structure. Reports source labels and annotation issues;
does not establish biological correctness or detect every visual near duplicate.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2] / "data" / "plant"
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def read_csv(archive, name):
    text = archive.read(name).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text, newline="")))


def main():
    summaries, hash_groups = [], defaultdict(list)
    output = ROOT / "manifests"
    output.mkdir(parents=True, exist_ok=True)
    with (output / "acquired_images.jsonl").open("w", encoding="utf-8") as manifest:
        for path in sorted((ROOT / "originals").rglob("*.zip")):
            dataset = path.relative_to(ROOT / "originals").parts[0]
            if dataset not in {"plantdoc", "potato-uav"}:
                continue  # Later collections use audit_next_batch.py and their own label adapters.
            with zipfile.ZipFile(path) as archive:
                names = [info.filename for info in archive.infolist() if not info.is_dir()
                         and "__MACOSX/" not in info.filename
                         and not Path(info.filename).name.startswith("._")]
                image_names = [n for n in names if Path(n).suffix.lower() in EXTS]
                csv_names = [n for n in names if n.lower().endswith(".csv")]
                tables = {n: read_csv(archive, n) for n in csv_names}
                labels_by_name = defaultdict(list)
                if dataset == "potato-uav":
                    for table in tables.values():
                        for row in table:
                            if row.get("Original_name"):
                                labels_by_name[row["Original_name"]].append(row)
                else:
                    for table_name, table in tables.items():
                        table_split = "TRAIN" if Path(table_name).name == "train_labels.csv" else "TEST"
                        for row in table:
                            if row.get("filename"):
                                labels_by_name[(table_split, row["filename"])].append(row)
                summary = {"dataset": dataset, "archive": str(path.relative_to(ROOT)),
                           "image_files": len(image_names), "readable_images": 0,
                           "images_without_table_entry": [], "invalid_images": [],
                           "invalid_boxes": [], "folder_label_mismatches": [], "conflicting_metadata_labels": [],
                           "csv_tables": {n: {"rows": len(rows), "columns": list(rows[0]) if rows else []}
                                          for n, rows in tables.items()}}
                sizes, labels, dates, groups = Counter(), Counter(), Counter(), set()
                for name in image_names:
                    data = archive.read(name)
                    sha = hashlib.sha256(data).hexdigest()
                    observation = f"{path.relative_to(ROOT).as_posix()}::{name}"
                    hash_groups[sha].append(observation)
                    record = {"dataset": dataset, "archive": path.relative_to(ROOT).as_posix(),
                              "archive_member": name, "sha256": sha, "split": "unassigned",
                              "label_status": "source_annotation_not_expert_revalidated"}
                    try:
                        with Image.open(io.BytesIO(data)) as image:
                            record.update(width=image.width, height=image.height, mode=image.mode)
                            image.verify()
                        summary["readable_images"] += 1
                        sizes[f"{record['width']}x{record['height']}"] += 1
                    except Exception as error:
                        summary["invalid_images"].append({"file": name, "error": str(error)})
                        record["image_status"] = "invalid"
                    source_split = "TRAIN" if "/TRAIN/" in name else "TEST" if "/TEST/" in name else None
                    lookup = Path(name).name if dataset == "potato-uav" else (source_split, Path(name).name)
                    rows = labels_by_name.get(lookup, [])
                    record["source_annotations"] = rows
                    if not rows:
                        summary["images_without_table_entry"].append(name)
                    if dataset == "potato-uav":
                        record.update(crop="potato", sensor="modified_RGB_NIR_sensitive", viewpoint="aerial_patch")
                        if rows:
                            row = rows[0]
                            year = name.split("/")[0]
                            group = f"potato-uav:{year}:{row.get('Date')}:{row.get('Image')}"
                            record.update(source_image_group=group,
                                          flight_group=f"potato-uav:{year}:{row.get('Date')}",
                                          plot_group=f"potato-uav:{year}:{row.get('Plot')}",
                                          source_label=row.get("Label"),
                                          condition="alternaria" if row.get("Label") == "1" else "no_alternaria")
                            if row.get("Label") not in {"0", "1"}:
                                record["condition"] = "unmapped"
                            if len({r.get("Label") for r in rows}) > 1:
                                summary["conflicting_metadata_labels"].append(name)
                                record["condition"] = "unmapped"
                                record["label_status"] = "conflicting_source_annotations"
                            labels[row.get("Label")] += 1
                            dates[row.get("Date")] += 1
                            groups.add(group)
                            if Path(name).parent.name != row.get("Label"):
                                summary["folder_label_mismatches"].append(name)
                    else:
                        record.update(sensor="RGB", viewpoint="ground_field_or_web_image",
                                      source_image_group=f"plantdoc:{sha}",
                                      source_split=source_split)
                        classes = [row.get("class") for row in rows]
                        record["source_classes"] = classes
                        labels.update(classes)
                        groups.add(record["source_image_group"])
                        for row in rows:
                            try:
                                x1, y1, x2, y2 = [float(row[key]) for key in ("xmin", "ymin", "xmax", "ymax")]
                                width, height = record["width"], record["height"]
                                if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                                    summary["invalid_boxes"].append({"image": name, "annotation": row})
                            except (KeyError, ValueError):
                                summary["invalid_boxes"].append({"image": name, "annotation": row,
                                                                  "reason": "could not validate box"})
                    manifest.write(json.dumps(record, ensure_ascii=False) + "\n")
                if dataset == "potato-uav":
                    observed_keys = {Path(n).name for n in image_names}
                else:
                    observed_keys = {("TRAIN" if "/TRAIN/" in n else "TEST" if "/TEST/" in n else None,
                                      Path(n).name) for n in image_names}
                summary["table_references_without_image"] = [n for n in labels_by_name if n not in observed_keys]
                summary.update(image_sizes=dict(sizes), source_label_counts=dict(labels),
                               flight_date_counts=dict(dates), source_image_groups=len(groups))
                summaries.append(summary)
                print(f"{path.name}: {summary['readable_images']} readable images; "
                      f"{len(summary['images_without_table_entry'])} without metadata/labels; "
                      f"{len(summary['invalid_boxes'])} questionable boxes", flush=True)
    report = {"archives": summaries,
              "exact_duplicate_groups": [v for v in hash_groups.values() if len(v) > 1],
              "unique_image_byte_hashes": len(hash_groups),
              "limitations": ["Image verification does not confirm disease labels", "Only byte-identical duplicates detected",
                              "Source group metadata must be reviewed before choosing splits", "No training split assigned"]}
    with (output / "acquisition_audit.json").open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(f"Reports: {output}")


if __name__ == "__main__":
    main()
