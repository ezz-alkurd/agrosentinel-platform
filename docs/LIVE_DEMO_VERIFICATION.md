# Laptop detection to phone verification — 24 October 2026

## Run on the laptop

From the agrosentinel folder in PowerShell:

```powershell
.\scripts\Start-LiveDemo.ps1 -VerifyOnly
.\scripts\Start-LiveDemo.ps1 -FireOnly
```

The launcher uses the existing private credential under `.secrets/` (ignored by Git), or `FIREBASE_KEY_PATH` / `-FirebaseKeyPath`. Override the interpreter with `-Python` when needed. It does not install packages or publish security rules.

Use `-Source 1` for a second USB camera; `-Source 'C:\path\recording.mp4'` for an identified recording; `-Image 'C:\path\photo.jpg' -FireOnly` for a single-image run. Single images bypass temporal confirmation and record `confirmation_mode=single_image`; they do not prove continuous video confirmation. Do not stage a real fire.

## Verification completed here

- Existing Python 3.11 runtime has OpenCV, Ultralytics, NumPy and Firebase Admin installed.
- Existing fire checkpoint loads as a fire/smoke detector. The two model files are found outside the source repository. These are legacy weights, not the new plant/fire model releases.
- Inference ran on the public-site wildfire image; its smoke result was below the 70% gate and no event was uploaded. Two other existing images produced no eligible detection. Do not lower thresholds just to force a demonstration.
- Restored the existing ignored Firebase client configuration for Flutter from the preserved source.
- Fixed the fetch/subscription alert gap by processing the initial stream snapshot and deduplicating event IDs in the cubit.
- Seven offline regression checks passed for continuous confirmation, dropped-frame reset, independent fire/smoke gates, cooldown, model paths, upload failures and source metadata.

## Not yet verified

Firebase authentication could not connect from the restricted execution environment (`TransportError`). A successful cloud write, evidence download and physical-phone display have not been demonstrated. Flutter tooling could not start successfully here, so the mobile edits still require analyzer/tests on the laptop. No APK was built in this step.

## Actual phone rehearsal

1. Run the read-only verification command. Resolve any connection/credential/service error before inference.
2. Sign in to the actual Firebase-backed app and keep Alerts visible in the foreground.
3. Run the camera/recording detector and show supported material continuously for at least two seconds above the existing confidence gate.
4. Check a real Firestore event and its evidence image. Verify capture time, source type and confidence, then check the same event in Detections and Alerts on the phone.
5. Refresh/reopen Alerts: the same event should appear once. Disconnect the source: its heartbeat should become stale/offline.

Foreground Firestore alerts are separate from background FCM push. Background push is not implemented or verified by these changes. No synthetic events were created during the checks. No cloud rules were changed.


## Current doctor handoff

The selected demo now uses the fire-only detector from the archived Sara folder and the three-class tomato close-up classifier. See `DOCTOR_DEMO_HANDOFF.md` and `models/demo-selection.json`; earlier references in this record to the two-class fire checkpoint describe the previous check, not the current selected release.

## Combined fire / tomato laptop update

The launcher now defaults to both reviewed models and offers separate Fire only / Tomato leaves only profiles. The PowerShell wrapper also defaults to both; use -FireOnly for fire surveillance. See LAPTOP_FIRE_AND_PLANT.md. The selected plant classifier operates on one close-up tomato leaf and produces full-frame evidence. It has no unsupported-object rejection. Combined model smoke checks use a local substituted receiver; actual cloud delivery remains a separate rehearsal.
