# Plant training data preparation — v1

Prepared: 2026-10-05. Research candidates; no models trained.

Original archives and acquisition manifests were not changed. Exports copy original images except PlantDoc EXIF-orientation normalization. No blanket resizing, augmentation, synthetic labels or healthy-label inference was applied.

## Prepared experiments

| Experiment | Train images | Validation images | Test images | Quarantined | Duplicate copies omitted |
|---|---:|---:|---:|---:|---:|
| aerial_pear_detection | 406 | 116 | 224 | 0 | 0 |
| aerial_potato_special_sensor | 3057 | 1446 | 3157 | 2 | 0 |
| ground_classification | 8689 | 1141 | 1129 | 260 | 269 |
| ground_detection | 2003 | 261 | 259 | 70 | 3 |

## What these experiments mean

- **Ground classification:** PlantWild v2's 115 crop/condition folders, mechanically standardized names only. No healthy class and no biological label review. Many classes have tiny test sets; counts appear in preparation_report.json. This is a closed-set research baseline, not a healthy-versus-disease triage model.
- **Ground detection:** PlantDoc source box classes are preserved separately from classifier labels. Unqualified crop-leaf labels do not mean healthy. Ambiguous source names are not merged with diseases. This experiment detects source leaf categories, not all PlantWild conditions.
- **Aerial pear detection:** RGB GYMNSA pear-rust boxes plus empty background files. All 10 capture dates remain whole. Test: 2022-08-17 positive flight plus 2023-08-30 background flight; validation: 2022-07-14 plus 2023-09-05 background. Other dates train. Test therefore also changes positive camera system (Zenmuse P1); results must be broken down by camera/date and cannot isolate sensor from season. Original-photo metadata was read, but incomplete/ambiguous joins were not guessed.
- **Aerial potato classification:** modified RGB/NIR-sensitive camera patches; train 2019-08-02 and 2019-08-05; validation 2019-08-08; test all 2022 dates. `no_alternaria` is not `healthy`. Repeated plots can occur across dates. This is a temporal/year-domain holdout, not an independent Jordan-farm test or an ordinary RGB-drone benchmark.

## Leakage controls and limitations

All 22,492 archive images were decoded and byte hashes checked against acquisition records. Exact byte and oriented-pixel matches were grouped globally. Conservative pHash/dHash and RGB-thumbnail checks identified 833 near-match pairs; these are kept in one split, not deleted as alleged duplicates. Such checks miss some crops/re-encodings and cannot establish independence of plants/farms.
Ground classification and detection use joint visual groups to protect overlapping public images across experiments. The intended ground ratio is 80/10/10, seed 42, with class coverage taking priority over exact ratios. All eligible images from one visual group receive the same split. Fixed aerial flight/year boundaries are retained; visual groups crossing those boundaries are quarantined. No augmentation precedes splitting. A frozen test set must not be used to select models, epochs, thresholds or label edits.

## Repairs and exclusions

`mechanical_actions.jsonl` records each orientation adjustment, source-dimension box rescaling and small GYMNSA boundary clip. Rescaling assumes unchanged framing and matching aspect ratio; its small review subset needs visual sign-off before a final detector run. Box excursions over 0.1% are rejected, not clipped automatically. Source labels are intact in the original archives.
`review_queue.jsonl` contains unresolved image labels/geometry, conflicting pixel-identical annotations and cross-flight visual overlaps. All occurrences of conflicting exact annotations within an experiment are quarantined. Identical pixels with identical task annotations retain one representative. The two potato folder/metadata disagreements are excluded without guessing a new label; their separately stored, metadata-consistent counterparts remain eligible.

## Files and next training step

- `training_manifest.jsonl`: exported image path, source provenance, task, labels, split, grouping, hashes and source annotations.
- `inventory.jsonl`: every acquired image and its disposition, including omitted copies and review items.
- `preparation_report.json`: complete per-class and split counts, repair totals and metadata-join audit.
- Classifiers: `train/<class>`, `val/<class>`, `test/<class>` and `labels.json`. Detector experiments: paired `images/<split>`, `labels/<split>` and `data.yaml`.

First run the independent export verifier. Next select a small pretrained-image-backbone baseline with a newly initialized plant head, or a from-random-weights comparison if fresh means no pretrained backbone. Do not reuse old plant checkpoints. Compute normalization/imbalance weights from train only; augment train only; choose hyperparameters on val; open test once for the selected experiment. Add independently sourced healthy, nonplant and unknown-condition examples before healthy/disease triage, then obtain Jordan-field/device validation before deployment.

## Sources and license restrictions

- [PlantDoc object detection](https://github.com/pratikkayal/PlantDoc-Object-Detection-Dataset), pinned commit 4730a233a555b30ee98e0879c63ad25d82407455. CC BY 4.0; retain attribution and original web-image provenance where available.
- [PlantWild project](https://tqwei05.github.io/PlantWild/) and [pinned dataset repository](https://huggingface.co/datasets/uqtwei2/PlantWild/tree/527a72eb8f00c95e41698bb09d982c7d4625dce3). Repository lists CC BY-NC-ND 4.0. Originals copied unchanged. Local research exports do not authorize redistribution, commercial deployment, or distribution of adaptations; obtain clarification for those uses and any derived-model licensing questions.
- [GYMNSA v1](https://data.mendeley.com/datasets/44kjgc4gkc/1), CC BY 4.0; source UAV metadata workbook preserved inside archive.
- [Potato Alternaria UAV](https://zenodo.org/records/10727413), CC BY 4.0.
