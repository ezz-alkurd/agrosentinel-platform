# AgroSentinel Colab Starter Files

Files included:
- `firebase_config.py` → Firebase connection
- `detect_and_upload.py` → upload + Firestore logging backend
- `quick_train_disease_model_colab.py` → simple training starter
- `run_disease_classification_colab.py` → run one image through the trained model and log results
- `requirements_colab.txt` → packages

Suggested Colab flow:
1. Upload these files into Colab.
2. Upload `serviceAccountKey.json`.
3. Upload a small disease dataset folder or mount Google Drive.
4. Run `quick_train_disease_model_colab.py` to produce:
   - `plant_disease_model.h5`
   - `class_names.json`
5. Update `CLASS_NAMES` in `run_disease_classification_colab.py` to match your saved class order.
6. Upload a `test.jpg` leaf image.
7. Run `run_disease_classification_colab.py`.

If you already have a trained `.h5` model, skip training and go directly to the runner.
