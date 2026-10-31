# Plant data collection workspace

Started: 2026-10-03 (Asia/Amman).

The platform should accept many image sources. A dataset is admitted to a particular model only after checking its crop, condition, viewpoint, sensor and annotation type. Collect original data before making training exports.

## First public-data batch

1. PlantDoc object detection: retain all crop classes for the initial inventory. Use reviewed leaf boxes to make classification crops later if appropriate. Preserve original source-image grouping and existing split metadata. Source: https://github.com/pratikkayal/PlantDoc-Object-Detection-Dataset
2. Potato Alternaria UAV: retain both years and the metadata tables. This is a modified camera sensitive to near infrared, with very fine image resolution; it is an aerial research baseline, not proof of performance on an ordinary RGB drone. Label 0 means no Alternaria, which can include background; it must not become `potato_healthy`. Source: https://zenodo.org/records/10727413

Download archives with `py -3.11 training/data_collection/collect_public.py --dataset plantdoc`, `--dataset potato-uav`, `--dataset plantwild-v2`, or `--dataset gymnsa`. The collector pins GitHub/Hugging Face data to a commit, preserves version metadata, checks published hashes where provided, records SHA-256 hashes, and caps archive downloads at 2,500 MB. It preserves archives rather than automatically converting annotations or creating splits.

PlantWild v2 and GYMNSA were acquired on 2026-10-05. Their separate inventory and checks are in `manifests/next_batch_images.jsonl` and `manifests/next_batch_audit.json`. Run `py -3.11 training/data_collection/audit_next_batch.py` to regenerate those checks. The first-batch audit script covers PlantDoc and potato UAV only.

## Next sources

See `dataset_registry.json`. PlantWild v2 and GYMNSA now have research preparations in `prepared/v1`, alongside PlantDoc and potato UAV. Add Tomato-Village and PlantSeg according to the next selected training task. Collect PlantVillage as a controlled-image baseline after checking existing team copies.

PlantWild and PlantSeg share some underlying images. PlantDoc and Cropped PlantDoc are related. Merged datasets may contain copies of all of these. They require overlap checks before independent evaluation.

## Files and storage

- `originals/`: downloaded source archives, metadata and acquisition receipts; do not edit originals.
- `local-field/`: team photos and a metadata record per photo; preserve original resolution and timestamps.
- `manifests/`: image inventories, hashes, groups, reviewed labels and eventually split assignments.
- `prepared/v1/`: 21,888 candidate research exports with compatible label definitions, grouped train/validation/test splits, review queues and structural verification. Source labels still await specialist validation.

Start with `docs/PLANT_DATA_COLLECTION_PLAN.md` and use `local-field/example_record.json` as the photo record template. The template is an example, not a collected observation. The team confirmed on 2026-10-03 that no farm access or capture equipment is available yet, so local collection is pending and public data is the current activity.

An acquisition inventory is not a training manifest: use `prepared/v1/training_manifest.jsonl`, not the acquisition inventories, for the new experiments. The original acquisition inventories remain unassigned and unchanged. The new research split is recorded and verified, but labels have not been validated by a plant specialist and no fresh model has been trained. See `../../docs/PLANT_DATA_PREPARATION.md` and `prepared/v1/PREPARATION_REPORT.md` for counts, limitations and next steps.
