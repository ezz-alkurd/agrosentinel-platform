# AgroSentinel Windows installer

Build the portable Windows app first, then run:

```powershell
.\scripts\Build-WindowsInstaller.ps1
```

Output: `artifacts/AgroSentinel-Setup.exe`. Send this single file to a Windows x64 laptop. It contains the application, fire and tomato models, frozen Python worker and private .NET runtime. The hosted API URL is already configured in the client.

The setup installs for the current user in `%LOCALAPPDATA%\Programs\AgroSentinel`, creates Desktop/Start menu shortcuts and an Installed apps uninstall entry. It requires no administrator elevation. Account sign-in and one-time phone/laptop pairing are still required. No SQL password, server signing key or paired-device credential is included.

The setup verifies its embedded ZIP checksum, checks required files and extraction paths, extracts to a staging folder, and upgrades only a folder bearing its installation marker. Existing detection settings/outbox live separately in `%LOCALAPPDATA%\AgroSentinel`.

Automated checks: `--verify-payload REPORT` validates embedded contents; `--extract-test EMPTY_DIRECTORY REPORT` tests extraction without creating shortcuts or registry entries. Build/test results are in `runtime/installer-build`. Payload validation, extraction, critical file hash comparisons and private runtime startup were checked. An interactive install/uninstall on another laptop remains to be checked.

A complete offline installer is about 372 MB. A smaller online downloader would need a hosted download URL for this package.
