param([string]$Python)
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
if(!$Python){$Python=Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'}
$work=Join-Path $repo 'runtime\installer-build'
New-Item -ItemType Directory -Force -Path $work | Out-Null
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$source=Join-Path $repo 'desktop\Installer\Setup.cs'
$common=@('/nologo','/target:winexe','/platform:x64','/optimize+','/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.IO.Compression.dll','/reference:System.IO.Compression.FileSystem.dll','/reference:Microsoft.CSharp.dll',('/win32icon:'+(Join-Path $repo 'presentation-web\wwwroot\favicon.ico')),('/win32manifest:'+(Join-Path $repo 'desktop\Installer\setup.manifest')))
& $compiler @common ('/out:'+(Join-Path $work 'Uninstall.exe')) $source
if($LASTEXITCODE -ne 0){throw 'Uninstaller compilation failed.'}
& $Python (Join-Path $repo 'scripts\package_windows_installer.py')
if($LASTEXITCODE -ne 0){throw 'Installer payload build failed.'}
$output=Join-Path $repo 'artifacts\AgroSentinel-Setup.exe'
& $compiler @common '/define:INSTALLER' ('/resource:'+(Join-Path $work 'payload.zip')+',AgroSentinel.Payload.zip') ('/out:'+$output) $source (Join-Path $work 'ReleaseInfo.cs')
if($LASTEXITCODE -ne 0){throw 'Setup compilation failed.'}
$report=Join-Path $work 'verify.txt'
$verification=Start-Process -FilePath $output -ArgumentList @('--verify-payload',('"'+$report+'"')) -WindowStyle Hidden -Wait -PassThru
if($verification.ExitCode -ne 0){throw 'Embedded installer validation failed.'}
Get-Content -LiteralPath $report
Write-Host ('Installer ready: '+$output)
