import cv2
from ultralytics import YOLO
import time
import os
import json
import random
import numpy as np
from pathlib import Path
try:
    import geocoder          # pip install geocoder
    _GEOCODER_AVAILABLE = True
except ImportError:
    _GEOCODER_AVAILABLE = False
# =============================================================================
# PROJECT CONFIGURATION
# =============================================================================

USE_REAL_GPS  = True
SAVE_COOLDOWN = 5       # minimum seconds between saving reports

# Output folders
BASE_DIR    = 'graduation_project_data'
CROPS_DIR   = os.path.join(BASE_DIR, 'crops')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

for folder in [CROPS_DIR, REPORTS_DIR]:
    os.makedirs(folder, exist_ok=True)


# =============================================================================
# MODEL PATHS — loaded directly from the newmodels/ folder
# =============================================================================

NEWMODELS_DIR      = Path(__file__).resolve().parents[3] / "newmodels"
MODEL_DISEASE_PATH = str(NEWMODELS_DIR / "plant_disease_best2.pt")
MODEL_FIRE_PATH    = str(NEWMODELS_DIR / "best.pt")

# --- Verify both files exist before doing anything else ---
if not os.path.exists(MODEL_DISEASE_PATH):
    print(f"[ERROR] Disease model not found at: {MODEL_DISEASE_PATH}")
    exit()

if not os.path.exists(MODEL_FIRE_PATH):
    print(f"[ERROR] Fire model not found at: {MODEL_FIRE_PATH}")
    exit()

print("[OK] Both model files found.")


# =============================================================================
# LOAD MODELS
# =============================================================================

print("[INFO] Loading plant disease model...")
model_disease = YOLO(MODEL_DISEASE_PATH)

print("[INFO] Loading fire detection model...")
model_fire = YOLO(MODEL_FIRE_PATH)

print("[INFO] Both models loaded successfully.")
print(f"       Disease classes : {list(model_disease.names.values())}")
print(f"       Fire classes    : {list(model_fire.names.values())}")


# =============================================================================
# QUICK SANITY CHECK
# Runs each model on a blank dummy image to confirm they return results
# without crashing. If this fails the .pt file is likely corrupted.
# =============================================================================

print("[INFO] Running sanity check on both models...")

dummy = np.zeros((640, 640, 3), dtype='uint8')

for name, model in [("Disease", model_disease), ("Fire", model_fire)]:
    try:
        test = model(dummy, verbose=False)
        if test is None or len(test) == 0:
            print(f"[WARNING] {name} model returned None on dummy image. File may be corrupted.")
        else:
            print(f"[OK] {name} model sanity check passed.")
    except Exception as e:
        print(f"[ERROR] {name} model crashed during sanity check: {e}")
        exit()


# =============================================================================
# MODEL REGISTRY
# Add a third model here in the future without changing anything else.
#
#   color is in BGR format (OpenCV convention):
#     (0, 255,   0) = green  → disease
#     (0,   0, 255) = red    → fire / smoke
# =============================================================================

MODELS = [
    {
        "model"    : model_disease,
        "category" : "Disease",
        "color"    : (0, 255, 0),
        "conf"     : 0.45,   # disease model needs lower threshold to detect
        # Exclude healthy classes — we only want to flag actual diseases
        "exclude"  : {"Pepper__bell___healthy", "Potato___healthy", "Tomato_healthy"},
    },
    {
        "model"    : model_fire,
        "category" : "Fire",
        "color"    : (0, 0, 255),
        "conf"     : 0.75,   # higher threshold to suppress false fire detections
        # Exclude the generic background class that fires on everything
        "exclude"  : {"default"},
    },
]


# =============================================================================
# FIREBASE CALLBACK HOOK  (for Member 4)
#
# Member 4 does NOT edit this file. They import it and call
# register_detection_handler() once, passing their upload function.
#
# Example in Member 4's firebase_integration.py:
#
#   from vision import register_detection_handler
#
#   def upload_to_firebase(report, crop_path):
#       # their Firebase code here
#       pass
#
#   register_detection_handler(upload_to_firebase)
# =============================================================================

on_detection_callback = None

def register_detection_handler(fn):
    """Register an external function to be called on every new detection."""
    global on_detection_callback
    on_detection_callback = fn


# =============================================================================
# GPS HELPER
# =============================================================================

def get_gps():
    if USE_REAL_GPS and _GEOCODER_AVAILABLE:
        try:
            g = geocoder.ip('me')
            if g.latlng:
                return g.latlng[0], g.latlng[1]
        except Exception:
            pass
    elif USE_REAL_GPS and not _GEOCODER_AVAILABLE:
        print("[WARNING] geocoder not installed — using simulated GPS. Run: pip install geocoder")
    # Fallback simulation — coordinates near university area
    return (
        32.1030 + random.uniform(-0.005, 0.005),
        36.1850 + random.uniform(-0.005, 0.005),
    )


