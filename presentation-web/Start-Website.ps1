param([int]$Port = 5168)
$ErrorActionPreference = 'Stop'
$siteRoot = $PSScriptRoot
$dll = Join-Path $siteRoot 'AgroSentinel.Presentation.dll'
if (-not (Test-Path -LiteralPath $dll)) {
    throw 'Run this script from the published website folder. See README.md for the source build command.'
}
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw 'Install the Microsoft ASP.NET Core 8 runtime before starting this website.'
}
$siteUrl = "http://127.0.0.1:$Port"
try {
    $health = Invoke-RestMethod "$siteUrl/health" -TimeoutSec 2
    if ($health.service -eq 'AgroSentinel presentation') {
        Start-Process $siteUrl
        exit 0
    }
    throw 'The selected port is already used by another application.'
} catch {
    if ($_.Exception.Message -eq 'The selected port is already used by another application.') { throw }
}
$logFolder = Join-Path ([IO.Path]::GetTempPath()) 'AgroSentinel-Presentation'
New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
$server = Start-Process -FilePath 'dotnet' -ArgumentList @('AgroSentinel.Presentation.dll', '--urls', $siteUrl) -WorkingDirectory $siteRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logFolder 'website.log') -RedirectStandardError (Join-Path $logFolder 'website-errors.log') -PassThru
$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if ($server.HasExited) { throw "Website stopped. See $logFolder for its logs." }
    try {
        $health = Invoke-RestMethod "$siteUrl/health" -TimeoutSec 2
        if ($health.service -eq 'AgroSentinel presentation') { $ready = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 500
}
if (-not $ready) { throw "Website did not respond. See $logFolder for its logs." }
Start-Process $siteUrl
Write-Host "AgroSentinel is open at $siteUrl"
Write-Host "Website process ID: $($server.Id). Close it after the presentation with Stop-Process -Id $($server.Id)."
