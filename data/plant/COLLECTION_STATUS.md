# Public plant collection: acquired and prepared for research

Updated: 2026-10-05. First batch: 2026-10-03; second batch: 2026-10-05. The team currently has no farm access or capture equipment and requested fresh plant models. This collection is separate from the old disease training data/checkpoints. No training has started. New grouped research splits and exports are now in `prepared/v1`; original acquisition inventories remain unchanged and unassigned.

## Preparation completed

All 22,492 acquired image files are accounted for: 21,888 exported, 332 quarantined for unresolved source labels/geometry, and 272 agreeing exact-pixel copies omitted. Conservative near-match checks grouped 833 candidate pairs. Export checks passed for full image decoding, hashes, geometry, labels and implemented split-isolation rules; five synthetic policy tests and classifier-loader smoke checks also passed. This is structural verification, not biological validation or independent-farm proof.

The exports cover PlantWild classification (115 classes), PlantDoc source-category detection (29 classes), RGB aerial pear-rust detection and specialized-camera aerial potato classification. They are separate research experiments. No healthy class exists in these exports; 67 PlantWild classes have fewer than 10 test images. Full results, source links and next training guidance are in `../../docs/PLANT_DATA_PREPARATION.md` and `prepared/v1/PREPARATION_REPORT.md`.

## Collected files

| Source | Files actually found in the pinned archives | Integrity checks |
|---|---|---|
| PlantDoc object detection, commit `4730a233a555b30ee98e0879c63ad25d82407455` | 2,596 readable images; 2,584 distinct image byte hashes | ZIP integrity passed; image structure verified; local SHA-256 recorded |
| Potato Alternaria, 2019 | 4,505 readable image files; 4,503 metadata rows | Published MD5 matched; ZIP integrity passed; image structure verified |
| Potato Alternaria, 2022 | 3,157 readable image files; 3,157 metadata rows | Published MD5 matched; ZIP integrity passed; image structure verified |
| PlantWild v2, commit `527a72eb8f00c95e41698bb09d982c7d4625dce3` | 11,488 readable images in 115 class folders | Published SHA-256 matched; ZIP integrity passed; image structure verified |
| GYMNSA version 1 | 746 readable RGB aerial images: 584 annotated and 162 with empty background label files | Published SHA-256 matched; ZIP integrity passed; all 746 images have matching YOLO label files |

The combined archive inventory is 22,492 image files (10,258 in the first batch and 12,234 added in the second batch). This is an acquisition count, not the number of clean independent training examples. The published potato total of 7,660 matches metadata rows; the actual archives contain 7,662 image files. Two 2019 folder labels disagree with their corresponding metadata and must be reviewed.

New archive sizes: PlantWild v2 1,640,342,849 bytes and GYMNSA 203,978,050 bytes. Original archives, metadata and acquisition receipts are under `data/plant/originals/plantwild-v2/527a72eb8f00/` and `data/plant/originals/gymnsa/1/`. GYMNSA also includes its three annotation tables and UAV metadata Excel workbook inside the archive. Sources: https://tqwei05.github.io/PlantWild/ and https://data.mendeley.com/datasets/44kjgc4gkc/1.

## Findings from acquisition (original records preserved)

- PlantDoc has 12 exact duplicate groups; 11 cross its supplied train/test split. That split cannot be accepted without review.
- PlantDoc has 18 images without matching annotation-table entries and 3 table references without matching images.
- PlantDoc has 11 bounding boxes outside the decoded image bounds or otherwise failing coordinate validation. Check source dimensions and images before choosing to repair or exclude them.
- Ground-source label names need a reviewed crop/condition mapping. The source archive contains label variants beyond common headline class counts.
- Potato labels are `Alternaria` and `no Alternaria`; no Alternaria is not equivalent to healthy potato.
- Potato imagery is from a modified RGB camera sensitive to NIR, not ordinary consumer-drone RGB.
- Labels have not been revalidated by a plant specialist. Hash checks detect exact file copies only; visual near-duplicate checks are pending.
- The second-batch audit found 385 exact duplicate groups and 72 new image records matching image bytes in the first batch. Review those records before creating independent splits.
- GYMNSA contains 16,251 source boxes. Of these, 16,245 pass the current normalized-coordinate checks; six boxes in five images extend slightly beyond an image boundary. Review their rounding/clipping before generating a training export. All source labels remain intact.
- GYMNSA's supplied split is 597 training images and 149 validation images. It has not been accepted as an independent test of new flights/trees. Source-image/tree joins using the preserved metadata workbook remain pending.

## Current artifacts

- `originals/*/*/source_metadata.json`: repository version, license metadata and source information.
- `originals/*/*/acquisition_receipt.json`: URLs, sizes, hashes and archive integrity.
- `manifests/acquired_images.jsonl`: one record per archive image with source annotations, grouping metadata, dimensions, SHA-256 and unassigned split.
- `manifests/acquisition_audit.json`: counts, duplicate groups, annotation issues and image metadata.
- `manifests/next_batch_images.jsonl`: PlantWild v2 and GYMNSA image records with source labels and unassigned training splits.
- `manifests/next_batch_audit.json`: second-batch readability, annotation, duplicate and cross-batch overlap checks.

Original archives remain intact. They are excluded from Git along with future farm photographs. The failed, incomplete first PlantDoc download was removed and replaced with the verified full archive.

## Next collection work

Mechanical preparation and conservative label definitions are complete; unresolved records are in `prepared/v1/review_queue.jsonl`. PlantWild v2 and GYMNSA are now downloaded; the earlier GYMNSA page timeout was resolved using its public file API. Collect properly labeled healthy/unknown examples and consider PlantVillage as a controlled-image baseline after checking any existing team copies. Add Tomato-Village or PlantSeg when the corresponding experiment is selected.

Model-specific research exports and held-out evaluations now exist. The general platform is not restricted to the old 15 classes, but supported crop/condition claims will depend on reviewed coverage, source license terms and field evaluation. The next training stage requires a new trainer that respects these recorded splits; the old 15-class trainer is not suitable unchanged.
