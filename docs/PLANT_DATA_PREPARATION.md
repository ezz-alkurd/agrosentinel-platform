# Fresh plant models: prepared data v1

Updated 2026-10-05. The data-preparation stage is complete; **no fresh models have been trained**. Existing project models and old training data were not changed.

The new exports live in [data/plant/prepared/v1](../data/plant/prepared/v1/). The complete output report is [PREPARATION_REPORT.md](../data/plant/prepared/v1/PREPARATION_REPORT.md), with machine-readable per-class counts in [preparation_report.json](../data/plant/prepared/v1/preparation_report.json). These large source-image exports are deliberately excluded from Git; this document and the preparation tools retain the reproducible workflow.

## What is ready

| Experiment | Training | Validation | Reserved test | Label scope |
|---|---:|---:|---:|---|
| Close-range classification | 8,689 | 1,141 | 1,129 | 115 PlantWild v2 crop/condition classes |
| Close-range detection | 2,003 | 261 | 259 | 29 PlantDoc source leaf categories |
| RGB aerial pear detection | 406 | 116 | 224 | Pear rust; also includes background images |
| Specialized-camera aerial potato classification | 3,057 | 1,446 | 3,157 | Alternaria / no Alternaria |

These are four compatible **research experiments**, not a decision that the final platform needs exactly four deployed models. Models should be selected by task, viewpoint, supported crops and sensor compatibility—not simply by whether a photo arrived from a phone or an IP camera. The aerial experiments cover two specific crops/conditions, not general drone disease recognition.

## Preparation actually performed

1. Rechecked the acquired bytes and decoded all 22,492 image files. Recorded oriented-pixel hashes as well as original-byte hashes.
2. Grouped exact matches and 833 conservative near-match pairs. Related ground images share a split across PlantWild and PlantDoc. Near matches were grouped, not automatically erased.
3. Preserved original source labels. Created 147 reversible source-label definitions and 14 explicit PlantDoc-to-PlantWild name links in `label_catalog.json`. The links do not merge box and image-label training tasks.
4. Set aside 332 ambiguous images: 260 PlantWild images with conflicting pixel-identical labels; 70 PlantDoc images with missing/inconsistent geometry or conflicting box annotations; two potato folder/metadata disagreements.
5. Omitted 272 redundant exact-pixel copies whose task annotations agree. Source archives remain intact. Every source image has a disposition in `inventory.jsonl`.
6. Normalized EXIF orientation for 16 PlantDoc exports, rescaled boxes from matching-aspect-ratio source dimensions in three images, and clipped six very small aerial box-boundary excursions. Every action is recorded. The 19 adjusted PlantDoc image previews were inspected for coarse box/image alignment; this is not specialist confirmation of disease or exhaustive annotation quality.
7. Exported 21,888 candidate research images into classification folders or paired YOLO image/label directories. No blanket resizing, augmentation or fabricated healthy labels was applied.

See `training_manifest.jsonl`, `review_queue.jsonl`, `mechanical_actions.jsonl`, `near_duplicate_candidates.jsonl`, and `annotation_review.png` for details. Unresolved records are preserved in manifests rather than silently dropped from accounting. Three PlantDoc annotation-table references have no source image and therefore cannot become image records; they remain in the original acquisition audit.

## Evaluation design

- Ground datasets use joint visual-group assignment, seed 42, targeting 80/10/10 while prioritizing class coverage. All 115 classifier classes appear in every split. The PlantDoc spider-mite category has insufficient independent examples for all three splits and must not be advertised as reliably evaluated.
- GYMNSA is split by entire capture date. Validation uses 2022-07-14 positives and 2023-09-05 backgrounds; test uses 2022-08-17 positives and 2023-08-30 backgrounds. Other dates train. Its supplied random split was not reused. Source-photo metadata was examined read-only; missing/ambiguous joins fall back to whole-date grouping, not guesses. This test also changes positive camera system and season, so it is a combined domain-shift test.
- Potato trains on 2019-08-02 and 2019-08-05, validates on 2019-08-08, and reserves all 2022 imagery for test. Patches from an original image and flight do not cross splits. Repeated plots can still occur across dates; this is not an unseen-farm test.
- Similarity checks cannot find every crop/re-encoding, nor prove independent plants or farms. No source offers a verified independent Jordan deployment test. Public-source evaluation is not proof of performance on any user camera.
- Augmentation, normalization statistics, class weighting and model selection must use training/validation only. Do not tune on reserved test images or use their results to choose thresholds repeatedly. If reviews lead to label changes, version and refreeze the whole experiment before training.

