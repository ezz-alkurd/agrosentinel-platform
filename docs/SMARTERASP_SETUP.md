# AgroSentinel: SQL Server, website API and Windows app

Implemented 24 October 2026. Website/API compatibility fix on 25 October: target .NET 8 and select SDK 8 locally; desktop remains .NET 10. NuGet.org must be reachable for package restore. After package restore completed, the .NET 8 website/API Debug build and Release publish passed on 25 October with no compiler warnings or errors. artifacts/website-publish now contains a verified net8.0 runtime configuration and both application DLLs. Hosted SQL/API verification is still pending. Firebase Authentication stays in use. Camera events and evidence now use the ASP.NET API; the mobile app no longer reads Firestore or Firebase Storage.

## What is ready

- SQL schema: services/control-api/schema.sql. No sample records are inserted.
- ASP.NET Core 8 API integrated into the existing presentation website under /api/v1.
- Windows WPF camera console: desktop/AgroSentinel.Desktop. It runs the existing Python models and supports camera/video, single images, three model profiles, model selection, preview, Stop, protected pairing credentials and queued evidence retries.
- Flutter settings now include Server & paired devices. Events, in-app alerts, device presence, map data and event deletion call the new API. Offline leaf analysis remains independent.
- Paired devices have revocable credentials scoped to one owner. SQL credentials and media signing secrets belong only on the server. Pairing codes expire after 10 minutes and can be claimed once.
- JPEG evidence lives outside wwwroot in App_Data/evidence. Events store references and checksums. Download links expire after one hour.
- Failed uploads stay in the laptop's local outbox and retain their event ID on retry. Server retries are idempotent. Queue files contain evidence and metadata, not device tokens. The desktop protects its credential with Windows DPAPI for the current user.

## Create the hosted database

1. In your SmarterASP control panel, create a new SQL Server database for AgroSentinel. Record its server address, database name, SQL username and password privately.
2. Connect to that database using SQL Server Management Studio (SSMS), with the hosting connection details.
3. Open services/control-api/schema.sql, select the correct NEW database, and execute it. It creates AgroUsers, AgroDevices, AgroPairings, AgroEvents and AgroSchemaVersion. Existing Firebase data is neither removed nor automatically migrated.
4. Confirm the hosting plan's database quota, application upload allowance, outbound HTTPS access to Google's signing-certificate endpoint and .NET 8 support.

## Configure and publish the website/API

Run in PowerShell at the source repository root:

    .\scripts\Configure-Hosting.ps1 -WebsiteUrl 'https://YOUR-WEBSITE' -SqlServer 'YOUR-SQL-SERVER' -Database 'YOUR-DATABASE' -SqlUser 'YOUR-SQL-USER'

The script prompts privately for the password and writes .secrets/hosting/appsettings.Production.json. It generates a random media signing key and preserves it on subsequent configuration runs. Never put this file in wwwroot, Git, the desktop app or the APK.

Then:

    .\scripts\Publish-Website.ps1

Deploy artifacts/website-publish using your existing website deployment process. Copy the private appsettings.Production.json beside AgroSentinel.Presentation.dll on the server. Keep App_Data/evidence writable by the application and preserve it during future deployments. A one-GB application evidence cap is configured; agree a retention policy and backup the database and evidence directory together. Deleted events are tombstoned in SQL; their evidence is retained until the operator reviews retention. This is application evidence storage, not an unlimited file archive.

The public health endpoint is https://YOUR-WEBSITE/api/v1/health. It reports ok only when required configuration and the schema check succeed. The old public presentation pages remain present.

The connection string enables encryption and certificate validation. Use the host's documented SQL connection settings; a SQL certificate error requires checking those settings with the provider rather than silently disabling validation.

## Build and run the Windows application

The development build already compiled here is desktop/AgroSentinel.Desktop/bin/Debug/net10.0-windows/AgroSentinel.exe. Run it from that directory. On the development laptop it locates the repository and existing Python interpreter automatically. Uncheck Sync confirmed events to the server to review local inference before hosting is configured.

