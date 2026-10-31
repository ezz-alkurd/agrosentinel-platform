# Plant data collection plan

Prepared 2026-10-03. First collection cycle: 3-16 October 2026. These dates are a proposed team work schedule, not appointments.

## Outcome of the first cycle

Create an auditable pilot collection for close-range plant analysis and a separate aerial experiment. Preserve broad public crop coverage in the inventory; use a manageable set of crops and conditions for each training experiment. The first pilot does not define the final supported crop list.

Expected deliverables: public archives with acquisition receipts; image/annotation inventory; reviewed label mappings; a small local photo pilot if farm access exists; a grouping plan for validation and final testing. Training follows these deliverables.

Team update on 2026-10-03: no farm access or capture equipment is available. Start a fresh data collection and fresh training runs rather than continuing old plant-disease checkpoints. General pretrained vision weights remain an appropriate initialization unless an experiment specifically requires random initialization. Local collection dates below are conditional on access becoming available.

## Two collection activities

### Public collections

Begin with PlantDoc object detection and potato Alternaria UAV. Keep original labels, filenames and dataset metadata. Next inspect PlantWild v2 and GYMNSA; add other collections as needed for the selected task. Acquisition status is recorded separately from suitability for training. Files downloaded successfully may still need label review or be unsuitable for the deployment sensor.

A public dataset's existing split is recorded, not automatically accepted as a new independent benchmark. Before exporting a training collection, check exact hashes and visually similar copies across sources. Group crops and augmentations with their source observation.

### Jordan farm photographs

Ask participating farms which crops, healthy plants and naturally symptomatic plants are currently accessible. Do not promise examples of every disease; availability is unknown until a visit. Ask a plant specialist to review representative symptoms and mark uncertain cases as uncertain. A visual assessment can support a symptom-based label; some pathogen identities require additional confirmation.

First visit target: 100-200 original photos from 30-50 distinct plants, where access permits. Include apparently healthy plants and symptomatic plants, several symptom severities and ordinary field backgrounds. These are workflow-pilot targets, not a claim of sufficient training data. Extra views of the same plant do not count as new independent plants.

For each selected plant, aim for 3-4 distinct views: a sharp leaf close-up, a wider view with the leaf in context, a whole-plant view, and an underside or alternate leaf view if useful. Keep plant IDs consistent. Capture original files rather than screenshots or compressed messaging-app copies. Collect in more than one session, with different lighting and actual intended devices.

Later choose a separate farm where possible, or reserve a complete plot/session before model development, for final testing. Expand the collection based on missing conditions and observed errors. A single farm/session cannot establish general performance across Jordan.

## Fixed-camera and drone pilot

Record device, resolution, viewpoint, distance, lighting and compression. Sample representative frames from recorded video; hundreds of consecutive frames from one scene remain one highly related group. Retain the source video and frame timestamps.

For a fixed camera, photograph the same selected plants at the intended installation distance. Check whether the leaf symptoms are actually visible before labelling frames for disease recognition.

For a drone, start with one short collection over a marked plot using available equipment and appropriate farm/site permission. Pair aerial observations with ground close-ups and expert observations from the same plot and date. Record flight ID, camera, altitude above ground, source image and plot footprint. Altitude alone does not determine usable resolution; review example images for sharpness and lesion detail. Avoid choosing a disease label solely from canopy colour or experimental treatment.

Photograph the target at multiple practical camera distances or heights and compare visible detail before planning a larger aerial collection. If individual symptoms cannot be seen, collect for suspicious-area mapping and request ground inspection. Do not convert such images into specific disease examples without evidence.

Drone GPS marks the camera position. Mapping an affected plant or image region requires additional camera geometry/georeferencing or ground plot coordinates. The current backend's IP geolocation is city-level and is not suitable for farm disease mapping.

## Metadata and labels

Use `data/plant/local-field/example_record.json` as a template. Every photo needs an image ID, source, farm/plot/plant/session group, crop, device, viewpoint, capture time and review status. Unknown values remain null. Store a suspected condition separately from a confirmed/reviewed condition. A healthy-looking leaf should be labelled apparently healthy unless the evidence supports more.

Store crop and condition as separate fields, then map to a model's class vocabulary. Distinguish disease, pest damage, nutrient problems, abiotic stress and background. Preserve multispectral band information; do not silently treat it as ordinary RGB.

Uncertain cases may support review or later robustness tests. They are not automatically one universal 'unknown' disease class. Gather representative non-leaf/background images to help evaluate rejection behaviour separately.

## Suggested five-member responsibilities

| Role | First-cycle work |
|---|---|
| Public collection custodian | Acquire public sources, versions, licenses and receipts |
| Label reviewer coordinator | Contact available plant expertise; maintain label mapping and review queue |
| Field collection lead | Arrange access; assign farm/plant IDs; coordinate original-photo transfer |
| Camera/drone collection lead | Capture deployment views and metadata; pair them with ground observations |
| Data quality and evaluation lead | Inventory, duplicate checks, annotation checks and reserved test groups |

These are responsibilities for the existing team; no messages or appointments have been sent on your behalf.

## First-cycle sequence

3-5 October: acquire and inventory the first public archives; establish metadata and label conventions; identify available farms/devices.

6-10 October: review samples and labels; perform one local collection pilot if access is available; document quality and equipment limitations.

11-16 October: resolve label conflicts, review annotations and duplicate groups, select the first training scope, and reserve evaluation groups. If farm access is not yet available, complete the public-data audit and mark deployment validation as pending.

## Readiness to train

- Images and annotations are readable and correctly paired.
- Source, version, license and hashes are recorded.
- Crop/condition labels are mapped and uncertain labels are excluded from supervised targets.
- Sensor and viewpoint fit the intended model.
- Related observations stay in one split; held-out data is not used for training or threshold tuning.
- Per-class and per-group counts are reported, including what is missing.

The current `training/train_disease.py` expects `training/plantvillage_raw`, which was absent in the active training folder during this scan. Its random 85/15 train/validation split has no independent test set. Update the preparation/splitting process before using that script for the new mixed-source collection. Its previous class list is a starting experiment, not a limit on the general platform.

## Sources

- PlantDoc: https://github.com/pratikkayal/PlantDoc-Object-Detection-Dataset
- Potato UAV: https://zenodo.org/records/10727413 and https://zenodo.org/api/records/10727413
- Potato imaging study: https://doi.org/10.3389/fpls.2024.1206998
- PlantWild versions: https://tqwei05.github.io/PlantWild/
- GYMNSA: https://data.mendeley.com/datasets/44kjgc4gkc/1
- PlantSeg: https://github.com/tqwei05/PlantSeg
- Tomato-Village: https://github.com/mamta-joshi-gehlot/Tomato-Village
- PlantVillage: https://github.com/spMohanty/PlantVillage-Dataset