# =============================================================================
# VIDEO SOURCE
#
# Webcam  → cv2.VideoCapture(0)
# Video file → cv2.VideoCapture('videos/drone_footage.mp4')
# =============================================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("[ERROR] Could not open video source. Check your camera or file path.")
    exit()

print("[INFO] Pipeline running. Press Q to quit.")

prev_time = 0
last_save  = 0


# =============================================================================
# MAIN INFERENCE LOOP
# =============================================================================

while cap.isOpened():
    success, frame = cap.read()

    # End of video file or camera disconnected
    if not success:
        print("[INFO] No more frames. Exiting.")
        break

    # Flip horizontally for webcam — remove this line for drone footage
    frame = cv2.flip(frame, 1)

    current_detections = []

    # -------------------------------------------------------------------------
    # RUN BOTH MODELS ON THE CURRENT FRAME
    # -------------------------------------------------------------------------

    for entry in MODELS:
        try:
            raw = entry["model"](
                frame,
                conf    = entry["conf"],
                imgsz   = 640,
                verbose = False,
            )
        except Exception as e:
            print(f"[WARNING] {entry['category']} model inference error: {e}")
            continue

        # Guard: model returned nothing
        if raw is None or len(raw) == 0:
            continue

        results = raw[0]

        # Guard: results object is empty or has no boxes
        if results is None or results.boxes is None:
            continue

        excluded = entry.get("exclude", set())

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf     = float(box.conf[0])
            cls_name = results.names[int(box.cls[0])]

            # Skip classes that are noise (e.g. "other" in fire model)
            if cls_name.lower() in {e.lower() for e in excluded}:
                continue

            color    = entry["color"]
            category = entry["category"]

            # Clean up class name for display (replace underscores, shorten)
            display_name = cls_name.replace("___", " - ").replace("__", " ").replace("_", " ")

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Draw label above bounding box
            label = f"[{category}] {display_name}  {conf:.2f}"
            cv2.putText(
                frame, label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
            )

            current_detections.append({
                "category"  : category,
                "class"     : cls_name,
                "confidence": round(conf, 2),
                "bbox"      : [x1, y1, x2, y2],
            })

    # -------------------------------------------------------------------------
    # SAVE REPORT + CROP  (only when detections exist and cooldown has passed)
    # -------------------------------------------------------------------------

    curr_time = time.time()

    if current_detections and (curr_time - last_save > SAVE_COOLDOWN):

        ts       = int(curr_time)
        lat, lon = get_gps()

        # Crop the first detected anomaly region
        first        = current_detections[0]
        x1, y1, x2, y2 = first["bbox"]

        # Clamp coordinates so crop never goes outside frame boundaries
        h_frame, w_frame = frame.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w_frame, x2)
        y2 = min(h_frame, y2)

        crop      = frame[y1:y2, x1:x2]
        crop_name = f"crop_{ts}.jpg"
        crop_path = os.path.join(CROPS_DIR, crop_name)

        # Only save crop if it has actual content
        if crop.size > 0:
            cv2.imwrite(crop_path, crop)
        else:
            crop_path = None
            print("[WARNING] Crop was empty, skipping image save.")

        # Build report dictionary
        report = {
            "project"   : "Autonomous Drone Agriculture Monitoring",
            "timestamp" : time.ctime(curr_time),
            "location"  : {
                "latitude" : lat,
                "longitude": lon,
                "mode"     : "real" if USE_REAL_GPS else "simulated",
            },
            "detections": current_detections,
            "crop_image": crop_path,
        }

        # Write JSON report to disk
        report_path = os.path.join(REPORTS_DIR, f"report_{ts}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=4)

        print(f"[DETECTION] {len(current_detections)} anomaly saved → {report_path}")

        # Trigger Firebase callback if Member 4 has registered it
        if on_detection_callback:
            try:
                on_detection_callback(report, crop_path)
            except Exception as e:
                print(f"[WARNING] Firebase callback error: {e}")

        last_save = curr_time

    # -------------------------------------------------------------------------
    # HUD OVERLAY
    # -------------------------------------------------------------------------

    fps = 1.0 / (curr_time - prev_time + 1e-9)
    prev_time = curr_time

    # FPS counter
    cv2.putText(frame, f"FPS: {int(fps)}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (255, 255, 255), 2)

    # Detection count
    cv2.putText(frame, f"Detections: {len(current_detections)}",
                (20, 70), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (200, 200, 200), 2)

    # Status indicator — green when clear, red when anomaly found
    status_color = (0, 0, 255) if current_detections else (0, 255, 0)
    status_text  = "! ANOMALY DETECTED !" if current_detections else "All Clear"
    cv2.putText(frame, status_text,
                (20, 100), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, status_color, 2)

    cv2.imshow("Drone Vision System - Graduation Project", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# =============================================================================
# CLEANUP
# =============================================================================

cap.release()
cv2.destroyAllWindows()
print("[INFO] Pipeline shut down cleanly.")