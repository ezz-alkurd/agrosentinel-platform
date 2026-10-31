# AgroSentinel

Camera-based agricultural analysis with separate close-up plant, distant/aerial plant, and fire/smoke models.

**Team:** Ezzeldeen Alkurd, Sara Hamdan, Khalid Masoud, Raneen Abdullah, Dina Afram. Dina owns fire/smoke model work. Other technical allocations are proposed in the architecture record.

Read [the final architecture](docs/FINAL_PRODUCT_ARCHITECTURE.md) and [the delivery backlog](docs/DELIVERY_BACKLOG.md). The final platform uses Flutter, an ASP.NET Core application API and SQL Server on SmarterASP.NET, a separate Python GPU runtime on Runpod, and a camera/Jetson agent. Soil analysis is reserved for a later model extension.

## Source status

This repository contains the Flutter app, Python detection and plant services, an ASP.NET control API, desktop and presentation apps, deployment scripts, data-preparation tools, contracts, and architecture records. These components are under active development; the presence of source code does not imply a production deployment or completed model validation. The backlog tracks the remaining work.

| Directory | Purpose |
|---|---|
| `app/` | Existing Flutter source to connect to the final public API |
| `ai-backend/` | Existing Python detector/Firebase/local-API implementation; reference during refactoring |
| `services/control-api/` | ASP.NET/SQL implementation boundary and requirements |
| `services/inference/` | Cloud inference/worker implementation boundary and requirements |
| `agents/camera/` | Camera/Jetson implementation boundary and requirements |
| `contracts/` | Versioned model catalog and analysis input contract |
| `models/` | Inventory and artifact policy; weights stay outside Git |
| `training/` | Current preparation tools and older trainers; observe training boundary below |
| `data/` | Source registry/manifests and metadata examples, not raw images |
| `deployment/` | Hosting and environment requirements |
| `scripts/` | Source verification, packaging and publishing utilities |
| `docs/` | Current decisions and data audit reports |

## Local configuration and data

The pre-existing datasets, prepared exports and old model weights remain in `D:\graduation-project\data` and `D:\graduation-project\models`. Private server credentials remain outside this source repository. No raw-image dataset, large model weight, application build, Python virtual environment or old Git history is included in the initial commit. The selected 5.5 MB ONNX model for offline Android analysis is the sole model-file exception.

Generate the app's Firebase client configuration using FlutterFire for your actual Firebase project, or restore the existing ignored `app/lib/firebase_options.dart` and `app/android/app/google-services.json` locally. These generated files are intentionally excluded from Git. Set `MAPS_API_KEY` as an environment variable or private Gradle property. Run `flutter pub get` in `app/` after configuration. A production release requires proper signing; the inherited Android project currently uses debug signing and must be changed before release.

For the inherited Python pipeline, create a virtual environment, install `ai-backend/requirements.txt`, set `FIREBASE_KEY_PATH` to your external service-account file, and restore required approved local weights. New plant training must consume the frozen exports described in `docs/PLANT_DATA_PREPARATION.md`; do not run the old 15-class trainer unchanged or reuse old plant checkpoints as the new releases.

Relocating prepared datasets requires recording path-only updates to detector YAML files and rechecking the frozen experiment. The copied data-audit reports record source checksums; they are not a replacement for the actual image/annotation exports.

## Collaboration

Use one branch per task and pull requests into `main`. Keep model artifacts and datasets in controlled external storage with manifests/checksums. Never add service accounts, camera passwords, signing keys or provider tokens to commits. See `docs/REPOSITORY_HANDOFF.md` for publishing and teammate access.

## Verification

```powershell
python scripts/verify_source.py
python training/data_collection/test_preparation.py
```

The second command requires the preparation dependencies. These checks do not establish app, model or production integration readiness.


## Doctor laptop / phone rehearsal

The selected legacy fire-only and tomato close-up models, portable Windows launcher and explicit verification limits are documented in [the doctor handoff](docs/DOCTOR_DEMO_HANDOFF.md). Build secret-free handoffs with `python scripts/package_doctor_demo.py`. The authenticated plant photo compatibility API is under `ai-backend/plant_api.py`, with its container recipe in `deployment/plant-photo-api/`. Neither this compatibility route nor the existing Firestore camera feed claims completion of the final ASP.NET/SQL platform. Cloud phone delivery, a new APK, doctor laptop validation and live deployment remain to be completed.

### Android offline leaf analysis (24 October 2026)

The phone now bundles the selected three-class tomato ONNX model. Leaf photos are analyzed on the Android CPU without an API or account. Firebase remains the separate camera-alert transport. Build and device-verification instructions: [Mobile handoff](docs/MOBILE_ON_DEVICE_HANDOFF.md). Android compilation/device validation is still pending; use a fresh APK, not the old installed build.

### ASP.NET / SQL / Windows update

The API module and WPF camera console are implemented; Flutter event/device feeds now use the API. Hosting setup, Windows distribution build and verification status: [SMARTERASP_SETUP.md](docs/SMARTERASP_SETUP.md). Existing Firebase sign-in remains; event/photo storage moves to SQL Server and private application evidence.
