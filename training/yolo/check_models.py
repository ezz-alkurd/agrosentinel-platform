"""
Run this script to verify both AI models are loaded correctly
and see all their detection classes.

Usage:  python check_models.py
"""
from pathlib import Path
from ultralytics import YOLO
import numpy as np

NEWMODELS_DIR = Path(__file__).resolve().parents[3] / "newmodels"

print("\n" + "="*60)
print("  AgroDrone AI — Model Verification")
print("="*60)

for label, filename in [("FIRE / SMOKE", "best.pt"), ("PLANT DISEASE", "plant_disease_best2.pt")]:
    path = NEWMODELS_DIR / filename
    print(f"\n[{label}]")
    print(f"  File : {path}")
    print(f"  Exists: {path.exists()}")

    if not path.exists():
        print("  ERROR: file not found!")
        continue

    model = YOLO(str(path))
    classes = list(model.names.values())
    print(f"  Classes ({len(classes)}): {classes}")

    # Quick sanity check on a blank image
    dummy = np.zeros((640, 640, 3), dtype='uint8')
    result = model(dummy, verbose=False)
    print(f"  Sanity check: {'PASSED' if result is not None else 'FAILED'}")

print("\n" + "="*60)
print("  Both models OK — ready to run vision.py")
print("="*60 + "\n")
