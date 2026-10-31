"""Attach reversible source label semantics to an existing prepared export."""
import argparse
import json
from pathlib import Path

from prepare_public import ROOT, slug, write_json


def catalog(version):
    policy = json.loads(Path(__file__).with_name("label_policy.json").read_text(encoding="utf-8"))
    folder = ROOT / "prepared" / version
    rows = [json.loads(line) for line in (folder / "inventory.jsonl").read_text(encoding="utf-8").splitlines()]
    labels = []
    wild = sorted({r["source_folder_label"] for r in rows if r["dataset"] == "plantwild-v2"})
    for name in wild:
        crop = next((c for c in policy["crop_prefixes"] if name.startswith(c + " ")), None)
        if not crop:
            raise ValueError(f"No crop prefix for {name}")
        labels.append({"dataset": "plantwild-v2", "source_label": name, "export_label": slug(name),
                       "crop": crop, "source_condition": name[len(crop) + 1:],
                       "condition_kind": "noninfectious_disorder" if name in policy["plantwild_noninfectious_condition"] else "source_disease_category",
                       "healthy": False, "biological_validation": "pending"})
    pd = sorted({b["class"] for r in rows if r["dataset"] == "plantdoc" for b in r["source_annotations"]})
    for name in pd:
        link = policy["plantdoc_classification_links"].get(name)
        if link and link not in wild:
            raise ValueError(f"Unknown classification link: {link}")
        kind = "condition_unspecified" if name in policy["plantdoc_condition_unspecified"] else (
            "pest" if name in policy["plantdoc_pest"] else "ambiguous_condition" if name in policy["plantdoc_requires_condition_review"] else "source_disease_category")
        labels.append({"dataset": "plantdoc", "source_label": name, "export_label": slug(name),
                       "condition_kind": kind, "compatible_classification_label": slug(link) if link else None,
                       "healthy": None, "biological_validation": "pending"})
    labels += [
        {"dataset": "gymnsa", "source_label": "GYMNSA", "export_label": "pear_rust", "crop": "pear",
         "condition_kind": "source_disease_category", "source_condition": "Gymnosporangium sabinae", "healthy": False},
        {"dataset": "potato-uav", "source_label": "0", "export_label": "no_alternaria", "crop": "potato",
         "condition_kind": "target_absent_including_background", "healthy": None},
        {"dataset": "potato-uav", "source_label": "1", "export_label": "alternaria", "crop": "potato",
         "condition_kind": "source_disease_category", "healthy": False}
    ]
    write_json(folder / "label_catalog.json", {"policy": policy, "labels": labels,
               "warning": "A healthy:false diseased source class is not a model-wide healthy decision. No prepared healthy class exists. Cross-task links do not turn image labels into box labels."})
    print(f"Catalog: {len(labels)} source label definitions; {len(policy['plantdoc_classification_links'])} explicit cross-task links")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    if not args.version or not all(c.isalnum() or c in "_-" for c in args.version):
        parser.error("Use a simple version directory name")
    catalog(args.version)
