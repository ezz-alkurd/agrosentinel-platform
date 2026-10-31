from __future__ import annotations   # allow `dict | None` etc. on Python 3.9

import torch
import os
import re
import json
import shutil
import random
import tempfile
from pathlib import Path
from ultralytics import YOLO
from datetime import datetime

# Resolve paths relative to this script, not the current working directory,
# so train and inference agree on where training_runs/ lives regardless of cwd.
SCRIPT_DIR       = Path(__file__).resolve().parent

# ── Dataset ─────────────────────────────────────────────────────
# RAW_DATASET_DIR: the messy Kaggle download (PlantVillage) — one folder per
# class, ALL crops mixed together (apple, corn, grape, tomato, potato, pepper...).
# This script filters it down to only the 15 tomato/potato/pepper classes and
# builds a clean train/val split in FILTERED_DATASET_DIR.
RAW_DATASET_DIR      = SCRIPT_DIR / "plantvillage_raw"
FILTERED_DATASET_DIR = SCRIPT_DIR / "plant_disease_dataset"
FORCE_REBUILD_DATASET = False   # set True to wipe FILTERED_DATASET_DIR and rebuild from raw

TRAIN_SPLIT = 0.85   # rest goes to val — no separate test split, same as train_fire.py

# ── Target classes — Tomato / Potato / Bell Pepper only (15 total) ─────────
# Matched against whatever is actually on disk via normalize() below, so it
# doesn't matter if your download names them "Tomato___Late_blight" or
# "Tomato_Late_blight" or "Pepper,_bell___healthy" vs "Pepper__bell___healthy".
SELECTED_CLASSES = [
    # ── BELL PEPPER (2) ──
    "Pepper__bell___Bacterial_spot",
    "Pepper__bell___healthy",
    # ── POTATO (3) ──
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    # ── TOMATO (10) ──
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites_Two_spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]
MIN_IMAGES_WARNING = 200   # flag any class below this as a risk (e.g. Potato healthy)

# ── Model — set PRETRAINED_MODEL to a downloaded disease-classifier .pt to skip scratch training
PRETRAINED_MODEL = None                  # e.g. "/path/to/plant_disease_best.pt"
MODEL            = PRETRAINED_MODEL if PRETRAINED_MODEL else "yolov8m-cls.pt"
# "m" (medium) gives noticeably better accuracy than "n"/"s" on this task for a
# small VRAM/time cost since classification is far lighter than detection.
# Drop to "yolov8s-cls.pt" if you only have a 4GB laptop GPU.

# FREEZE_EPOCHS must be > WARMUP_EPOCHS (3) or Phase 1 is 100% warmup with no stable training
FREEZE_EPOCHS   = 8 if PRETRAINED_MODEL else 10
# yolov8*-cls models have exactly 10 top-level modules (indices 0-9), where index 9
# is the Classify head — freezing all 10 (as train_fire.py does for its much deeper
# detection model) leaves zero trainable params and crashes. 9 locks the whole
# backbone (0-8) and leaves only the Classify head trainable for Phase 1.
FREEZE_LAYERS   = 9
FINETUNE_EPOCHS = 40 if PRETRAINED_MODEL else 60
# Classification on PlantVillage-style data converges MUCH faster than fire/smoke
# detection — this dataset is known to hit 95%+ within 10-20 epochs since images
# are plain-background studio shots. Patience below will usually stop it early.

IMG_SIZE        = 224                   # native yolov8-cls resolution — best transfer learning fidelity
SEED            = 42                    # fixed seed for reproducible experiments

LR_PHASE1       = 0.001
LR_PHASE2       = 0.005
LRF             = 0.01                  # Final LR = lr0 * lrf (cosine decay)
MOMENTUM        = 0.937
WEIGHT_DECAY    = 0.0005
WARMUP_EPOCHS   = 3
WARMUP_MOMENTUM = 0.8
WARMUP_BIAS_LR  = 0.1
PATIENCE        = 20                    # cls converges fast — shorter patience than detection

