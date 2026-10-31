# Laptop fire and tomato alerts

Open a PowerShell terminal in `D:\graduation-project\agrosentinel` and run:

```powershell
& "C:\Users\MCC\AppData\Local\Programs\Python\Python311\python.exe" ".\ai-backend\demo_launcher.py"
```

On the doctor laptop, use SETUP.cmd once, supply the private Firebase credential separately, then START_DEMO.cmd.

1. Choose Read-only connection check and Start first.
2. Choose Camera or recorded video, and Detection models: Fire + tomato leaves.
3. Use source 0 for the default camera or Browse to an actual recording. Start runs both selected models.
4. Fire uploads after two seconds at >=70%. A stable tomato disease label uploads after two seconds at >=90%. Healthy and uncertain tomato classifications do not create disease alerts. Repeats have a 30-second per-label cooldown.
5. For plants, fill the frame with one close-up tomato leaf. Supported classes are early blight, late blight and healthy. This classifier has no leaf detector or unsupported-object rejection; a high score on unrelated objects is not meaningful. Use Fire only for ordinary fire surveillance, and Tomato leaves only for a dedicated leaf station.
6. Sign into the Android app and keep Events/Alerts open. Check the uploaded evidence image and label. Leaf inference on the phone is separately bundled and does not use a laptop photo API.
7. Stop in the launcher or press q in the preview window.

Single recorded image supports either model or both. It bypasses the video confirmation timer and saves confirmation_mode=single_image.

The source PowerShell wrapper now enables both models by default:

```powershell
.\scripts\Start-LiveDemo.ps1 -Source 0
.\scripts\Start-LiveDemo.ps1 -Source 0 -FireOnly
.\scripts\Start-LiveDemo.ps1 -Source 0 -PlantOnly
```

The reviewed checkpoint identities remain pinned in models/demo-selection.json. The plant camera uses plant_disease_best.pt (three-class classifier), not the previously wired 38-class detector. Classifier evidence is the full frame, with no fabricated bounding box. Firebase events retain anomaly_type=disease, disease_name, confidence and the model SHA so the existing phone feed can display them.

Offline regression checks and real inference through a local receiver are recorded separately. These do not establish live Firebase upload or phone receipt; rehearse that on the actual laptop and phone before handoff.

## Upload rejected with Forbidden / 403

The launcher now identifies Storage evidence upload, Storage metadata update and Firestore event write separately. Run Read-only connection check again after reopening it. It now tests Storage IAM permissions even if there are no previous events. Authentication, Firestore read and Storage permission results are separate. A permission check does not prove that a real upload or phone receipt succeeded.

Check project agriculture-drone-e0dc0 in Firebase Console > Storage. Firebase Storage requires an active Blaze billing account; Spark/absent billing can return 402 or 403. If billing is active, use the detailed error to check the exact bucket and the laptop service account's Storage permissions (create, read, update). Do not make public rules to repair an Admin SDK IAM failure. No billing, IAM or cloud rules have been changed by these code edits.

References: https://firebase.google.com/docs/storage/faqs-storage-changes-announced-sept-2024 and https://docs.cloud.google.com/storage/docs/troubleshooting

## Fire replacement candidate

Current fire-only checkpoint is not established as reliable on live webcam footage. Its earlier four-image check is a small rehearsal, not a quality benchmark. A compatible candidate for comparison is rabahdev/fire-smoke-yolov8n on Hugging Face, trained on D-Fire with fire and smoke classes and background negatives in the dataset. Its reported metrics are from its own test split and cannot establish superiority on the presentation camera. Candidate weights have not been downloaded or activated in this session because external downloads are unavailable here. Compare positive and non-fire recordings from the intended camera before choosing a replacement. Keep Dina's forthcoming model evaluation as the longer-term release path.

Candidate: https://huggingface.co/rabahdev/fire-smoke-yolov8n
