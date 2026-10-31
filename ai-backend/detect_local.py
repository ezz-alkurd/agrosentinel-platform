"""
detect_local.py — STANDALONE laptop detector (no Firebase, no mobile app).

Runs BOTH models on the laptop camera and shows the results live on screen:
  - fire model    -> ../models/fire_best.pt          (detection: fire, smoke boxes)
  - disease model -> ../models/plant_disease_detect.pt (detection: 38 classes)

This is the "models alone" version. It does NOT upload anything and does NOT
need the phone. (The app-connected version is run_detection.py.)

USAGE:
    pip install ultralytics opencv-python
    python detect_local.py                 # default webcam (source 0)
    python detect_local.py --source 1       # another camera
    python detect_local.py --source clip.mp4
    python detect_local.py --image leaf.jpg # one image, print result, show it
    python detect_local.py --no-disease     # fire only

Press 'q' in the window to quit.
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from types import ModuleType

import cv2

# ── legacy-checkpoint import shim (models trained on old ultralytics) ──
def _patch_ultralytics_yolo() -> None:
    mappings = {
        "ultralytics.yolo": "ultralytics",
        "ultralytics.yolo.utils": "ultralytics.utils",
        "ultralytics.yolo.utils.ops": "ultralytics.utils.ops",
        "ultralytics.yolo.engine": "ultralytics.engine",
        "ultralytics.yolo.engine.results": "ultralytics.engine.results",
        "ultralytics.yolo.v8": "ultralytics.models.yolo",
    }
    for old, new in mappings.items():
        if old not in sys.modules:
            try:
                sys.modules[old] = __import__(new, fromlist=[""])
            except ImportError:
                sys.modules[old] = ModuleType(old)

_patch_ultralytics_yolo()
from ultralytics import YOLO

SCRIPT_DIR = Path(__file__).resolve().parent
MODELS_DIR = SCRIPT_DIR.parent / "models"
FIRE_MODEL = MODELS_DIR / "fire_best.pt"
DISEASE_MODEL = MODELS_DIR / "plant_disease_detect.pt"  # 38-class detector

CONF = 0.25                     # detection display threshold
FIRE_EXCLUDE = {"other"}
DISEASE_DISPLAY_CONF = 0.35


def annotate_disease(frame, disease_model):
    """Detect plant disease and draw boxes (skips healthy classes)."""
    res = disease_model(frame, conf=CONF, verbose=False)[0]
    if res.boxes is None:
        return
    for box in res.boxes:
        label = res.names[int(box.cls[0])]
        conf = float(box.conf[0])
        if "healthy" in label.lower() or conf < DISEASE_DISPLAY_CONF:
            continue
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        short = label.split("___")[-1].replace("_", " ")
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
        cv2.putText(frame, f"{short} {conf:.0%}", (x1, max(18, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)


def annotate_fire(frame, fire_model):
    """Run fire detection and return a frame with boxes drawn."""
    res = fire_model(frame, conf=CONF, verbose=False)[0]
    if res.boxes is None or len(res.boxes) == 0:
        return frame
    # filter excluded classes, then let ultralytics draw the rest
    keep = [i for i, b in enumerate(res.boxes)
            if not any(x in res.names[int(b.cls[0])].lower() for x in FIRE_EXCLUDE)]
    if not keep:
        return frame
    return res[keep].plot()


def main():
    ap = argparse.ArgumentParser(description="Standalone laptop detector (no Firebase)")
    ap.add_argument("--source", default="0", help="camera index or video path")
    ap.add_argument("--image", help="run on a single image and show it")
    ap.add_argument("--no-disease", action="store_true", help="fire only")
    args = ap.parse_args()

    for m in (FIRE_MODEL, DISEASE_MODEL):
        if not m.exists():
            raise SystemExit(f"Model not found: {m}")

    print("Loading models...")
    fire_model = YOLO(str(FIRE_MODEL))
    disease_model = None if args.no_disease else YOLO(str(DISEASE_MODEL))
    print(f"fire classes: {fire_model.names}")

    # single image mode
    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            raise SystemExit(f"Cannot read image: {args.image}")
        out = annotate_fire(frame, fire_model)
        if disease_model is not None:
            annotate_disease(out, disease_model)
            r = disease_model(frame, conf=CONF, verbose=False)[0]
            if r.boxes is not None:
                for b in r.boxes:
                    name = r.names[int(b.cls[0])]
                    if "healthy" in name.lower():
                        continue
                    print(f"[disease] {name} {float(b.conf[0]):.2%}")
        cv2.imshow("AgroSentinel (local) — press any key", out)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    # live camera / video mode
    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open source: {source}")

    print("Running. Press 'q' to quit.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        out = annotate_fire(frame, fire_model)
        if disease_model is not None:
            annotate_disease(out, disease_model)
        cv2.imshow("AgroSentinel (local) — fire + disease", out)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
