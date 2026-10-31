# Apps 1.0.1

The Android tomato runtime now preserves all ONNX Runtime Java classes and
members during R8 shrinking. The previous release mapping renamed TensorInfo,
which native JNI code accesses by name. Native runtime errors are logged with
the AgroSentinelPlant tag. Photo selection/preview is bounded to reduce memory
use and lost photo selection is recovered after Android activity recreation.

Authentication waits for Firebase's initial restored-user event. The router
shows a startup screen until that check completes. Only explicit Logout signs
out. Appearance defaults to dark; text size and contrast are increased.

Windows monitoring runs server presence updates on a bounded background worker.
Camera/stream read failures reconnect; recorded files can loop at their recorded
rate until stopped. Source interruptions reset confirmation continuity while
preserving the 30-second alert cooldown. Preview write failures do not terminate
inference. Uploads remain durable and retry while the connection recovers.

The desktop adds Monitor/Connection tabs, File/Monitor/Help menus, preferences,
a session timer, exportable timestamped activity and keyboard shortcuts.

Validation: 12 Python monitoring/outbox tests; 15 Flutter tests; desktop Release
publish; real packaged inference and repeated-video checks with a local server
returning 503. The packaged loop test survived three failed heartbeats and four
video replays, then exited 0 only after the stop signal. Installer verification
checks payload integrity, required files and safe extraction paths.

Files: artifacts/AgroSentinel-Setup.exe and artifacts/AgroSentinel.apk.
No API/website deployment is required for these app-only changes. Actual leaf
inference on the affected phone and long hardware-camera sessions still require
on-device confirmation; simulated checks are not a hardware or accuracy test.

Android release assembly succeeded. Lint analysis ran, but its text-report writer
was excluded in this restricted session because Java reports the output directory
as non-writable even though a direct write succeeds. The normal build script
keeps the standard release lint checks. JNI class names and bundled ONNX hash
were verified separately against the actual release APK.
