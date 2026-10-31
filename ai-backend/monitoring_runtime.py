"""Continuous capture and background presence, independent of model inference."""
import math
import threading
import time
from pathlib import Path
import cv2


class PresenceReporter:
    """One bounded worker: slow/unavailable hosting never blocks inference."""
    def __init__(self, send, offline, interval=5.0, log=print):
        self.send, self.offline, self.interval, self.log = send, offline, interval, log
        self.stopped = threading.Event()
        self.worker = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.worker.start()

    def _run(self):
        try:
            while not self.stopped.is_set():
                try:
                    self.send()
                except Exception as error:
                    self.log(f"[connection] Heartbeat unavailable ({type(error).__name__}); monitoring continues. Retrying automatically.", flush=True)
                if self.stopped.wait(self.interval):
                    break
        finally:
            try:
                self.offline()
            except Exception as error:
                self.log(f"[connection] Offline update unavailable ({type(error).__name__}).", flush=True)

    def close(self):
        self.stopped.set()
        # HTTP requests have a finite timeout; the UI can display Stopping meanwhile.
        self.worker.join(timeout=40)


class ContinuousCapture:
    def __init__(self, source, should_stop, loop_video=False, factory=None, log=print):
        self.source, self.should_stop, self.loop_video = source, should_stop, loop_video
        self.factory = factory or self._open
        self.log = log
        self.is_file = isinstance(source, str) and Path(source).is_file()
        self.cap = None
        self.next_frame = time.monotonic()
        self.frame_period = 0.0
        self.interrupted = False
        self.discontinuity = False

    @staticmethod
    def _open(source):
        if isinstance(source, str) and '://' in source:
            # FFmpeg stream reads/open are bounded so Stop does not wait forever.
            return cv2.VideoCapture(source, cv2.CAP_FFMPEG, [
                cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000,
                cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000])
        return cv2.VideoCapture(source)

    def _wait(self, seconds):
        until = time.monotonic() + seconds
        while not self.should_stop() and time.monotonic() < until:
            time.sleep(min(.05, max(0, until-time.monotonic())))

    def read(self):
        while not self.should_stop():
            if self.cap is None:
                self.cap = self.factory(self.source)
                if self.is_file and not self.cap.isOpened():
                    self.close()
                    raise RuntimeError('Cannot open video file. Choose a supported, readable video.')
                fps = self.cap.get(cv2.CAP_PROP_FPS) if self.is_file else 0
                self.frame_period = 1/fps if math.isfinite(fps) and fps > 0 else 0
                self.next_frame = time.monotonic()
            try:
                ok, frame = self.cap.read() if self.cap.isOpened() else (False, None)
            except cv2.error:
                ok, frame = False, None
            if ok:
                self._wait(max(0, self.next_frame-time.monotonic()))
                self.next_frame = max(self.next_frame+self.frame_period, time.monotonic())
                if self.should_stop():
                    return False, None
                if self.interrupted:
                    self.log('[source] Connected. Monitoring resumed.', flush=True)
                self.interrupted = False
                return True, frame
            self.interrupted = True
            self.discontinuity = True
            if self.is_file:
                if not self.loop_video:
                    return False, None
                self.log('[source] Video ended. Replaying until Stop.', flush=True)
                # Reopen rather than relying on codec-specific seek behavior.
                self.close()
                self._wait(.1)
            else:
                self.log('[source] Camera/stream unavailable. Reconnecting in 2 seconds; use Stop to end.', flush=True)
                self.close()
                self._wait(2)
        return False, None

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
