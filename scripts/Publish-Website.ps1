$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
$out=Join-Path $repo 'artifacts\website-publish'
Push-Location (Join-Path $repo 'presentation-web')
try {
 & dotnet publish 'AgroSentinel.Presentation.csproj' -c Release -o $out
 if($LASTEXITCODE -ne 0){throw 'Website/API publish failed.'}
} finally { Pop-Location }
New-Item -ItemType Directory -Force -Path (Join-Path $out 'database') | Out-Null
Copy-Item -LiteralPath (Join-Path $repo 'services\control-api\schema.sql') -Destination (Join-Path $out 'database\schema.sql')
Write-Host 'Website/API published. Add the private appsettings.Production.json separately, then deploy this folder. Preserve App_Data/evidence on updates.'
