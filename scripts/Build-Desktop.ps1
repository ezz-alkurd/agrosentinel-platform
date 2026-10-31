param([string]$Python,[switch]$UiOnly)
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
if(!$Python){$Python=Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'}
$out=Join-Path $repo 'artifacts\AgroSentinel-Windows'
$env:YOLO_CONFIG_DIR=Join-Path $repo 'runtime\packaging-ultralytics'
$env:PYINSTALLER_CONFIG_DIR=Join-Path $repo 'runtime\pyinstaller-cache'
Push-Location $repo
try {
 & dotnet publish desktop/AgroSentinel.Desktop/AgroSentinel.Desktop.csproj -c Release -o (Join-Path $out 'app') -p:UseAppHost=false -p:NuGetAudit=false -m:1 -nr:false
 if($LASTEXITCODE -ne 0){throw 'Desktop publish failed.'}
 if(!$UiOnly){
  & $Python -m PyInstaller --version
  if($LASTEXITCODE -ne 0){throw 'Install PyInstaller in the selected Python environment first.'}
  $stage=Join-Path $repo ('runtime\desktop-build-'+[Guid]::NewGuid().ToString('N'))
  & $Python -m PyInstaller scripts/AgroSentinel.Worker.spec --distpath (Join-Path $stage 'dist') --workpath (Join-Path $stage 'build')
  if($LASTEXITCODE -ne 0){throw 'Worker packaging failed.'}
  & $Python scripts/package_windows_app.py (Join-Path $stage 'dist\AgroSentinel.Worker')
 } else { & $Python scripts/package_windows_app.py }
 if($LASTEXITCODE -ne 0){throw 'Runtime/model packaging failed.'}
 $compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
 & $compiler /nologo /target:winexe /reference:System.Windows.Forms.dll ('/win32icon:'+ (Join-Path $repo 'presentation-web\wwwroot\favicon.ico')) ('/out:'+ (Join-Path $out 'AgroSentinel.exe')) (Join-Path $repo 'desktop\Bootstrapper.cs')
 if($LASTEXITCODE -ne 0){throw 'Launcher compilation failed.'}
 if(!$UiOnly){& (Join-Path $out 'worker\AgroSentinel.Worker.exe') --help; if($LASTEXITCODE -ne 0){throw 'Packaged worker could not start.'}}
 Write-Host ('Windows application: '+(Join-Path $out 'AgroSentinel.exe'))
} finally {Pop-Location}
