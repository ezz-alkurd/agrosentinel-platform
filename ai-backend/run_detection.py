"""
run_detection.py — AgroSentinel drone detection driver.

Loads the two current models and sends confirmed detections to the ASP.NET
API. Firebase is available only through the explicit legacy backend.

MODELS
  fire    -> reviewed fire_best.pt (fire detector)
  plant   -> reviewed plant_disease_best.pt (three-class tomato classifier)

Plant input must be a close-up tomato leaf filling the frame. The classifier
has no leaf detector or unsupported-object rejection. Healthy and uncertain
results do not create disease alerts. Explicit detector overrides are supported.

USAGE (run on a machine with a camera / the ultralytics runtime installed):
    pip install ultralytics opencv-python firebase-admin
    python run_detection.py                 # default webcam (source 0)
    python run_detection.py --source 1       # another camera
    python run_detection.py --source path/to/video.mp4
    python run_detection.py --image leaf.jpg # classify/detect one image and exit
    python run_detection.py --no-disease     # fire detection only
    python run_detection.py --headless       # no preview window (e.g. on a Pi)

Press 'q' in the preview window to quit.
"""

from __future__ import annotations

import sys
import os
import time
import argparse
import threading
import hashlib
import math
from datetime import datetime, UTC
from pathlib import Path

import cv2

# ── make the upload library importable regardless of launch directory ──
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Legacy handlers are imported only for explicitly selected Firebase runs.
def handle_fire_detection(*args, **kwargs):
    from detect_and_upload import handle_fire_detection as handler
    return handler(*args, **kwargs)
def handle_disease_classification(*args, **kwargs):
    from detect_and_upload import handle_disease_classification as handler
    return handler(*args, **kwargs)
def update_device_status(*args, **kwargs):
    from detect_and_upload import update_device_status as handler
    return handler(*args, **kwargs)
def set_device_offline(*args, **kwargs):
    from detect_and_upload import set_device_offline as handler
    return handler(*args, **kwargs)
_api_transport = None

# ── legacy-checkpoint import shim (models trained on old ultralytics) ──
def _patch_ultralytics_yolo() -> None:
    from types import ModuleType
    mappings = {
        "ultralytics.yolo": "ultralytics",
        "ultralytics.yolo.utils": "ultralytics.utils",
        "ultralytics.yolo.utils.ops": "ultralytics.utils.ops",
        "ultralytics.yolo.utils.loss": "ultralytics.utils.loss",
        "ultralytics.yolo.utils.metrics": "ultralytics.utils.metrics",
        "ultralytics.yolo.utils.plotting": "ultralytics.utils.plotting",
        "ultralytics.yolo.engine": "ultralytics.engine",
        "ultralytics.yolo.engine.results": "ultralytics.engine.results",
        "ultralytics.yolo.v8": "ultralytics.models.yolo",
        "ultralytics.yolo.v8.detect": "ultralytics.models.yolo.detect",
    }
    for old, new in mappings.items():
        if old not in sys.modules:
            try:
                sys.modules[old] = __import__(new, fromlist=[""])
            except ImportError:
                sys.modules[old] = ModuleType(old)

os.environ.setdefault("YOLO_CONFIG_DIR", str(SCRIPT_DIR.parent / "runtime" / "ultralytics"))
_patch_ultralytics_yolo()
from ultralytics import YOLO

# ── paths ──
MODELS_DIR = SCRIPT_DIR.parent / "models"
FIRE_MODEL = MODELS_DIR / "fire_best.pt"
DISEASE_MODEL = MODELS_DIR / "plant_disease_best.pt"

# ── thresholds & timers (see docs/INTEGRATION_RULES.md) ──
CONF = 0.15                  # inference floor — boxes below this never returned
FIRE_UPLOAD_CONF = 0.70      # fire/smoke: confirm/upload at >= 70%
DISEASE_UPLOAD_CONF = 0.90   # plant disease: confirm/upload at >= 90%
CONFIRM_SECONDS = 2.0        # must stay above the gate this long before uploading
SAVE_COOLDOWN = 30.0         # after an upload, don't re-upload same anomaly for 30s

