@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-DemoMobile.ps1"
if errorlevel 1 (
 echo.
 echo APK build failed. See the error above.
) else (
 echo.
 echo Ready: artifacts\AgroSentinel.apk
)
pause
