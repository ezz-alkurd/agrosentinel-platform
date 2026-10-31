param([switch]$LocalDebug,[string]$Flutter)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$app = Join-Path $repo 'app'
if (!$Flutter) {
    $installed = Get-Command flutter -ErrorAction SilentlyContinue
    if ($installed) { $Flutter = $installed.Source }
    else {
        $properties = Join-Path $app 'android/local.properties'
        if (Test-Path -LiteralPath $properties) {
            $setting = Get-Content -LiteralPath $properties | Where-Object { $_ -match '^flutter\.sdk=' } | Select-Object -First 1
            if ($setting) { $Flutter = Join-Path (($setting -replace '^flutter\.sdk=', '').Replace('\\', '\').Replace('\:', ':')) 'bin/flutter.bat' }
        }
    }
}
if (!$Flutter -or !(Test-Path -LiteralPath $Flutter)) { throw 'Flutter SDK not found. Run with -Flutter followed by the full path to flutter.bat.' }
$model = Join-Path $app 'assets/models/tomato_closeup.onnx'
$metadataPath = Join-Path $app 'assets/models/tomato_closeup.json'
if (!(Test-Path -LiteralPath $model)) {
    throw 'Bundled model missing. Restore app/assets/models/tomato_closeup.onnx or run training/export_mobile_model.py from the full project.'
}
$metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $model -Algorithm SHA256).Hash.ToLowerInvariant() -ne $metadata.sha256) {
    throw 'Bundled model checksum does not match its metadata. Re-export both files together.'
}
foreach ($config in @('lib/firebase_options.dart', 'android/app/google-services.json')) {
    if (!(Test-Path -LiteralPath (Join-Path $app $config))) {
        throw "Missing Firebase client configuration: $config. Run flutterfire configure for the intended project. Never use an admin service-account key in the app."
    }
}
Push-Location $app
try {
    & $Flutter pub get
    if ($LASTEXITCODE -ne 0) { throw 'Dependency restore failed.' }
    & $Flutter analyze --no-fatal-infos
    if ($LASTEXITCODE -ne 0) { throw 'Mobile analyzer failed.' }
    $reports = Join-Path $repo 'artifacts'
    New-Item -ItemType Directory -Force -Path $reports | Out-Null
    $testReport = Join-Path $reports 'mobile-tests.jsonl'
    & $Flutter test --reporter expanded --file-reporter ("json:"+$testReport)
    if ($LASTEXITCODE -ne 0) {
        if (Test-Path -LiteralPath $testReport) {
            Get-Content -LiteralPath $testReport | ForEach-Object {
                try {
                    $testEvent = $_ | ConvertFrom-Json
                    if ($testEvent.type -eq 'error') { Write-Host $testEvent.error }
                } catch { }
            }
        }
        throw "Mobile tests failed. Full results: $testReport"
    }
    $build = @('build', 'apk')
    if ($LocalDebug) { $build += '--debug' } else { $build += '--release' }
    & $Flutter @build
    if ($LASTEXITCODE -ne 0) { throw 'APK build failed.' }
    if (!$LocalDebug) {
        $mapping = Join-Path $app 'build/app/outputs/mapping/release/mapping.txt'
        $ortTypes = @(Select-String -LiteralPath $mapping -Pattern '^ai\.onnxruntime\.[^ ]+ -> ')
        if ($ortTypes.Count -eq 0) { throw 'Could not verify ONNX Runtime release class names.' }
        foreach ($entry in $ortTypes) {
            # R8-generated lambda helpers are not JNI entry points.
            if ($entry.Line -match '\$\$ExternalSynthetic') { continue }
            if ($entry.Line -match '^(.*?) -> (.*):$' -and $Matches[1] -ne $Matches[2]) {
                throw 'R8 renamed a native ONNX Runtime class. Check android/app/proguard-rules.pro.'
            }
        }
    }
    $flavor = if ($LocalDebug) { 'debug' } else { 'release' }
    $apk = Join-Path $app "build/app/outputs/flutter-apk/app-$flavor.apk"
    $artifacts = Join-Path $repo 'artifacts'
    New-Item -ItemType Directory -Force -Path $artifacts | Out-Null
    Copy-Item -LiteralPath $apk -Destination (Join-Path $artifacts 'AgroSentinel.apk')
    Write-Host "APK: $(Join-Path $artifacts 'AgroSentinel.apk')"
    Write-Host 'Leaf inference is bundled and offline. Camera events use the preconfigured AgroSentinel website. Sign-in and one-time laptop pairing are required.'
} finally { Pop-Location }
