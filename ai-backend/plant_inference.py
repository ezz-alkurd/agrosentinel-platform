"""Shared close-up plant runtime for local rehearsal and hosted photo inference."""
import hashlib
import json
import os
import threading
from pathlib import Path
import cv2
import numpy as np
from runtime_config import resolve_model

class PlantEngine:
    def __init__(self, path=None):
        os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(__file__).resolve().parent.parent / "runtime" / "ultralytics"))
        from ultralytics import YOLO
        self.path = resolve_model("plant_disease_best.pt", path or os.getenv("PLANT_MODEL_PATH"))
        self.sha256 = hashlib.sha256(self.path.read_bytes()).hexdigest()
        manifest=Path(__file__).resolve().parent.parent / "models" / "demo-selection.json"
        if manifest.is_file():
            expected=json.loads(manifest.read_text(encoding="utf-8"))["artifacts"]["plant_disease_best.pt"]["sha256"]
            if self.sha256 != expected: raise ValueError("Plant release checksum mismatch")
        self.model = YOLO(str(self.path))
        if self.model.task != "classify" or set(self.model.names.values()) != {"Tomato_Early_blight", "Tomato_Late_blight", "Tomato_healthy"}:
            raise ValueError("This release requires the reviewed three-class tomato classifier.")
        self.lock = threading.Lock()
        self.threshold = float(os.getenv("PLANT_MIN_CONFIDENCE", "0.90"))
        if not 0 <= self.threshold <= 1: raise ValueError("Invalid confidence threshold")

    def metadata(self):
        return {"id":"plant-closeup-demo-tomato-3", "task":"classify", "classes":3,
                "sha256":self.sha256, "experimental":True,
                "supported_crops":["tomato"]}

    def analyze(self, data):
        # Header inspection limits decompressed dimensions before OpenCV allocation.
        from PIL import Image
        import io
        try:
            with Image.open(io.BytesIO(data)) as header:
                if header.width * header.height > 20_000_000:
                    raise ValueError("Image exceeds 20 megapixels")
                if header.format not in ("JPEG", "PNG", "WEBP"):
                    raise ValueError("Use JPEG, PNG or WebP")
        except (Image.UnidentifiedImageError, OSError) as exc:
            raise ValueError("Cannot decode image") from exc
        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise ValueError("Image dimensions are too large") from exc
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None: raise ValueError("Cannot decode image")
        if not self.lock.acquire(blocking=False): raise RuntimeError("Model busy; retry shortly")
        try:
            result = self.model(image, device=os.getenv("INFERENCE_DEVICE", "cpu"), verbose=False)[0]
            index = int(result.probs.top1)
            confidence = float(result.probs.top1conf)
            label = {"Tomato_Early_blight":"Tomato___Early_blight", "Tomato_Late_blight":"Tomato___Late_blight", "Tomato_healthy":"Tomato___healthy"}[result.names[index]]
            return {"status":"prediction" if confidence >= self.threshold else "inconclusive",
                    "label":label if confidence >= self.threshold else None,
                    "confidence":confidence, "model":self.metadata(),
                    "message":"Close-up tomato leaves only. This legacy model is not validated for general field imagery."}
        finally:
            self.lock.release()
