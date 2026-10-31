# Android offline leaf analysis

The Android app targets Android 7.0/API 24 or newer and bundles `app/assets/models/tomato_closeup.onnx` (5,779,466 bytes), exported from the selected three-class tomato checkpoint. It runs through the official ONNX Runtime Android dependency on the CPU. GPU/NNAPI acceleration is not enabled. iOS inference is not implemented.

## Build and install

From the full repository on a Windows development laptop with Flutter and the Android SDK available:

```powershell
.\scripts\Build-DemoMobile.ps1
```

This validates the model SHA, runs `flutter pub get`, `flutter analyze --no-fatal-infos`, `flutter test`, then `flutter build apk --release`. `-LocalDebug` selects a debug APK. Install the newly produced `app/build/app/outputs/flutter-apk/app-release.apk`; hot reload cannot install the Kotlin runtime. Release builds currently use the existing development signing key and are for the supervised demo, not store distribution.

Keep Firebase client files `app/lib/firebase_options.dart` and `app/android/app/google-services.json` configured for the intended project. They are not admin credentials. No service-account file belongs in the app. `MAPS_API_KEY` is optional for Google Maps and unrelated to offline analysis.

## What changed

- Login screen offers analysis without an account. Signed-in navigation has Home, Events, Leaf scan, Alerts and Settings; the event map is linked from Home.
- Camera/gallery photos are decoded with EXIF orientation, converted to RGB, resized/cropped to the training preprocessing, normalized to NCHW float32, then passed to a Kotlin worker thread. Inference does not perform network calls or save photos to Firebase.
- The native runtime verifies the ONNX SHA against its JSON metadata before creating a session. Model failures produce an error, with no placeholder predictions.
- Supported classes: tomato early blight, tomato late blight, healthy leaf class. Scores below 0.90 or unknown labels yield Inconclusive. No affected-area estimates, severity scores or treatment doses are invented.
- Home, alert and map placeholder data sources have been removed. Cloud views use actual Firestore events and device presence, with empty/error states. Missing timestamps and locations stay unavailable.
- Alerts update from complete snapshots, including deletions, and preserve local read state. Camera alerts require sign-in/internet and the app in the foreground; background push is not enabled.

## Model and preprocessing checks

`training/export_mobile_model.py` reproduces the export using the selected original checkpoint and installed PyTorch, Ultralytics, ONNX and ONNX Runtime. The original PT SHA and exported ONNX SHA are recorded in `app/assets/models/tomato_closeup.json`. All six recorded comparison photos retained the same top label, with maximum absolute probability difference 0.000000835. This checks export fidelity; it does not measure field accuracy.

The original model achieved four correct top labels on six tomato field samples; only two exceeded the 90% gate. There was no healthy-field or unsupported-object evaluation. Use close-up tomato leaves, and describe predictions as suggestions.

`training/create_mobile_preprocessing_fixtures.py` generates independent Pillow RGB references for square, portrait, landscape and EXIF-rotated inputs. Flutter tests compare the phone preprocessor to these fixtures and cover inconclusive presentation and alert snapshot replacement/read-state behavior.

## Required phone rehearsal

1. Install the freshly built APK. Save the six rehearsal photos to the phone before disconnecting.
2. Enable airplane mode, force-close/reopen, tap Try offline leaf analysis, select a photo and analyze. Repeat with the camera and at least one inconclusive sample. Check actual measured inference time; no speed claim has been established yet.
3. Deny photo/camera permission, cancel the picker and try a different photo. Verify useful errors and no stale prediction. The first inference loads the model; subsequent analyses reuse its session.
4. Restore connectivity, sign into the same Firebase project as the laptop, then rehearse actual confirmed fire event upload and phone receipt. Verify the evidence image and timestamp.
5. Close/stop the detector and check that the phone does not continue showing a live device beyond the heartbeat window.

## Verification status in this session

Export and Python ONNX inference passed. Flutter commands fail to start in this restricted environment (Dart reports a path canonicalization/access error), so the Dart analyzer, Flutter tests, Android compilation and physical phone UI/performance checks have **not** passed here. The supplied build script must complete, followed by the phone rehearsal, before handing the demo to the doctor.
