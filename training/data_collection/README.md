# Public plant preparation tools

These tools keep fresh plant experiments separate from the old 15-class training script and plant checkpoints. They do not start model training, modify original archives, or confirm a biological diagnosis.

## Reproduce

Use Python with Pillow, numpy and openpyxl. The first run was performed with the bundled workspace Python runtime; the team's normal Python currently lacks openpyxl. Install the preparation requirements in a dedicated environment if running elsewhere.

```powershell
python -m pip install -r training/data_collection/requirements_preparation.txt
python training/data_collection/test_preparation.py
python training/data_collection/prepare_public.py --version v1
python training/data_collection/write_label_catalog.py --version v1
python training/data_collection/verify_prepared.py --version v1
python training/data_collection/render_annotation_review.py --version v1
python training/data_collection/freeze_prepared.py --version v1
```

If `v1` already exists, use a new version such as `v2`. Preparation refuses to overwrite an existing directory. Never rebuild into a reviewed or frozen experiment directory. Originals and acquisition inventories must be available first. The output lives in `data/plant/prepared/<version>/`, excluded from Git because it contains source photographs.

## Policy

- Ground experiments share visual grouping and split assignment. Disease folder labels are not invented box annotations. PlantDoc's ambiguous leaf names are not merged with more specific PlantWild diagnoses.
- Exact pixel duplicates with conflicting task labels/boxes enter review, not automatic majority-vote relabeling. Identical pixels with identical task annotations retain one copy. Conservative near matches stay in one split; they are not automatically deleted.
- GYMNSA uses whole capture-date holdouts, including background dates. Missing/ambiguous original-photo joins do not weaken that boundary. No claim of independent trees/farms is made.
- Potato uses source metadata labels and year/flight holdouts. Folder/metadata disagreement enters review. No Alternaria does not imply healthy, and modified-camera images are not ordinary RGB.
- Train/validation/test are prepared before augmentation. Train-only image statistics, class weights and augmentation must be enforced by the future trainer. Validation is for selection; test is reserved for final evaluation.
- `label_policy.json` lists only explicit compatible cross-task names and categories needing biological review. `label_catalog.json` preserves reversible source/export label pairs; compatibility links do not combine experiments automatically.

Inspect `PREPARATION_REPORT.md`, `preparation_report.json`, `verification.json`, `review_queue.jsonl`, `mechanical_actions.jsonl` and `annotation_review.png` in the export directory. Passing file verification establishes structural usability and the implemented grouping rules, not label correctness or field performance.

`experiment_freeze.json` records checksums for manifests, labels, configs and annotations; image checksums are in the frozen training manifest. Detector `data.yaml` files contain local absolute paths. When relocating to a GPU computer or cloud workspace, regenerate only the location-specific paths and record that change with verification; do not recreate splits or silently relabel the frozen experiment.

## Training boundary

Do not run the existing `training/train_disease.py` on these exports: it filters down to the old 15 classes and makes its own split. A new trainer must consume the frozen export as supplied, initialize a new plant head, and not reuse old plant checkpoints. Whether to initialize the backbone from general-image pretraining or entirely random weights remains a team choice. The first supported baseline is closed-set PlantWild classification, not healthy/disease triage. Source licensing and rare-class evaluation limitations remain gates for later deployment.
