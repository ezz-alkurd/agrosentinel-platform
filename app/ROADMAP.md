# AgroDrone AI — Full Completion Roadmap & Feature Suggestions

---

## Current State (as of now)

The app has a solid Clean Architecture foundation (BLoC/Cubit + GoRouter + DI) with the following screens scaffolded: Login, Signup, Home, Live Map, AI Diagnostic, Notifications, and Settings. The UI now supports 5 switchable color themes with smooth animations.

---

## Phase 1 — Backend & Authentication (2–3 weeks)

### 1.1 Real Authentication
- Replace the mock `AuthRemoteDataSource` with a real call to your backend (Firebase Auth, Supabase, or a custom REST API).
- Add JWT token storage using `flutter_secure_storage`.
- Implement auto-login on app start (check stored token → emit `AuthAuthenticated`).
- Add a forgot-password flow with email OTP verification.
- Add biometric login (fingerprint / Face ID) via the `local_auth` package.

### 1.2 User Profile
- Create a profile page showing the farmer's name, farm name, total scans, and alert history.
- Allow the user to edit their name, farm name, and profile picture (stored in Firebase Storage or AWS S3).

---

## Phase 2 — Drone Integration (3–4 weeks)

### 2.1 Real-time Drone Telemetry
- Connect to a drone SDK (DJI Mobile SDK, Parrot ARSDK, or a custom MAVLink-over-WebSocket bridge).
- Replace the mock `DroneStatusModel` with live telemetry: GPS coordinates, battery, altitude, speed, camera gimbal angle, and flight mode.
- Use a WebSocket stream so the `HomeState` updates in real time without polling.

### 2.2 Drone Control Panel
- Build a dedicated `DroneControlPage` with:
  - Takeoff / Land / Return-to-Home buttons.
  - Altitude and speed sliders.
  - Emergency stop button (always visible, colored red).
  - Pre-flight checklist modal before first takeoff.

### 2.3 Flight Planning
- Allow the user to draw a polygon on the map defining the area to scan.
- Auto-generate a lawnmower flight path and calculate estimated battery usage.
- Save and re-use flight plans.

---

## Phase 3 — Live Map (2–3 weeks)

### 3.1 Real Map Integration
- Replace the placeholder `MapPage` with `flutter_map` (OpenStreetMap tiles) or Google Maps.
- Show the drone as a moving marker using the real-time GPS stream.
- Plot detected anomaly markers (fire, disease) as color-coded pins.

### 3.2 Field Layers
- Overlay NDVI (vegetation health) heat-map tiles fetched from a satellite API (e.g., Sentinel Hub or Planet).
- Toggle-able layers: NDVI, thermal, RGB, alerts.

### 3.3 Geo-fencing
- Let the user draw a field boundary.
- Trigger an alert if the drone exits the boundary.

---

## Phase 4 — AI Diagnostic (3–4 weeks)

### 4.1 Real Model Integration
- Train or fine-tune a PyTorch / TensorFlow Lite model on plant disease datasets (PlantVillage, etc.).
- Export to `.tflite` and load via the `tflite_flutter` package for on-device inference.
- Fall back to a REST API (FastAPI or Flask) when the device has low RAM.

### 4.2 Diagnosis History
- Store every scan result in local SQLite (via `drift`) with the image thumbnail, date, detected disease, confidence score, and treatment recommendation.
- Build a history list/timeline so the farmer can track crop health over time.

### 4.3 Disease Knowledge Base
- Embed a searchable database of 50+ common crop diseases with images, symptoms, causes, and treatment steps.
- Link every diagnosis result directly to the relevant knowledge base entry.

---

## Phase 5 — Notifications & Alerts (1–2 weeks)

### 5.1 Push Notifications
- Integrate Firebase Cloud Messaging (FCM).
- Send a push when the drone detects fire (high urgency) or disease (medium urgency) automatically from the server or onboard processing.
- Show a rich notification with the field name and thumbnail image.

### 5.2 In-app Alert Detail
- Each notification card should be tappable, opening a detail screen with the exact GPS location, image evidence, confidence score, and suggested action.

### 5.3 Alert Rules
- Let the user configure thresholds: battery % for low-battery alert, wind speed, temperature, etc.

---

## Phase 6 — Reports & Analytics (2–3 weeks)

### 6.1 Field Health Dashboard
- A chart page (using `fl_chart`) showing:
  - Disease detections over time (line chart).
  - Battery usage per flight (bar chart).
  - NDVI trend over weeks (area chart).