# ── Augmentation ────────────────────────────────────────────────
# Kept moderate — disease diagnosis depends on subtle lesion color/texture,
# so we avoid aggressive hue/blend augmentation that could wash that out.
FLIPLR          = 0.5
FLIPUD          = 0.15                  # leaves are photographed at any orientation
DEGREES         = 20.0
TRANSLATE       = 0.1
SCALE           = 0.6
SHEAR           = 0.0
PERSPECTIVE     = 0.0005
HSV_H           = 0.02
HSV_S           = 0.6
HSV_V           = 0.4
MIXUP           = 0.15
CUTMIX          = 0.0
ERASING         = 0.4                   # random erasing — standard cls regularizer
AUTO_AUGMENT    = "randaugment"
DROPOUT         = 0.3                   # PlantVillage is known to overfit fast (plain backgrounds)
LABEL_SMOOTHING = 0.1

# ── Save & Output ───────────────────────────────────────────────
PROJECT         = str(SCRIPT_DIR / "training_runs")
SAVE_PERIOD     = 10

# ── Resume control ──────────────────────────────────────────────
FORCE_RESTART   = False  # set True only to wipe checkpoints and retrain from scratch
STATE_FILE      = os.path.join(PROJECT, "training_state.json")

# Guard: Phase 1 needs stable (non-warmup) epochs or the frozen-head phase is pointless.
assert FREEZE_EPOCHS > WARMUP_EPOCHS, (
    f"FREEZE_EPOCHS ({FREEZE_EPOCHS}) must exceed WARMUP_EPOCHS ({WARMUP_EPOCHS}); "
    f"otherwise Phase 1 is 100% warmup with no stable training."
)


# ╔══════════════════════════════════════════════════════════════╗
# ║                     DEVICE DETECTION                         ║
# ╚══════════════════════════════════════════════════════════════╝