## Checks and remaining gates

Five synthetic preparation-policy tests passed. The classification folders were loaded successfully using the existing PyTorch/torchvision installation: 115 ground classes and two aerial-potato classes, with matching class IDs across all splits. Sample tensors decoded successfully. The loader's temporary 224-pixel resize was a structural smoke check, not a chosen production training transform.

The export verifier checks full image decoding, image checksums, geometry, paired labels, coordinate bounds/round trips, split/class counts, and exact/pixel/visual-group and aerial flight/source-photo split isolation. Consult `verification.json` for the run outcome; verification is structural, not biological validation.

Both detector configurations parsed successfully and all 25,006 exported box class IDs matched their source-label mappings. `experiment_freeze.json` records manifest/config/annotation checksums, while the training manifest retains every image checksum. New label decisions or splits require a new experiment version. Detector config paths are location-specific and need an audited path-only change after transfer to another machine.

Important gaps before deployment:

- **No healthy class exists in the new exports.** PlantWild contains disease/condition categories; unspecified PlantDoc leaves and potato “no Alternaria” cannot substitute for healthy plants. Obtain properly labeled healthy examples before healthy/disease triage, plus nonplant/unknown-condition examples for rejection evaluation.
- **67 of the 115 PlantWild classes have fewer than 10 test images.** Start with a research baseline and report per-class support, macro metrics and uncertainty; do not treat every class as production-ready.
- PlantWild includes a noninfectious condition such as blossom-end rot. PlantDoc includes pests and unspecified leaf categories. Predictions must not imply that every condition is an infection or recommend treatment automatically.
- The potato camera is modified and NIR-sensitive. Keep that research experiment separate from consumer-drone RGB claims.
- Ground-box rescaling relies on unchanged framing. Full-resolution team review and specialist label checking remain desirable before promoting the detector experiment.
- PlantWild's listed CC BY-NC-ND 4.0 license needs particular care. These originals are copied unchanged for local research. Do not assume permission for commercial deployment, redistributing modified data, or derived-model distribution; seek clarification when that use is planned. Other collected sources list CC BY 4.0 and require attribution.

The installed PyTorch build is CPU-only (`2.11.0+cpu`) and reports CUDA unavailable. This does not establish whether the computer physically lacks a GPU, but this environment cannot currently perform CUDA training. A GPU-capable local environment or a team-selected GPU service is the practical next training choice; no cloud account, payment or upload has been initiated.

## Next step

Prepare a **new** close-range classification trainer consuming this frozen export. Do not reuse `training/train_disease.py`: it selects the old 15 classes and generates a different split. Do not load old plant checkpoints. The team should distinguish a new plant model fine-tuned from a general-image pretrained backbone from an entirely random-weight model; both are fresh plant experiments, but their compute and data needs differ.

Begin with a small sanity run on training/validation only, then a full baseline. Select augmentation and input resolution from validation evidence, compute imbalance handling from train only, and preserve the actual label order with the exported model. Report macro-F1/per-class recall for classification and detection metrics by capture date/camera for aerial boxes. Do not equate high public-data accuracy with reliable farm diagnosis.

Reproduction commands and preparation-only dependencies are in [training/data_collection/README.md](../training/data_collection/README.md). All source URLs, pinned versions and licensing notes are preserved in the full export report and acquisition receipts.

## Dataset sources

- [PlantWild project](https://tqwei05.github.io/PlantWild/) / [pinned archive repository](https://huggingface.co/datasets/uqtwei2/PlantWild/tree/527a72eb8f00c95e41698bb09d982c7d4625dce3).
- [PlantDoc object detection](https://github.com/pratikkayal/PlantDoc-Object-Detection-Dataset), commit `4730a233a555b30ee98e0879c63ad25d82407455`.
- [GYMNSA v1](https://data.mendeley.com/datasets/44kjgc4gkc/1).
- [Potato Alternaria UAV imagery](https://zenodo.org/records/10727413).