FIRE_EXCLUDE = {"other"}                 # substrings to drop (fire model)
DISEASE_SKIP_HEALTHY = True              # don't upload "healthy" classifications

# Real location via IP geolocation (resolved at startup in main()).
from gps import get_coordinates
GPS_LAT, GPS_LNG = 0.0, 0.0

# background upload threads (non-daemon so uploads finish before exit)
_upload_threads: list[threading.Thread] = []
_upload_failures: list[str] = []
_event_context: dict = {}


def _upload_async(fn, *args, **kwargs) -> None:
    # Keep the source provenance and actual capture time on the saved event.
    context = {**_event_context, "captured_at": datetime.now(UTC).isoformat()}
    def upload():
        try:
            fn(*args, **kwargs, event_context=context)
        except Exception as exc:
            if _api_transport is not None:
                print(f"[sync] Upload pending/failed: {type(exc).__name__}: {str(exc)[:350]}",flush=True)
            else:
                from firebase_diagnostics import describe_error
                _upload_failures.append(type(exc).__name__)
                print("[upload] FAILED: " + describe_error(exc),flush=True)
    _upload_threads[:] = [t for t in _upload_threads if t.is_alive()]
    t = threading.Thread(target=upload, daemon=False)
    t.start()
    _upload_threads.append(t)


from monitoring_runtime import ContinuousCapture, PresenceReporter
from detection_timing import Confirmer
from runtime_config import resolve_model


def run_fire(model: YOLO, frame, confirmer: Confirmer, now: float):
    """Detect fire/smoke; upload confirmed boxes. Returns annotated frame."""
    res = model(frame, conf=CONF, verbose=False)[0]
    best_by_label: dict[str, tuple[float, list[int]]] = {}
    if res.boxes is not None:
        for box in res.boxes:
            label = res.names[int(box.cls[0])].lower()
            if any(x in label for x in FIRE_EXCLUDE):
                continue
            conf = float(box.conf[0])
            if conf < FIRE_UPLOAD_CONF:
                continue
            if label not in best_by_label or conf > best_by_label[label][0]:
                best_by_label[label] = (conf, [int(v) for v in box.xyxy[0].tolist()])

    # confirmation per label (fire / smoke tracked independently)
    for label in ("fire", "smoke"):
        present = label in best_by_label
        if confirmer.update(f"fire:{label}", present, now):
            conf, bbox = best_by_label[label]
            print(f"[fire] CONFIRMED {label} {conf:.2%} -> uploading")
            _upload_async(handle_fire_detection, frame.copy(), label, conf,
                          GPS_LAT, GPS_LNG, bbox)
    return res.plot() if res.boxes is not None else frame


DISEASE_DISPLAY_CONF = 0.35


def _plant_candidates(result):
    """Read actual classifier probabilities or explicit detector boxes."""
    if result.probs is not None:
        index = int(result.probs.top1)
        confidence = float(result.probs.top1conf)
        label = result.names[index]
        canonical = {
            "Tomato_Early_blight": "Tomato___Early_blight",
            "Tomato_Late_blight": "Tomato___Late_blight",
            "Tomato_healthy": "Tomato___healthy",
        }.get(label, label)
        return [(confidence, None, canonical)] if math.isfinite(confidence) and 0 <= confidence <= 1 else []
    candidates = []
    if result.boxes is not None:
        for box in result.boxes:
            confidence = float(box.conf[0])
            if not math.isfinite(confidence) or not 0 <= confidence <= 1:
                continue
            candidates.append((confidence, [int(v) for v in box.xyxy[0].tolist()], result.names[int(box.cls[0])]))
    return candidates


