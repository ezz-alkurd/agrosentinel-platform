param(
    [string]$Source = '0',
    [string]$Image,
    [switch]$FireOnly,
    [switch]$PlantOnly,
    [switch]$IncludePlant,
    [switch]$Headless,
    [switch]$VerifyOnly,
    [string]$FirebaseKeyPath,
    [string]$Python
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
if ($FireOnly -and $PlantOnly) { throw 'Choose either FireOnly or PlantOnly, or neither to run both.' }
if (-not $Python) {
    $Python = Join-Path $repo '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $Python)) { $Python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe' }
    if (-not (Test-Path -LiteralPath $Python)) { throw 'Pass -Python with the path to your Python interpreter.' }
}
if (-not $FirebaseKeyPath) { $FirebaseKeyPath = $env:FIREBASE_KEY_PATH }
if (-not $FirebaseKeyPath) { $FirebaseKeyPath = Join-Path $repo '.secrets\serviceAccountKey.json' }
if (-not (Test-Path -LiteralPath $FirebaseKeyPath)) { throw 'Pass -FirebaseKeyPath with the private service-account file.' }
$env:FIREBASE_KEY_PATH = (Resolve-Path -LiteralPath $FirebaseKeyPath).Path
$env:YOLO_CONFIG_DIR = Join-Path $repo 'runtime\ultralytics'
if ($VerifyOnly) {
    & $Python (Join-Path $repo 'ai-backend\verify_live_demo.py') --firebase
} else {
    $detectorArgs = @((Join-Path $repo 'ai-backend\run_detection.py'))
    if ($Image) { $detectorArgs += @('--image', (Resolve-Path -LiteralPath $Image).Path) }
    else { $detectorArgs += @('--source', $Source) }
    if ($FireOnly) { $detectorArgs += '--no-disease' }
    if ($PlantOnly) { $detectorArgs += '--no-fire' }
    if ($Headless) { $detectorArgs += '--headless' }
    Push-Location $repo
    try { & $Python @detectorArgs } finally { Pop-Location }
}
if ($LASTEXITCODE -ne 0) { throw 'Verification/detection failed. Review the messages above; phone delivery is not established.' }
