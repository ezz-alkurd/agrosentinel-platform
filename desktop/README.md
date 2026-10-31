# AgroSentinel Windows console

WPF .NET 10 application around the existing Python detection engine. Development executable: AgroSentinel.Desktop/bin/Debug/net10.0-windows/AgroSentinel.exe.

Run scripts/Build-Desktop.ps1 from the repository root to create a complete portable distribution with a private runtime, worker and selected models. This final packaging step has not been verified in the current environment. See docs/SMARTERASP_SETUP.md for server provisioning, pairing, local preview and verification status.


Client default (25 October 2026): both the Windows console and Flutter app use https://ezzeldeenalkurd-001-site2.ftempurl.com automatically. Signing in and pairing the laptop once are still required; the server URL does not need to be entered. Existing explicitly saved server selections are retained. The private SQL connection string and signing key remain on the website only.
