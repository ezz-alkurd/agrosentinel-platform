"""
Colab-friendly disease classification runner.

What it does:
1. Loads a Keras .h5 disease classification model
2. Reads one input image
3. Predicts the disease class
4. If confidence is high enough, uploads the full image to Firebase Storage
5. Logs the event in Firestore

Before running:
- Put these files in the same Colab working folder:
  - run_disease_classification_colab.py
  - detect_and_upload.py
  - firebase_config.py
  - serviceAccountKey.json
  - plant_disease_model.h5
  - test.jpg
- Update CLASS_NAMES to match your own model's training order exactly.
"""

import cv2
import numpy as np
import tensorflow as tf
from detect_and_upload import handle_disease_classification

# Load trained model
MODEL_PATH = "plant_disease_model.h5"
model = tf.keras.models.load_model(MODEL_PATH)

# IMPORTANT:
# Replace this list with the exact class order used during training.
CLASS_NAMES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___healthy",
]

# Input image
IMAGE_PATH = "test.jpg"
frame = cv2.imread(IMAGE_PATH)

if frame is None:
    raise FileNotFoundError(
        "test.jpg was not found. Upload it to Colab or place it in the working folder."
    )

# Preprocess for a common 224x224 RGB classifier
img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
img = cv2.resize(img, (224, 224))
img = img.astype("float32") / 255.0
img = np.expand_dims(img, axis=0)

# Predict
predictions = model.predict(img, verbose=0)
pred_index = int(np.argmax(predictions[0]))
confidence = float(np.max(predictions[0]))
disease_name = CLASS_NAMES[pred_index]

# Temporary fixed GPS for testing
gps_lat = 32.0123
gps_lng = 36.1234

print(f"Predicted class: {disease_name}")
print(f"Confidence: {confidence:.4f}")

# Log only if confidence is high enough
if confidence > 0.80:
    handle_disease_classification(
        frame=frame,
        disease_name=disease_name,
        confidence=confidence,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
    )
else:
    print("Prediction confidence too low. Nothing uploaded.")
