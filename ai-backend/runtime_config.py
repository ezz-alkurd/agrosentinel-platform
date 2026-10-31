"""Resolve approved existing model files without copying weights into Git."""
import os
import sys
import json
import hashlib
from pathlib import Path
REPOSITORY_ROOT = Path(sys.executable).resolve().parent.parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parent.parent

def resolve_model(name, override=None):
    if override:
        path = Path(override).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Configured model does not exist: {path}")
        return path
    configured = os.getenv("AGROSENTINEL_MODELS_DIR")
    if not configured:
        manifest = REPOSITORY_ROOT / "models" / "demo-selection.json"
        if manifest.is_file():
            artifact = json.loads(manifest.read_text(encoding="utf-8"))["artifacts"].get(name)
            if artifact:
                selected = (REPOSITORY_ROOT / artifact["path"]).resolve()
                if not selected.is_file():
                    raise FileNotFoundError(f"Selected release is missing: {name}")
                if hashlib.sha256(selected.read_bytes()).hexdigest() != artifact["sha256"]:
                    raise ValueError(f"Selected checkpoint checksum mismatch: {name}")
                return selected
    roots = [Path(configured)] if configured else [REPOSITORY_ROOT / "models", REPOSITORY_ROOT.parent / "models"]
    for directory in roots:
        path = directory / name
        if path.is_file():
            return path.resolve()
    raise FileNotFoundError(f"Model {name} not found. Set AGROSENTINEL_MODELS_DIR or pass an explicit model path.")