### 6.2 PDF Export
- Generate a professional PDF report per field / per month using the `pdf` Flutter package.
- Include a map snapshot, health trend charts, and a table of all detected issues.

### 6.3 Season Summary
- Auto-generate a season summary at the end of each month — total area covered, total anomalies, average crop health score.

---

## Phase 7 — Polish & Release (2 weeks)

### 7.1 Performance
- Implement image caching (using `cached_network_image`).
- Add pagination to Notifications and Diagnosis History lists.
- Run `flutter analyze` and `flutter test` to clean up any lint and cover critical paths.

### 7.2 Offline Mode
- Cache the last drone status and NDVI map tiles locally so the farmer can review data without internet.

### 7.3 Localization
- Complete Arabic translation (all strings currently in code should go through `AppL10n`).
- Add Kurdish (`ku`) as a third language if your target users include Kurdistan region farmers.

### 7.4 App Store Release
- Set up Fastlane for automated Android (Play Store) and iOS (App Store) deployment.
- Write a privacy policy and terms of service page (required by both stores).
- Target Android API 34+ and iOS 16+.

---

## Suggested New Features

### 🌡️ Weather Integration
Pull real-time weather from OpenWeatherMap or AccuWeather — temperature, humidity, wind speed, UV index, and rain forecast. Show a "safe to fly" indicator based on these conditions. Display a 7-day forecast mini-widget on the Home screen.

### 🐛 Pest Detection (separate AI model)
Train a dedicated model to detect insects (aphids, whiteflies, locusts) from close-up photos. Show a pest risk level for the field based on detected species and environmental conditions.

### 💧 Irrigation Recommendation
Based on NDVI data, soil moisture sensors (if connected), and weather forecast, recommend which sections of the field need irrigation today. Integrate with smart irrigation controllers via a REST API.

### 📡 Multi-Drone Support
Allow the user to manage a fleet of drones. Show all drones on the map simultaneously with distinct color-coded markers. Add a fleet status panel showing each drone's battery, location, and task.

### 🤖 AI Chat Assistant
Embed a lightweight chat interface powered by a small language model (or your backend API wrapping GPT-4o). The farmer can ask natural language questions like "What disease was detected most this month?" or "Is it safe to fly tomorrow?".

### 🌾 Crop Calendar
A seasonal planting calendar that reminds the farmer when to plant, fertilize, spray, and harvest based on the crop type and region. Integrate with the diagnosis history to correlate disease patterns with crop lifecycle stages.

### 📸 Drone Camera Live Feed
Stream the drone's camera feed (RTSP → HLS) directly into the app using `flutter_vlc_player` or `video_player`. Let the user zoom in, take a screenshot, and immediately run AI diagnosis on the snapshot.

### 🔋 Battery & Maintenance Tracker
Log each drone's total flight hours, battery charge cycles, propeller wear, and firmware version. Notify the farmer when a component needs replacement based on usage thresholds.

### 👥 Team / Multi-User Farms
Allow multiple users (e.g., farm owner + agronomist + field worker) to share the same farm account with role-based access control — the owner can see everything, the field worker can only trigger scans.

### 📊 Yield Prediction
Use historical NDVI data, diagnosis history, and weather trends to predict the harvest yield percentage relative to an ideal crop. Display a yield forecast card on the Home screen updated weekly.

### 🛒 Marketplace / Treatment Store
Show nearby agricultural suppliers for the recommended treatment after each disease diagnosis. Include product name, price range, and a map of the nearest stockist.

---

## Tech Stack Recommendations

| Layer | Current | Recommended Addition |
|---|---|---|
| Auth | Mock | Firebase Auth + `flutter_secure_storage` |
| Database | None | `drift` (SQLite) for local, Supabase / Firebase Firestore for cloud |
| Drone SDK | Mock | DJI Mobile SDK (Android/iOS) or MAVLink via WebSocket |
| AI Model | Mock | TFLite on-device + FastAPI fallback |
| Maps | Placeholder | `flutter_map` with OpenStreetMap tiles |
| Charts | None | `fl_chart` |
| Push | None | Firebase Cloud Messaging |
| PDF | None | `pdf` + `printing` packages |
| State Mgmt | BLoC/Cubit ✅ | Keep — it's already clean |
| CI/CD | None | GitHub Actions + Fastlane |

---

*Generated for the AgroDrone AI graduation project — Ezzeldeen, 2026*
