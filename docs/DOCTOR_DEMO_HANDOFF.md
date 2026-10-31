# Handoff update: ASP.NET / SQL Server migration

The current path is the WPF Windows app and SQL-backed API. Follow [SMARTERASP_SETUP.md](SMARTERASP_SETUP.md). The older Firebase/Tkinter instructions below describe the previous transport and are retained for reference; the old doctor ZIP does not contain the new Windows/API distribution.

# Doctor laptop / phone handoff

Prepared 24 October 2026. Target: Windows 10/11, 64-bit, CPU inference. This is a reproducible rehearsal package, not proof that the doctor laptop, cloud account or phone have been tested.

## Selected models

| Use | Selected original artifact | Actual task/classes | Why |
| --- | --- | --- | --- |
| Laptop fire alert | Archived `historical-contributions/sara/models/best.pt` | Detection; fire only; about 22.5 MB | On the same four-image smoke check: wildfire fire=0.9875, no detections on field, leaf or street-sign negatives. The other three fire/smoke candidates stayed below the 0.70 fire gate on that image. This is not a representative accuracy test. Smoke support is absent. |
| Laptop / phone close-up leaf photo | Archived `old-models/plant_disease_yolov8_best.pt` | Classification; tomato early blight, tomato late blight, tomato healthy; about 3.0 MB | Small CPU model, explicit three-condition scope. Four of six sampled tomato field images had the correct top label. At the existing 0.90 gate, two late-blight results were returned; four results were inconclusive. No healthy-field set was tested. |

The 38-class disease detector is not enabled by default: it repeatedly misidentified classes on the inspected field samples. The 15-class classifiers also failed many field examples. A 46-class model identifies plant species rather than disease. COCO/ImageNet base weights are not agricultural disease releases. Checkpoint metadata scores were not compared as if they used the same evaluation set. None of these legacy models replaces the planned new close-up/far releases or Dina's pending release.

Exact hashes, all distinct checkpoint identities and raw checks are in `models/demo-selection.json`, `models/demo-checkpoint-audit.json` and the `demo-*-checks.json` reports. Source artifacts remain intact. The package renames selected files to stable logical filenames, with original names/source hashes retained in the manifest.

## Before giving the package to the doctor

1. Extract the handoff ZIP into a local folder. Run `SETUP.cmd` once with internet access and Python 3.11 64-bit installed. CPU PyTorch avoids needing an NVIDIA GPU/CUDA. Allow time for first-time downloads.
2. Supply the intended private Firebase credential separately into `.secrets/serviceAccountKey.json`, or choose its location in the launcher. It is deliberately not in the ZIP. Do not put it in the APK, a public website or a repository. Existing source-side private configuration stays ignored by Git.
3. Build and install a fresh Android APK: run `scripts/Build-DemoMobile.ps1` from the full source repository with Flutter/Android tools available. This checks the bundled model SHA, restores dependencies, runs analyzer/tests and builds an APK. No photo API URL is needed. The previously installed APK does not contain this new native runtime. See `docs/MOBILE_ON_DEVICE_HANDOFF.md` in the source repository.
4. The phone must sign into the same Firebase project. This package does not create users or change cloud rules. The foreground Events and Alerts feeds show the actual stored events. Background FCM notification delivery is not implemented by this package.
5. Complete the rehearsal below on the actual doctor laptop and phone before declaring them ready. The updated Android APK and physical-device inference still require verification.

## Start on the doctor's laptop

Double-click `START_DEMO.cmd`. Choose **Read-only connection check** first. The log must report Firestore access and, when a previous event exists, its evidence blob. Errors are visible; no synthetic event is inserted as a connectivity test.

Use **Camera or recorded video** with camera index `0` or another actual index; use Browse for a real recording. Select the **Fire + tomato leaves** detection profile (the default) to run both reviewed models. **Fire only** and **Tomato leaves only** are also available. Start writes device presence and confirms a stable eligible detection for two seconds: fire at 70% or above; the same non-healthy tomato label at 90% or above. The plant classifier analyzes the full frame, so one tomato leaf must fill it. It does not locate leaves or reject unrelated objects. Healthy and inconclusive predictions do not create disease events. A 30-second cooldown suppresses repeats. Stop signals a graceful camera shutdown and offline presence. A source shown as a recording must be described as recorded during presentation.

Use **Single recorded image** for an honest one-photo end-to-end check. It bypasses the two-second window and saves `confirmation_mode=single_image`; it does not demonstrate temporal video confirmation. The `examples/` folder contains actual project photographs and the six inspected tomato samples. It does not contain a staged fake Firebase event or a manufactured camera recording.

## Confirm the phone flow

- Keep the signed-in phone app open to Alerts or Events.
- Use an eligible source at the existing 70% fire gate. Do not lower the threshold only to manufacture a positive result.
- Check the detector log for a successful evidence upload and event write. Open the resulting event on the phone; compare its actual image, confidence, timestamp and source.
- Refresh/reopen Alerts and check that the same event appears once. A model bounding box on the laptop alone does not establish successful phone delivery.
- Stop the source and confirm the connected-device heartbeat expires/offline state appears. Location is unavailable unless explicitly configured; IP geolocation is opt-in and approximate.

## Phone photo feature

Install the new Android APK, open **Try offline leaf analysis** from the login screen, or **Leaf scan** after signing in. Choose a camera/gallery photo and tap **Analyze leaf**. The 5.8 MB ONNX model runs on the Android CPU; photos are not uploaded. No API, hosting subscription or login is needed for leaf inference. The selected model has three tomato classes and shows Inconclusive below 90%. A high score does not establish real-world correctness or reject every unsupported object.

For the offline rehearsal, save the sample photos to the phone first, enable airplane mode, force-close/reopen the app, then analyze them. Verify permission denial, unreadable image, retake and low-confidence behavior. Restore connectivity and sign in for the separate laptop-to-phone alert rehearsal. Background push is not implemented.


## Verified here / still pending

Verified: ONNX export probability parity on six photos (maximum absolute difference below 0.000001); all 14 distinct checkpoints loaded for audit; selected fire and tomato model inference; seven timing/path/upload regression checks; ten authenticated API contract checks; real tomato service positive and inconclusive cases; actual selected fire inference through two-second confirmation to a locally substituted upload handler; script syntax and package hashes. The local upload-handler check does not write to Firebase. The unit API checks use injected test identity and do not claim live Firebase authentication.

Pending: actual Firebase writes and phone receipt (authentication-network connection failed here), camera access on the doctor laptop, a newly built APK/Flutter analyzer (toolchain could not start here), Android native runtime/device performance and offline cold-start behavior, and a full connected-camera rehearsal. The older Python photo API is optional and is no longer used by the mobile app. The handoff must not be described as end-to-end verified until those checks pass.

## Combined laptop verification

The combined launcher and driver use the reviewed three-class tomato classifier rather than the unselected 38-class detector. `test_combined_demo.py` checks source/profile selection, class continuity, healthy/uncertain rejection, classification without boxes and the disease-event schema. Actual model inference on recorded fire, confident tomato and uncertain tomato examples is recorded in `models/demo-combined-pipeline-check.json`; the receiver is locally substituted and no Firebase event is written by that check. Live cloud receipt still needs the actual presenting phone.
