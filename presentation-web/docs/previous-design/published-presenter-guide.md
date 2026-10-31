# AgroSentinel — presenter guide

## Before the audience arrives

1. Open the website and test both project films, including audio.
2. Click Present project. Use the arrow buttons or keyboard; N shows speaker notes, F toggles full screen, Esc returns to the normal website.
3. Rehearse the separate Python detector and Flutter application. The website does not run inference.
4. Confirm the intended models load; verify camera access and the phone's configured backend.
5. Generate one real event and check that its evidence image arrives in the mobile app.
6. Use known supported examples. Recorded sources must be identified as recorded.
7. Confirm which location source is being displayed. IP geolocation is approximate and is not drone GPS.
8. Disable laptop sleep during the presentation and keep the charger connected.

## Suggested narrative

1. The big picture: AgroSentinel connects aerial observation, ground robotics and image analysis.
2. The vision: plant conditions, visible fire/smoke and future sensor context.
3. The platforms: drone for a wider view; rover for close observation and planned soil sensing.
4. The models: separate close-up, far-image and fire/smoke roles. Old demo weights are not newly trained releases.
5. The pipeline: capture → analyze → confirm/save → mobile review. Click each stage for its explanation.
6. The films: select the drone or rover video. These are project/concept films.
7. The live demonstration: use the actual laptop detector, then show the actual event on the phone.
8. Credit the team and supervisors.

## Live demonstration sequence

- Start the prepared detector using the configured camera or a clearly identified recorded clip.
- Show a supported scene and explain the actual output. Do not stage a real fire.
- Explain confidence gating and temporal confirmation. The reviewed script uses a 2-second window and a cooldown; thresholds need rehearsal on the selected examples.
- After the event is uploaded, show the real entry, image and timestamp on the phone.
- If nothing arrives, check the detector logs, model threshold, connection, Firebase storage/event write, then the phone.
- If the live flow fails, describe the observed failure honestly; use the project films to continue explaining the concept.

## What can be stated accurately

The workspace contains a Flutter application, a Python/Firebase demo pipeline, saved legacy weights, and the presentation website. Existing app code reads events and device presence from Firebase. Phone diagnosis currently targets a configurable laptop API until cloud hosting is implemented.

The target architecture uses ASP.NET/SmarterASP, a separate Python model host, Firebase services and a camera/Jetson agent. Deployment is not established by this presentation.

## What still requires separate evidence

- Fresh close-up and distant/aerial plant model releases.
- Dina's updated fire-model release and evaluation.
- A deployed public model API tested using phone mobile data.
- Actual rover sensors, calibration, movement controls and telemetry.
- Autonomous drone navigation and hardware-specific feed access.
- Actual Jetson Nano compatibility/performance.
- Background push notification delivery.

Do not quote a model accuracy, alert latency, exact drone location or vehicle capability that has not been measured.

## Files for the host

Upload the contents of publish/ to the SmarterASP site root. Start-Website.ps1 provides a local laptop backup when the ASP.NET Core 8 runtime is installed.