def run_disease(model: YOLO, frame, annotated, confirmer: Confirmer, now: float,
                headless: bool):
    """Confirm a stable disease label; a classifier uploads its full input frame."""
    result = model(frame, conf=CONF, verbose=False)[0]
    candidates = _plant_candidates(result)
    eligible = [candidate for candidate in candidates
                if "healthy" not in candidate[2].lower() and candidate[0] >= DISEASE_UPLOAD_CONF]
    best = max(eligible, key=lambda candidate: candidate[0], default=None)
    # Reset a previous class when the prediction changes or becomes uncertain.
    previous = getattr(confirmer, "plant_label", None)
    current = best[2] if best else None
    if previous is not None and previous != current:
        confirmer.update("disease:" + previous, False, now)
    confirmer.plant_label = current
    if best and confirmer.update("disease:" + best[2], True, now):
        confidence, bbox, label = best
        print(f"[disease] CONFIRMED {label} {confidence:.2%} -> uploading")
        _upload_async(handle_disease_classification, frame.copy(), label, confidence,
                      GPS_LAT, GPS_LNG, bbox)
    if not headless and candidates:
        confidence, bbox, label = max(candidates, key=lambda candidate: candidate[0])
        healthy = "healthy" in label.lower()
        short = label.split("___")[-1].replace("_", " ")
        if bbox is None:
            status = short if confidence >= DISEASE_UPLOAD_CONF else "Inconclusive"
            color = (130, 195, 145) if healthy and confidence >= DISEASE_UPLOAD_CONF else (0, 185, 245)
            cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 70), (25, 35, 28), -1)
            cv2.putText(annotated, f"Tomato close-up: {status} ({confidence:.0%})", (12, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, .55, color, 1)
            cv2.putText(annotated, "One tomato leaf must fill the frame", (12, 53),
                        cv2.FONT_HERSHEY_SIMPLEX, .48, (210, 215, 210), 1)
        elif not healthy and confidence >= DISEASE_DISPLAY_CONF:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 165, 255), 2)
            cv2.putText(annotated, f"{short} {confidence:.0%}", (x1, max(18, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 165, 255), 2)
    return candidates


def process_single_image(path: str, fire_model, disease_model, do_disease: bool, preview_file=None):
    frame = cv2.imread(path)
    if frame is None:
        raise SystemExit(f"Cannot read image: {path}")
    annotated = frame.copy()
    # A one-photo check is explicitly recorded as single_image, without a timer.
    if fire_model is not None:
        annotated = run_fire(fire_model, frame, Confirmer(0), time.monotonic())
    if do_disease and disease_model is not None:
        candidates = run_disease(disease_model, frame, annotated, Confirmer(0), time.monotonic(), not bool(preview_file))
        for confidence, _, label in candidates:
            status = "healthy; no alert" if "healthy" in label.lower() else "inconclusive; no alert" if confidence < DISEASE_UPLOAD_CONF else "disease candidate"
            print(f"[plant] {label} {confidence:.2%} ({status})")

    if preview_file:
        target=Path(preview_file);target.parent.mkdir(parents=True,exist_ok=True)
        ok,encoded=cv2.imencode('.jpg',annotated)
        if ok: target.write_bytes(encoded.tobytes())


def _device_type(source_str: str) -> str:
    """Auto-detect the device/source type for the app's connected state."""
    s = str(source_str)
    if s.isdigit():
        return "Laptop camera"
    if s.startswith(("http://", "https://", "rtsp://", "rtmp://")):
        return "IP / drone stream"
    return "Video file"


def _auto_device_id(source_str: str) -> str:
    """Stable per-source device id so multiple detectors don't collide."""
    import hashlib
    s = str(source_str)
    if s.isdigit():
        return f"laptop-cam-{s}"
    return "stream-" + hashlib.md5(s.encode()).hexdigest()[:8]


def main():
    import signal
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, signal.default_int_handler)
    ap = argparse.ArgumentParser(description="AgroSentinel detection driver")
    ap.add_argument("--sync-only", action="store_true", help="Retry the saved API outbox and exit")
    ap.add_argument("--backend", choices=["api","firebase"], default="api", help="ASP.NET API (default); Firebase is legacy")
    ap.add_argument("--local-only", action="store_true", help="Preview only; no cloud writes")
    ap.add_argument("--preview-file", help="JPEG preview file for the desktop application")
    ap.add_argument("--source", default="0", help="camera index, video path, or stream URL")
    ap.add_argument("--loop-video", action="store_true", help="Replay recorded videos continuously until stopped")
    ap.add_argument("--image", help="classify/detect a single image and exit")
    ap.add_argument("--no-disease", action="store_true", help="fire only")
    ap.add_argument("--no-fire", action="store_true", help="tomato leaf analysis only")
    ap.add_argument("--headless", action="store_true", help="no preview window")
    ap.add_argument("--device-id", help="device doc id to report to (default: auto from source)")
    ap.add_argument("--name", help="device display name shown in the app")
    ap.add_argument("--fire-model", help="Explicit approved fire/smoke checkpoint")
    ap.add_argument("--disease-model", help="Explicit approved plant checkpoint")
    ap.add_argument("--firebase-key", help="Private Firebase service-account file (never committed)")
    ap.add_argument("--ip-location", action="store_true", help="Opt in to approximate IP location; otherwise location is unavailable")
    ap.add_argument("--stop-file", help="Local launcher stop signal file")
    args = ap.parse_args()
    if args.sync_only:
        from api_transport import ApiTransport
        ApiTransport.from_environment(start_worker=False).flush()
        return
    if getattr(sys,"frozen",False) and args.backend=="firebase":
        ap.error("The portable worker supports the ASP.NET API and local preview. Use source Python for legacy Firebase.")
    if args.no_fire and args.no_disease:
        ap.error("Enable at least one model.")

    global handle_fire_detection, handle_disease_classification, update_device_status, set_device_offline, _api_transport
    if args.local_only:
        def local_detection(frame,label,confidence,*values,**context):
            print(f"[local] Confirmed {label} {confidence:.2%}; preview only, no upload.",flush=True)
        handle_fire_detection=handle_disease_classification=local_detection
        update_device_status=lambda *a,**k:None
        set_device_offline=lambda *a,**k:None
        print("LOCAL PREVIEW: cloud synchronization is disabled.",flush=True)
    elif args.backend=="api":
        from api_transport import ApiTransport
        transport=ApiTransport.from_environment()
        _api_transport=transport
        handle_fire_detection=transport.handle_fire_detection
        handle_disease_classification=transport.handle_disease_classification
        update_device_status=transport.update_device_status
        set_device_offline=transport.set_device_offline
        print("Sync backend: ASP.NET API with durable local evidence outbox.",flush=True)

    # Resolve this machine's real location (city-level, via IP).
    global GPS_LAT, GPS_LNG
    GPS_LAT, GPS_LNG = get_coordinates() if args.ip_location else (0.0, 0.0)

    global FIRE_MODEL, DISEASE_MODEL
    if not args.no_fire:
        FIRE_MODEL = resolve_model("fire_best.pt", args.fire_model)
    if not args.no_disease:
        DISEASE_MODEL = resolve_model("plant_disease_best.pt", args.disease_model)
    if args.firebase_key:
        os.environ["FIREBASE_KEY_PATH"] = str(Path(args.firebase_key).resolve())
    _event_context.update({
        "device_id": args.device_id or _auto_device_id(args.image or args.source),
        "source_type": "Recorded image" if args.image else _device_type(args.source),
        "location_source": "ip_approximate" if (GPS_LAT or GPS_LNG) else "unavailable",
        "confirmation_mode": "single_image" if args.image else "continuous_2_seconds",
    })

    print("Loading models...")
    fire_model = None if args.no_fire else YOLO(str(FIRE_MODEL))
    disease_model = None if args.no_disease else YOLO(str(DISEASE_MODEL))
    if fire_model is not None:
        _event_context["fire_model_sha256"] = hashlib.sha256(FIRE_MODEL.read_bytes()).hexdigest()
        print(f"fire classes:    {fire_model.names}")
    if disease_model:
        if disease_model.task not in ("classify", "detect"):
            raise SystemExit("Plant model must be a classifier or detector.")
        _event_context["plant_model_sha256"] = hashlib.sha256(DISEASE_MODEL.read_bytes()).hexdigest()
        _event_context["plant_inference_kind"] = "whole_frame_classification" if disease_model.task == "classify" else "bbox_detection"
        print(f"plant task: {disease_model.task}; classes: {disease_model.names}")
        print("Plant scope: close-up tomato leaves only. Healthy/uncertain results do not create alerts.")

    if args.image:
        process_single_image(args.image, fire_model, disease_model, not args.no_disease,args.preview_file)
        _join_uploads()
        return

    source = int(args.source) if args.source.isdigit() else args.source
    def should_stop():
        return bool(args.stop_file and Path(args.stop_file).exists())
    cap = ContinuousCapture(source, should_stop, loop_video=args.loop_video)

    # ── device presence (heartbeat the app watches) ──
    device_type = _device_type(args.source)
    device_id = args.device_id or _auto_device_id(args.source)
    device_name = args.name or device_type
    models_list = ([] if args.no_fire else ["fire"]) + ([] if args.no_disease else ["disease"])
    started_at = datetime.now(UTC).isoformat()
    presence = PresenceReporter(
        lambda: update_device_status(device_id, device_name, device_type, source,
                                     GPS_LAT, GPS_LNG, models_list, online=True, started_at=started_at),
        lambda: set_device_offline(device_id))
    presence.start()

    fire_conf = Confirmer(CONFIRM_SECONDS, SAVE_COOLDOWN)
    disease_conf = Confirmer(CONFIRM_SECONDS, SAVE_COOLDOWN)
    print("Running. Press 'q' to quit." if not args.headless else "Running headless. Ctrl+C to quit.")

    try:
        while True:
            if should_stop():
                break
            ok, frame = cap.read()
            if not ok:
                break
            if cap.discontinuity:
                cap.discontinuity = False
                fire_conf.reset_continuity()
                disease_conf.reset_continuity()
            now = time.monotonic()
            annotated = run_fire(fire_model, frame, fire_conf, now) if fire_model is not None else frame.copy()
            if disease_model is not None:
                run_disease(disease_model, frame, annotated, disease_conf, now,
                            args.headless and not args.preview_file)

            if int(now) % 2 == 0 and now - getattr(cap, 'last_status', 0) >= 2:
                cap.last_status = now
                print('[monitor] Frame analyzed. Monitoring active.', flush=True)

            if args.preview_file:
                try:
                    target=Path(args.preview_file);target.parent.mkdir(parents=True,exist_ok=True)
                    ok,preview=cv2.imencode('.jpg',annotated,[cv2.IMWRITE_JPEG_QUALITY,75])
                    if ok:
                        temporary=target.with_suffix('.next.jpg');temporary.write_bytes(preview.tobytes());os.replace(temporary,target)
                except OSError:
                    if now-getattr(cap, 'last_preview_error', 0)>10:
                        cap.last_preview_error=now
                        print('[preview] Preview file temporarily unavailable; detection continues.', flush=True)
            if not args.headless:
                cv2.imshow("AgroSentinel — fire + disease", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        cap.close()
        cv2.destroyAllWindows()
        presence.close()
        print("[device] Marked offline.")
        _join_uploads()


def _join_uploads():
    if _upload_threads:
        print(f"Waiting for {len(_upload_threads)} upload(s) to finish...")
        for t in _upload_threads:
            t.join()
    if _upload_failures:
        raise SystemExit(f"{len(_upload_failures)} event upload(s) failed; the phone flow is not verified.")
    if _api_transport is not None:
        pending=len(list(_api_transport.root.glob('*/metadata.json')))
        print(f"[sync] {pending} saved detection(s) awaiting upload." if pending else "[sync] No pending uploads.",flush=True)
    elif not _upload_threads:
        print("No event met the confidence gate; no event was uploaded.")
    print("Done.")


if __name__ == "__main__":
    # Frozen Windows workers must handle multiprocessing helper invocations before argparse.
    import multiprocessing
    multiprocessing.freeze_support()
    main()
