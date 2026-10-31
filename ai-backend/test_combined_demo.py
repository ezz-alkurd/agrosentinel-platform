"""Offline combined camera tests; no Firebase writes."""
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import numpy as np
import run_detection as runner
from detection_timing import Confirmer
from demo_launcher import detection_arguments, PROFILES

def model_for(predictions):
    names = {0:"Tomato_Early_blight",1:"Tomato_Late_blight",2:"Tomato_healthy"}
    return Mock(side_effect=[[SimpleNamespace(names=names,boxes=None,
        probs=SimpleNamespace(top1=index,top1conf=confidence))] for index,confidence in predictions])

class PlantCameraTests(unittest.TestCase):
    def setUp(self): self.frame=np.zeros((224,224,3),dtype=np.uint8)
    def run_frames(self,predictions,times):
        model=model_for(predictions); gate=Confirmer()
        with patch.object(runner,"_upload_async") as upload:
            for now in times: runner.run_disease(model,self.frame,self.frame.copy(),gate,now,True)
            return upload.call_args_list
    def test_confident_disease_uploads_full_frame_after_confirmation(self):
        calls=self.run_frames([(1,.96)]*3,[0,1,2])
        self.assertEqual(len(calls),1)
        self.assertIs(calls[0].args[0],runner.handle_disease_classification)
        self.assertEqual(calls[0].args[2],"Tomato___Late_blight")
        self.assertEqual(calls[0].args[3],.96)
        self.assertIsNone(calls[0].args[-1])
    def test_healthy_uncertain_and_invalid_scores_do_not_alert(self):
        for prediction in [(2,.99),(1,.89),(1,float("nan"))]:
            self.assertEqual(self.run_frames([prediction]*2,[0,3]),[])
    def test_changing_disease_resets_confirmation(self):
        self.assertEqual(self.run_frames([(0,.96),(1,.96)],[0,2]),[])
        calls=self.run_frames([(0,.96),(1,.96),(1,.96)],[0,2,4])
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0].args[2],"Tomato___Late_blight")
    def test_healthy_frame_resets_confirmation(self):
        self.assertEqual(self.run_frames([(1,.96),(2,.99),(1,.96)],[0,1,2]),[])
    def test_single_image_supports_classifier_without_boxes(self):
        with patch.object(runner.cv2,"imread",return_value=self.frame),patch.object(runner,"_upload_async") as upload:
            runner.process_single_image("leaf.jpg",None,model_for([(0,.95)]),True)
            upload.assert_called_once()
            self.assertEqual(upload.call_args.args[2],"Tomato___Early_blight")
    def test_disease_evidence_preserves_mobile_schema(self):
        import detect_and_upload as uploads
        with patch.object(uploads,"save_full_image",return_value=("local.jpg","local.jpg")),patch.object(uploads,"upload_image",return_value=("detections/disease/local.jpg","https://example.invalid/evidence")),patch.object(uploads,"log_event") as log:
            uploads.handle_disease_classification(self.frame,"Tomato___Late_blight",.96,0,0,event_context={"plant_model_sha256":"verified-model"})
            event=log.call_args.kwargs
            self.assertEqual(event["anomaly_type"],"disease")
            self.assertEqual(event["extra"]["disease_name"],"Tomato___Late_blight")
            self.assertEqual(event["extra"]["saved_mode"],"full_image")
            self.assertEqual(event["extra"]["plant_model_sha256"],"verified-model")

class LauncherTests(unittest.TestCase):
    def test_default_profile_enables_both(self):
        args=detection_arguments("Camera or recorded video","0",PROFILES[0],Path("ai-backend"))
        self.assertNotIn("--no-disease",args);self.assertNotIn("--no-fire",args)
    def test_single_model_choices(self):
        args=detection_arguments("Camera or recorded video","0","Fire only",Path("ai-backend"))
        self.assertIn("--no-disease",args)
        args=detection_arguments("Single recorded image","leaf.jpg","Tomato leaves only",Path("ai-backend"))
        self.assertIn("--no-fire",args);self.assertIn("--image",args);self.assertNotIn("--no-disease",args)

if __name__=="__main__": unittest.main()
