import os
import uuid
from datetime import datetime, UTC
import cv2

from firebase_config import initialize_firebase

# Connect once to Firebase
# Assumes you have a file named serviceAccountKey.json in the same working folder
# and a firebase_config.py that returns (db, bucket).
db, bucket = initialize_firebase()


def save_crop(image, bbox, output_dir="detections_local"):
    os.makedirs(output_dir, exist_ok=True)

    height, width = image.shape[:2]
    x1, y1, x2, y2 = map(int, bbox)

    # Keep bbox inside image boundaries
    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(0, min(x2, width))
    y2 = max(0, min(y2, height))

    if x2 <= x1 or y2 <= y1:
        raise ValueError("Invalid bounding box: crop area is empty.")

    crop = image[y1:y2, x1:x2]

    filename = f"{uuid.uuid4().hex}.jpg"
    local_path = os.path.join(output_dir, filename)

    success = cv2.imwrite(local_path, crop)
    if not success:
        raise IOError("Failed to save cropped image.")

    return local_path, filename


def save_full_image(image, output_dir="detections_local"):
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.jpg"
    local_path = os.path.join(output_dir, filename)

    success = cv2.imwrite(local_path, image)
    if not success:
        raise IOError("Failed to save image.")

    return local_path, filename


def upload_image(local_path, anomaly_type):
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    filename = os.path.basename(local_path)

    storage_path = f"detections/{anomaly_type}/{today}/{filename}"

    blob = bucket.blob(storage_path)
    blob.upload_from_filename(local_path)

    # With uniform bucket-level access, do not use blob.make_public()
    return storage_path


def log_event(anomaly_type, confidence, gps_lat, gps_lng, image_url, storage_path, extra=None):
    data = {
        "anomaly_type": anomaly_type,
        "confidence": float(confidence),
        "gps_lat": float(gps_lat),
        "gps_lng": float(gps_lng),
        "timestamp": datetime.now(UTC).isoformat(),
        "image_url": image_url,
        "storage_path": storage_path,
        "status": "new"
    }

    if extra:
        data.update(extra)

    db.collection("events").add(data)


def handle_detection(frame, bbox, anomaly_type, confidence, gps_lat, gps_lng, disease_name=None):
    """For bbox-based models such as fire detection."""
    try:
        local_path, filename = save_crop(frame, bbox)
        storage_path = upload_image(local_path, anomaly_type)

        extra = {"source_file": filename}
        if disease_name:
            extra["disease_name"] = disease_name

        log_event(
            anomaly_type=anomaly_type,
            confidence=confidence,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            image_url="",
            storage_path=storage_path,
            extra=extra,
        )

        print(f"✅ {anomaly_type} uploaded successfully!")

    except Exception as e:
        print("Error while handling detection:", e)


def handle_disease_classification(frame, disease_name, confidence, gps_lat, gps_lng):
    """For classification-only disease models that do not return a bounding box."""
    try:
        local_path, filename = save_full_image(frame)
        storage_path = upload_image(local_path, "disease")

        extra = {
            "source_file": filename,
            "disease_name": disease_name,
        }

        log_event(
            anomaly_type="disease",
            confidence=confidence,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            image_url="",
            storage_path=storage_path,
            extra=extra,
        )

        print(f"✅ disease uploaded successfully: {disease_name}")

    except Exception as e:
        print("Error while handling disease classification:", e)
