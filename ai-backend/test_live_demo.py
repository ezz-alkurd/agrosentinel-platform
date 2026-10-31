"""Offline regression checks; never write synthetic Firebase events."""
import os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from detection_timing import Confirmer
from runtime_config import resolve_model

class ConfirmationTests(unittest.TestCase):
    def test_continuity_and_cooldown(self):
        gate = Confirmer()
        self.assertFalse(gate.update("fire", True, 0))
        self.assertFalse(gate.update("fire", True, 1.9))
        self.assertTrue(gate.update("fire", True, 2))
        self.assertFalse(gate.update("fire", True, 3))
        self.assertFalse(gate.update("fire", True, 5))
        self.assertTrue(gate.update("fire", True, 32))

    def test_missing_frame_resets_confirmation(self):
        gate = Confirmer()
        gate.update("fire", True, 10)
        gate.update("fire", False, 11)
        self.assertFalse(gate.update("fire", True, 12))
        self.assertFalse(gate.update("fire", True, 13))
        self.assertTrue(gate.update("fire", True, 14))

    def test_fire_and_smoke_confirm_independently(self):
        gate = Confirmer()
        gate.update("fire", True, 10)
        gate.update("smoke", True, 11)
        self.assertTrue(gate.update("fire", True, 12))
        self.assertFalse(gate.update("smoke", True, 12))

class ModelPathTests(unittest.TestCase):
    def test_explicit_missing_model_does_not_fall_back(self):
        with self.assertRaises(FileNotFoundError):
            resolve_model("fire_best.pt", "definitely-missing.pt")

    def test_configured_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "fire_best.pt"
            checkpoint.write_bytes(b"test path only; never loaded as a model")
            with patch.dict(os.environ, {"AGROSENTINEL_MODELS_DIR": directory}):
                self.assertEqual(resolve_model("fire_best.pt"), checkpoint.resolve())

class UploadTests(unittest.TestCase):
    def test_failure_is_reported_to_caller(self):
        import detect_and_upload as uploads
        with patch.object(uploads, "save_full_image", side_effect=OSError("disk unavailable")):
            with self.assertRaises(OSError):
                uploads.handle_fire_detection(None, "fire", .8, 0, 0)

    def test_evidence_and_source_metadata_reach_event(self):
        import detect_and_upload as uploads
        with patch.object(uploads, "save_full_image", return_value=("local.jpg", "local.jpg")), patch.object(uploads, "upload_image", return_value=("detections/fire/local.jpg", "https://example.invalid/evidence")), patch.object(uploads, "log_event") as log:
            uploads.handle_fire_detection(None, "smoke", .85, 0, 0, event_context={"source_type":"Recorded image","confirmation_mode":"single_image"})
            event = log.call_args.kwargs
            self.assertEqual(event["anomaly_type"], "smoke")
            self.assertEqual(event["extra"]["source_type"], "Recorded image")
            self.assertEqual(event["storage_path"], "detections/fire/local.jpg")

if __name__ == "__main__":
    unittest.main()
