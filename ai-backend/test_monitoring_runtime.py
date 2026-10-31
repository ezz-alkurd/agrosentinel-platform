import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from monitoring_runtime import ContinuousCapture, PresenceReporter
from detection_timing import Confirmer

class FakeCapture:
    def __init__(self, frames): self.frames=list(frames); self.released=False
    def isOpened(self): return True
    def read(self): return self.frames.pop(0) if self.frames else (False,None)
    def get(self, prop): return 30
    def release(self): self.released=True

class MonitoringChecks(unittest.TestCase):
    def test_source_reconnect_breaks_confirmation_but_keeps_alert_cooldown(self):
        confirmer=Confirmer(2,30)
        self.assertFalse(confirmer.update('fire',True,0))
        self.assertTrue(confirmer.update('fire',True,2))
        confirmer.reset_continuity()
        self.assertFalse(confirmer.update('fire',True,5))
        self.assertFalse(confirmer.update('fire',True,7))
        self.assertTrue(confirmer.update('fire',True,32))
        confirmer.reset_continuity()
        self.assertFalse(confirmer.update('new-leaf',True,40))
        confirmer.reset_continuity()
        self.assertFalse(confirmer.update('new-leaf',True,50))

    def test_heartbeat_failure_recovers_without_ending_worker(self):
        recovered=threading.Event(); offline=threading.Event(); calls=[]
        def send():
            calls.append(1)
            if len(calls)==1: raise ConnectionError('hosting unavailable')
            recovered.set()
        reporter=PresenceReporter(send,offline.set,interval=.01,log=lambda *a,**k:None)
        reporter.start()
        try: self.assertTrue(recovered.wait(1))
        finally: reporter.close()
        self.assertGreaterEqual(len(calls),2); self.assertTrue(offline.is_set())

    def test_slow_heartbeat_runs_off_detection_thread(self):
        entered=threading.Event(); release=threading.Event()
        def send(): entered.set(); release.wait(1)
        reporter=PresenceReporter(send,lambda:None,interval=.01)
        reporter.start()
        try:
            self.assertTrue(entered.wait(1))
            capture=ContinuousCapture(0,lambda:False,factory=lambda _:FakeCapture([(True,'frame')]))
            self.assertEqual(capture.read(),(True,'frame')); capture.close()
        finally: release.set(); reporter.close()

    def test_video_reopens_after_eof_when_repeat_enabled(self):
        with TemporaryDirectory() as folder:
            video=Path(folder)/'clip.avi'; video.touch(); opened=[]
            def factory(_):
                cap=FakeCapture([(True,'frame')]); opened.append(cap); return cap
            capture=ContinuousCapture(str(video),lambda:False,loop_video=True,factory=factory,log=lambda *a,**k:None)
            with patch.object(capture,'_wait'):
                self.assertEqual(capture.read(),(True,'frame'))
                self.assertEqual(capture.read(),(True,'frame'))
            self.assertEqual(len(opened),2); self.assertTrue(opened[0].released)
            self.assertTrue(capture.discontinuity); capture.close()

    def test_video_completes_without_repeat(self):
        with TemporaryDirectory() as folder:
            video=Path(folder)/'clip.avi'; video.touch()
            capture=ContinuousCapture(str(video),lambda:False,factory=lambda _:FakeCapture([]))
            self.assertEqual(capture.read(),(False,None)); capture.close()

    def test_camera_failure_reconnects_and_stop_ends_reads(self):
        stopped=threading.Event(); caps=iter([FakeCapture([]),FakeCapture([(True,'reconnected')])])
        capture=ContinuousCapture(0,stopped.is_set,factory=lambda _:next(caps),log=lambda *a,**k:None)
        with patch.object(capture,'_wait'):
            self.assertEqual(capture.read(),(True,'reconnected'))
        stopped.set(); self.assertEqual(capture.read(),(False,None)); capture.close()

if __name__=='__main__': unittest.main()
