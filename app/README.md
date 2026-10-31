# AgroDrone AI

AI-Powered Autonomous Drone for Smart Agriculture — Flutter mobile app.

This project is the merged "best of" of the two earlier prototypes
(`agri_drone_ai/` and `gproject/`):

- **Architecture:** Clean Architecture (data / domain / presentation) with
  BLoC + Cubit, GoRouter, GetIt for DI, Dio for networking.
- **Features:** Authentication, Home dashboard, Live Map (placeholder),
  AI plant diagnostic (image picker), Notifications, Settings (theme + i18n).
- **Localization:** English + Arabic (RTL) via a hand-rolled delegate.

> **Note:** Firebase and Google Maps SDK have been stripped so the app builds
> and runs out-of-the-box without API keys. The Map screen renders a stylized
> placeholder showing markers + flight path on a synthetic grid; replace
> `lib/features/map/presentation/pages/map_page.dart` with a real
> `google_maps_flutter` implementation when you wire up an API key.

## Run

```bash
flutter pub get
flutter run
```

Tested with Flutter 3.x / Dart 3.x on Android.

## Project structure

```
lib/
  app.dart                  ← MaterialApp.router root
  main.dart                 ← entry-point + DI bootstrap
  core/
    constants/              ← colors, dimensions
    di/                     ← GetIt setup
    errors/                 ← Failure types
    l10n/                   ← English + Arabic strings
    network/                ← ApiClient (Dio wrapper)
    router/                 ← GoRouter config
    theme/                  ← dark + light theme
    utils/                  ← extensions
  features/
    auth/                   ← login + signup
    home/                   ← drone status dashboard
    map/                    ← live map (placeholder)
    notifications/          ← realtime alerts
    ai_diagnostic/          ← image upload + analysis
    settings/               ← theme + language
    shell/                  ← bottom-nav scaffold
```

## Re-enabling Google Maps later

1. Add `google_maps_flutter: ^2.5.3` back to `pubspec.yaml`.
2. Add the API-key meta-data tag back to `android/app/src/main/AndroidManifest.xml`.
3. Replace `lib/features/map/presentation/pages/map_page.dart` with a `GoogleMap`
   widget — the `MapMarkerEntity` already exposes `latitude`/`longitude`.