For the doctor distribution:

    .\scripts\Build-Desktop.ps1

This publishes the WPF application, packages the worker with PyInstaller, copies the selected checkpoint files with checksum verification, bundles the installed private .NET 10.0.12 runtime, and compiles a Windows launcher. Keep the complete artifacts/AgroSentinel-Windows directory together; start AgroSentinel.exe. The published application does not need VS Code. The private runtime assembly script currently targets the .NET version installed on this development computer. Packaging and a clean-machine run still need verification.

## Connect the phone and laptop

1. Build/install the updated Android app using scripts/Build-DemoMobile.ps1.
2. Sign into the phone, open Settings > Server & paired devices, enter the HTTPS website root, and Save & check server.
3. On Windows, enter the same root address and choose Pair with phone.
4. Enter that eight-character code on the phone and choose Pair laptop. The laptop then stores its revocable credential protected by Windows.
5. Start monitoring on Windows. Fire needs >=70% for two seconds; tomato disease needs the same non-healthy label at >=90% for two seconds. Tomato input must be one close-up tomato leaf; unrelated objects are not reliably rejected by that classifier.
6. Keep the phone app open on Events or Alerts; it refreshes every five seconds. Check actual evidence, label and capture provenance. Background push is not implemented.
7. Disconnect briefly, generate an eligible detection, then reconnect and use Retry queued uploads. Confirm the same event is stored once. Revoke the device on the phone and confirm subsequent uploads are rejected.

## Verification status

Completed before the environment change: ASP.NET website/API build passed with no warnings; WPF application build passed with no warnings; the existing 30 Python regression tests passed. New API security integration checks compile, but their HTTP run was blocked by this environment's loopback socket permissions. SQL LocalDB could not access its registry configuration, so no real SQL schema/application integration is claimed.

Additional Python outbox and Flutter API checks are provided but have not been executed. Flutter analysis/device verification, final Windows packaging, real hosted SQL, Firebase ID-token verification against live Google certificates, and an actual laptop-to-phone run are pending.

The execution environment subsequently rejected every shell launch because its Windows sandbox configuration contains an invalid file:///workspace entry. File edits continued through the file editor. Run the supplied build/check scripts in your normal terminal, or restore the task's Windows workspace permissions before asking the agent to finish those checks. No live deployment or hosting-account change has been performed.

## Checks to run from the repository

    dotnet run --project services/control-api/Tests/ApiChecks.csproj
    dotnet build desktop/AgroSentinel.Desktop/AgroSentinel.Desktop.csproj
    cd ai-backend
    python -m unittest test_live_demo test_combined_demo test_plant_api test_firebase_diagnostics test_api_transport
    cd ../app
    flutter pub get
    flutter analyze --no-fatal-infos
    flutter test

The API test process uses a test-only store and ephemeral RSA signing certificate. It verifies actual signature/audience/expiry enforcement, pairing, ownership, idempotency, evidence signatures and device revocation without creating cloud records. Production always registers SQL Server; it has no in-memory or fake-data fallback.


## Preconfigured clients (25 October 2026)

Both clients now default to https://ezzeldeenalkurd-001-site2.ftempurl.com. No server URL entry is needed for a fresh installation. Existing explicit server choices are retained. Sign-in and one-time laptop pairing remain required.

The portable Windows folder artifacts/AgroSentinel-Windows bundles the models, Python worker and private .NET runtime. Its runtime startup and frozen fire/plant image smoke test passed. All six outbox tests passed using a writable test directory. Live pairing/upload/phone review is still pending.

The new APK could not be built in the agent session: Dart exits with an access-denied path canonicalization error, including from a writable SDK copy. Run scripts/Build-ConfiguredApk.cmd in a normal Windows session; it discovers the SDK, runs checks and creates artifacts/AgroSentinel.apk after success. Older APKs have not been updated.
