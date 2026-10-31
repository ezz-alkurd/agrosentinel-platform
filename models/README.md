# Model artifact policy

`legacy-inventory.json` records hashes of the pre-existing local files. Their presence does not make them the new close-up/far/fire production releases.

The three final model IDs and owners are in `contracts/model-catalog.json`. No active release is invented for an untrained model. Keep immutable trained weights in private object storage; commit manifests, checksums and evaluation records. Export Jetson-compatible artifacts separately and build TensorRT engines on the target device/software stack.