def detect_device():

    if not torch.cuda.is_available():
        print("=" * 60)
        print("  ❌  ERROR: No CUDA GPU detected on this machine!")
        print("=" * 60)
        print("  Make sure CUDA drivers and PyTorch CUDA are installed.")
        print("  Check with: python -c \"import torch; print(torch.cuda.is_available())\"")
        print("  Install:    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        raise SystemExit(1)

    gpu_count = torch.cuda.device_count()
    name      = torch.cuda.get_device_name(0)
    vram      = min(
        torch.cuda.get_device_properties(i).total_memory
        for i in range(gpu_count)
    ) / 1e9

    print(f"  GPUs found : {gpu_count}x {name}")
    print(f"  VRAM (each): {vram:.1f} GB")

    if gpu_count > 1:
        device = ",".join(str(i) for i in range(gpu_count))
        print(f"  Mode       : Multi-GPU ({device})")
    else:
        device = "0"
        print(f"  Mode       : Single GPU")

    if   vram >= 40: workers = 16
    elif vram >= 20: workers = 12
    elif vram >= 16: workers = 8
    elif vram >= 10: workers = 6
    elif vram >=  6: workers = 4
    else:            workers = 2

    amp = True
    if "1650" in name or "1660" in name or "1050" in name or "1060" in name:
        amp = False
        print(f"  AMP        : Disabled (older GPU — avoids NaN losses)")
    else:
        print(f"  AMP        : Enabled (faster training with mixed precision)")

    return device, int(vram), workers, amp, gpu_count


def count_train_images():
    """Count images in the training split so auto_batch can avoid a final
    batch of exactly 1 image (BatchNorm crashes when batch size == 1)."""
    train_dir = FILTERED_DATASET_DIR / "train"
    if not train_dir.exists():
        return None
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    n = sum(1 for p in train_dir.rglob("*") if p.suffix.lower() in exts)
    return n if n > 0 else None


def auto_batch(vram_gb, gpu_count, dataset_size=None):
    # Classification at 224px is far lighter than 640px detection, so batch
    # sizes are roughly 2x what train_fire.py uses for the same VRAM tier.
    if   vram_gb >= 40: batch_per_gpu = 128
    elif vram_gb >= 24: batch_per_gpu = 64
    elif vram_gb >= 16: batch_per_gpu = 32
    elif vram_gb >= 10: batch_per_gpu = 24
    elif vram_gb >=  6: batch_per_gpu = 16
    else:               batch_per_gpu = 8

    total_batch = batch_per_gpu * gpu_count

    if dataset_size is not None and total_batch > 1:
        remainder = dataset_size % total_batch
        if remainder == 1:
            total_batch -= 1
            print(f"  ⚠️  Batch adjusted {total_batch + 1} → {total_batch} "
                  f"to avoid a final batch of size 1 (train images = {dataset_size})")

    print(f"  Batch      : {batch_per_gpu}/GPU × {gpu_count} GPU = {total_batch} total")
    return total_batch


def shared_args(device, batch, workers, amp):
    return dict(
        data            = str(FILTERED_DATASET_DIR),
        imgsz           = IMG_SIZE,
        batch           = batch,
        device          = device,
        workers         = workers,
        momentum        = MOMENTUM,
        weight_decay    = WEIGHT_DECAY,
        warmup_epochs   = WARMUP_EPOCHS,
        warmup_momentum = WARMUP_MOMENTUM,
        warmup_bias_lr  = WARMUP_BIAS_LR,
        patience        = PATIENCE,
        fliplr          = FLIPLR,
        flipud          = FLIPUD,
        degrees         = DEGREES,
        translate       = TRANSLATE,
        scale           = SCALE,
        shear           = SHEAR,
        perspective     = PERSPECTIVE,
        hsv_h           = HSV_H,
        hsv_s           = HSV_S,
        hsv_v           = HSV_V,
        mixup           = MIXUP,
        cutmix          = CUTMIX,
        erasing         = ERASING,
        auto_augment    = AUTO_AUGMENT,
        dropout         = DROPOUT,
        label_smoothing = LABEL_SMOOTHING,
        cache           = "disk",      # set to "ram" instead — dataset is small (~20k imgs), fits comfortably
        amp             = amp,
        cos_lr          = True,
        seed            = SEED,
        plots           = True,
        verbose         = True,
        save_period     = SAVE_PERIOD,
        project         = PROJECT,
    )


def save_state(state: dict):
    """Atomic write: dump to a temp file in the same dir, then os.replace().

    Prevents a half-written training_state.json if the process is killed
    mid-save (OOM / power loss), which would otherwise crash the next run.
    """
    os.makedirs(PROJECT, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=PROJECT, prefix=".state-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, STATE_FILE)   # atomic on POSIX/NTFS
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def load_state() -> dict | None:
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  ⚠️  Corrupt/unreadable state file ({exc}) — starting fresh.")
        try:
            os.remove(STATE_FILE)
        except OSError:
            pass
        return None


def detect_resume_state():
    if FORCE_RESTART:
        print("  FORCE_RESTART=True — ignoring any saved checkpoints.")
        return _fresh_state()

    state = load_state()
    if state is None:
        return _fresh_state()

    run_name   = state["run_name"]
    phase1_dir = state["phase1_dir"]
    phase2_dir = state["phase2_dir"]

    if state.get("phase2_done"):
        return dict(mode="done", run_name=run_name,
                    phase1_dir=phase1_dir, phase2_dir=phase2_dir,
                    p1_last=None, p2_last=None, phase1_best=None)

    if state.get("phase1_done"):
        phase1_best = state.get("phase1_best")
        p2_last = os.path.join(phase2_dir, "weights", "last.pt")
        if os.path.exists(p2_last):
            return dict(mode="resume_phase2", run_name=run_name,
                        phase1_dir=phase1_dir, phase2_dir=phase2_dir,
                        p1_last=None, p2_last=p2_last, phase1_best=phase1_best)
        else:
            return dict(mode="skip_to_phase2", run_name=run_name,
                        phase1_dir=phase1_dir, phase2_dir=phase2_dir,
                        p1_last=None, p2_last=None, phase1_best=phase1_best)

    p1_last = os.path.join(phase1_dir, "weights", "last.pt")
    if os.path.exists(p1_last):
        return dict(mode="resume_phase1", run_name=run_name,
                    phase1_dir=phase1_dir, phase2_dir=phase2_dir,
                    p1_last=p1_last, p2_last=None, phase1_best=None)

    print("  State file found but no weights on disk — starting fresh.")
    return _fresh_state()


def _fresh_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    run_name   = f"disease_{datetime.now().strftime('%Y%m%d_%H%M')}"
    phase1_dir = os.path.join(PROJECT, run_name + "_phase1")
    phase2_dir = os.path.join(PROJECT, run_name + "_phase2")
    return dict(mode="fresh", run_name=run_name,
                phase1_dir=phase1_dir, phase2_dir=phase2_dir,
                p1_last=None, p2_last=None, phase1_best=None)


# ╔══════════════════════════════════════════════════════════════╗
# ║                DATASET PREPARATION (filter + split)          ║
# ╚══════════════════════════════════════════════════════════════╝

def normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def find_dataset_root(search_root: Path):
    """The raw Kaggle download often nests images one or two folders deep
    (e.g. plantvillage_raw/PlantVillage/PlantVillage/...). Walk the tree and
    return the directory that actually contains the most class subfolders."""
    best_dir, best_count = None, 0
    for dirpath, dirnames, _ in os.walk(search_root):
        class_dirs = [d for d in dirnames if "___" in d or "healthy" in d.lower()]
        if len(class_dirs) > best_count:
            best_count = len(class_dirs)
            best_dir = Path(dirpath)
    return best_dir


def prepare_dataset():
    """Filter the raw multi-crop PlantVillage dump down to only the 15
    tomato/potato/pepper classes and split each into train/val. Idempotent —
    skips rebuilding if FILTERED_DATASET_DIR is already populated."""

    if not FORCE_REBUILD_DATASET and FILTERED_DATASET_DIR.exists():
        train_dir = FILTERED_DATASET_DIR / "train"
        has_images = train_dir.exists() and any(
            p.suffix.lower() in (".jpg", ".jpeg", ".png") for p in train_dir.rglob("*")
        )
        if has_images:
            print(f"  Filtered dataset already exists at {FILTERED_DATASET_DIR} — skipping rebuild.")
            print(f"  Set FORCE_REBUILD_DATASET=True to rebuild from raw data.")
            return

    if not RAW_DATASET_DIR.exists():
        print(f"  ❌ ERROR: raw dataset folder not found: {RAW_DATASET_DIR}")
        print(f"  Download the PlantVillage dataset from Kaggle and extract it there.")
        raise SystemExit(1)

    print(f"\n  Locating class folders inside: {RAW_DATASET_DIR}")
    dataset_root = find_dataset_root(RAW_DATASET_DIR)
    if dataset_root is None:
        print(f"  ❌ ERROR: could not find any class folders under {RAW_DATASET_DIR}")
        raise SystemExit(1)
    print(f"  ✅ Dataset root: {dataset_root}")

    all_disk_classes = sorted(d.name for d in dataset_root.iterdir() if d.is_dir())
    disk_lookup = {normalize(d): d for d in all_disk_classes}

    print("\n  Matching target classes against disk...")
    resolved = []
    for cls in SELECTED_CLASSES:
        key = normalize(cls)
        if key in disk_lookup:
            actual = disk_lookup[key]
            marker = "✅" if actual == cls else "🔄"
            suffix = f"  → mapped from '{cls}'" if actual != cls else ""
            print(f"    {marker} {actual}{suffix}")
            resolved.append((cls, actual))
        else:
            print(f"    ❌ NOT FOUND: '{cls}' — skipping")

    if len(resolved) < len(SELECTED_CLASSES):
        print(f"\n  ⚠️  Only found {len(resolved)}/{len(SELECTED_CLASSES)} target classes.")
    if not resolved:
        print("  ❌ ERROR: none of the target classes were found on disk.")
        raise SystemExit(1)

    # ── Dataset inspector — image counts + imbalance warning ────────
    exts = {".jpg", ".jpeg", ".png"}
    print("\n" + "=" * 65)
    print("  DATASET INSPECTION")
    print("=" * 65)
    counts = {}
    for label, actual in resolved:
        folder = dataset_root / actual
        n = sum(1 for p in folder.iterdir() if p.suffix.lower() in exts)
        counts[label] = n
        flag = "⚠️  LOW" if n < MIN_IMAGES_WARNING else ("ℹ️  moderate" if n < 500 else "✅ good")
        print(f"    {n:>5} images  —  {label:<50} {flag}")

    total = sum(counts.values())
    min_cls = min(counts, key=counts.get)
    max_cls = max(counts, key=counts.get)
    ratio = counts[max_cls] / max(counts[min_cls], 1)
    print(f"\n  TOTAL : {total} images across {len(resolved)} classes")
    print(f"  Smallest : {min_cls} ({counts[min_cls]} images)")
    print(f"  Largest  : {max_cls} ({counts[max_cls]} images)")
    if ratio > 5:
        print(f"  ⚠️  CLASS IMBALANCE: largest class is {ratio:.1f}x the smallest — "
              f"the model may under-perform on '{min_cls}'.")
    print("=" * 65 + "\n")

    # ── Build train/val split ────────────────────────────────────────
    print("  Building train/val split...")
    random.seed(SEED)
    for label, actual in resolved:
        src = dataset_root / actual
        imgs = [p for p in src.iterdir() if p.suffix.lower() in exts]
        random.shuffle(imgs)
        cut = int(len(imgs) * TRAIN_SPLIT)
        train_imgs, val_imgs = imgs[:cut], imgs[cut:]

        for split, split_imgs in [("train", train_imgs), ("val", val_imgs)]:
            out_dir = FILTERED_DATASET_DIR / split / label
            out_dir.mkdir(parents=True, exist_ok=True)
            for img in split_imgs:
                shutil.copy2(img, out_dir / img.name)

        print(f"    ✓ {label:<50} {len(train_imgs):>4} train | {len(val_imgs):>3} val")

    print(f"\n  ✅ Dataset ready at {FILTERED_DATASET_DIR}\n")


# ╔══════════════════════════════════════════════════════════════╗
# ║                        VALIDATION                            ║
# ╚══════════════════════════════════════════════════════════════╝

def validate(model, output_dir):
    print("\n  Validating best model...")
    best = os.path.join(output_dir, "weights", "best.pt")
    if os.path.exists(best):
        model = YOLO(best)

    metrics = model.val(data=str(FILTERED_DATASET_DIR), augment=True)  # TTA
    top1 = metrics.top1
    top5 = metrics.top5

    g = lambda v, t: "✅" if v >= t else ("⚠️ " if v >= t * 0.85 else "❌")

    print("\n" + "=" * 52)
    print("  FINAL RESULTS")
    print("=" * 52)
    print(f"  {g(top1, 0.90)}  Top-1 Accuracy : {top1*100:.2f}%   (target ≥ 90%)")
    print(f"  {g(top5, 0.98)}  Top-5 Accuracy : {top5*100:.2f}%   (target ≥ 98%)")
    print("=" * 52)

    if top1 >= 0.90:
        print("\n  ✅ Excellent! Model is ready for deployment.")
    elif top1 >= 0.75:
        print("\n  ⚠️  Good model. Consider more epochs, more data, or checking class imbalance.")
    else:
        print("\n  ❌ Low accuracy. Try more epochs, a larger dataset, or verify labels.")

    return metrics


def main():
    print("=" * 60)
    print("   YOLOv8-cls Plant Disease — Tomato / Potato / Pepper")
    print("=" * 60)

    device, vram, workers, amp, gpu_count = detect_device()

    print("\n" + "─" * 60)
    print("  Preparing dataset (filter + split)")
    print("─" * 60)
    prepare_dataset()

    n_train = count_train_images()
    batch = auto_batch(vram, gpu_count, dataset_size=n_train)
    os.makedirs(PROJECT, exist_ok=True)

    rs = detect_resume_state()
    mode       = rs["mode"]
    run_name   = rs["run_name"]
    phase1_dir = rs["phase1_dir"]
    phase2_dir = rs["phase2_dir"]

    print(f"\n  Model      : {MODEL}")
    print(f"  Strategy   : STAGED (Phase 1: frozen backbone → Phase 2: full fine-tune)")
    print(f"  Phase 1    : {FREEZE_EPOCHS} epochs — AdamW, frozen backbone (head warmup)")
    print(f"  Phase 2    : {FINETUNE_EPOCHS} epochs — SGD + cosine LR, all layers")
    print(f"  Image size : {IMG_SIZE}px")
    print(f"  Seed       : {SEED}")
    print(f"  Run name   : {run_name}")
    print(f"  Resume mode: {mode}")

    if PRETRAINED_MODEL:
        print(f"\n  Pretrained : {PRETRAINED_MODEL}")
        try:
            probe = YOLO(PRETRAINED_MODEL)
            n_classes = len(probe.names)
            if n_classes == len(SELECTED_CLASSES):
                print(f"  ✅ Class count check passed: {n_classes} classes")
            else:
                print(f"  ⚠️  Class count mismatch: model has {n_classes}, expected {len(SELECTED_CLASSES)}")
                print(f"     Phase 1 will retrain the classification head — this is safe to continue.")
            del probe
        except Exception as e:
            print(f"  ❌ Could not load pretrained model: {e}")
            raise SystemExit(1)

    if mode == "done":
        print("\n  Training already complete for this run.")
        print(f"  Results in: {phase2_dir}/")
        print("  Set FORCE_RESTART=True to retrain from scratch.")
        validate(YOLO(os.path.join(phase2_dir, "weights", "best.pt")), phase2_dir)
        raise SystemExit(0)

    if mode in ("fresh", "resume_phase1"):
        print("\n" + "─" * 60)
        if mode == "resume_phase1":
            print(f"  RESUMING PHASE 1 from: {rs['p1_last']}")
        else:
            print(f"  PHASE 1 / 2 — Frozen backbone ({FREEZE_EPOCHS} epochs, AdamW)")
            print(f"  Trains classification head only — fast convergence on new classes")
        print("─" * 60 + "\n")

        phase1_name = run_name + "_phase1"
        torch.cuda.empty_cache()

        if mode == "resume_phase1":
            model = YOLO(rs["p1_last"])
            model.train(
                **shared_args(device, batch, workers, amp),
                resume    = True,
                epochs    = FREEZE_EPOCHS,
                freeze    = FREEZE_LAYERS,
                optimizer = "AdamW",
                lr0       = LR_PHASE1,
                lrf       = LRF,
                name      = phase1_name,
            )
        else:
            model = YOLO(MODEL)
            model.train(
                **shared_args(device, batch, workers, amp),
                epochs    = FREEZE_EPOCHS,
                freeze    = FREEZE_LAYERS,
                optimizer = "AdamW",
                lr0       = LR_PHASE1,
                lrf       = LRF,
                name      = phase1_name,
            )

        real_phase1_dir  = str(model.trainer.save_dir)
        real_phase1_best = str(model.trainer.best)

        if not os.path.exists(real_phase1_best):
            real_phase1_best = str(model.trainer.last)
            print(f"  ⚠️  best.pt missing, falling back to last.pt")

        print(f"\n  ✅ Phase 1 complete")
        print(f"     Dir  : {real_phase1_dir}")
        print(f"     Best : {real_phase1_best}")

        save_state(dict(
            run_name    = run_name,
            phase1_dir  = real_phase1_dir,
            phase1_best = real_phase1_best,
            phase2_dir  = phase2_dir,
            phase1_done = True,
            phase2_done = False,
        ))

        phase1_dir     = real_phase1_dir
        p1_best_for_p2 = real_phase1_best

    else:
        model          = None
        phase1_dir     = rs["phase1_dir"]
        p1_best_for_p2 = rs["phase1_best"]
        if not p1_best_for_p2:
            print("  ❌ ERROR: state file has no Phase 1 weights path "
                  "(corrupt or pre-upgrade state). Set FORCE_RESTART=True to retrain.")
            raise SystemExit(1)

    print("\n" + "─" * 60)
    if mode == "resume_phase2":
        print(f"  RESUMING PHASE 2 from: {rs['p2_last']}")
    else:
        print(f"  PHASE 2 / 2 — Full fine-tune ({FINETUNE_EPOCHS} epochs, SGD + cosine LR)")
        print(f"  All layers unlocked — deep feature adaptation")
        print(f"  Loading weights: {p1_best_for_p2}")
    print("─" * 60 + "\n")

    if mode != "resume_phase2":
        if not os.path.exists(p1_best_for_p2):
            print(f"  ❌ ERROR: Phase 1 weights not found: {p1_best_for_p2}")
            print(f"  Check your {PROJECT}/ folder and update the path manually.")
            raise SystemExit(1)
        print(f"  ✅ Phase 1 weights verified on disk")

    phase2_name = run_name + "_phase2"

    if mode == "resume_phase2":
        model2 = YOLO(rs["p2_last"])
        model2.train(
            **shared_args(device, batch, workers, amp),
            resume    = True,
            epochs    = FINETUNE_EPOCHS,
            freeze    = 0,
            optimizer = "SGD",
            lr0       = LR_PHASE2,
            lrf       = LRF,
            name      = phase2_name,
        )
    else:
        model2 = YOLO(p1_best_for_p2)
        model2.train(
            **shared_args(device, batch, workers, amp),
            epochs    = FINETUNE_EPOCHS,
            freeze    = 0,
            optimizer = "SGD",
            lr0       = LR_PHASE2,
            lrf       = LRF,
            name      = phase2_name,
        )

    real_phase2_dir = str(model2.trainer.save_dir)

    save_state(dict(
        run_name    = run_name,
        phase1_dir  = phase1_dir,
        phase1_best = p1_best_for_p2,
        phase2_dir  = real_phase2_dir,
        phase1_done = True,
        phase2_done = True,
    ))

    validate(model2, real_phase2_dir)

    best_final = os.path.join(real_phase2_dir, "weights", "best.pt")
    print(f"\n  ✅ Training complete! Files saved to: {real_phase2_dir}/")
    print(f"   └── weights/best.pt       ← use this for inference")
    print(f"   └── weights/last.pt")
    print(f"   └── results.png           ← accuracy/loss curves")
    print(f"   └── confusion_matrix.png  ← per-class accuracy (15x15)")

    onnx_path = str(Path(best_final).with_suffix(".onnx"))
    print(f"\n  Exporting best model to ONNX...")
    try:
        export_model = YOLO(best_final)
        export_model.export(format="onnx", imgsz=IMG_SIZE, dynamic=True)
        print(f"  ✅ ONNX model saved: {onnx_path}")
        print(f"     Use for edge cameras, Jetson, or CPU-only deployments.")
    except Exception as e:
        print(f"  ⚠️  ONNX export failed: {e} — best.pt still usable.")

    print(f"\n  Inference command (PyTorch):")
    print(f'   yolo classify predict model="{os.path.abspath(best_final)}" source=your_leaf.jpg')
    print(f"\n  Inference command (ONNX):")
    print(f'   yolo classify predict model="{os.path.abspath(onnx_path)}" source=your_leaf.jpg')


if __name__ == '__main__':
    main()
