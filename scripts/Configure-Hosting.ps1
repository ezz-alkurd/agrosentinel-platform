param([Parameter(Mandatory)][string]$WebsiteUrl,[Parameter(Mandatory)][string]$SqlServer,[Parameter(Mandatory)][string]$Database,[Parameter(Mandatory)][string]$SqlUser,[Security.SecureString]$SqlPassword)
$ErrorActionPreference='Stop'
$uri=[Uri]$WebsiteUrl
if($uri.Scheme -ne 'https' -or $uri.UserInfo -or $uri.Query -or $uri.Fragment){throw 'Enter the HTTPS website root address.'}
if(!$SqlPassword){$SqlPassword=Read-Host 'SQL password (saved only in the private server configuration)' -AsSecureString}
$repo=Split-Path $PSScriptRoot -Parent
$folder=Join-Path $repo '.secrets\hosting'
New-Item -ItemType Directory -Force -Path $folder | Out-Null
$settings=Join-Path $folder 'appsettings.Production.json'
$pointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($SqlPassword)
try {
 $connection=[System.Data.Common.DbConnectionStringBuilder]::new()
 $connection['Server']=$SqlServer;$connection['Database']=$Database;$connection['User ID']=$SqlUser
 $connection['Password']=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
 $connection['Encrypt']='True';$connection['TrustServerCertificate']='False';$connection['Connect Timeout']='10'
 $key=$null;if(Test-Path -LiteralPath $settings){$key=(Get-Content -LiteralPath $settings -Raw | ConvertFrom-Json).AgroSentinel.MediaSigningKey}
 if(!$key){$bytes=[byte[]]::new(32);$rng=[Security.Cryptography.RandomNumberGenerator]::Create();$rng.GetBytes($bytes);$rng.Dispose();$key=[Convert]::ToBase64String($bytes)}
 $body=@{ConnectionStrings=@{AgroSentinel=$connection.ConnectionString};AgroSentinel=@{FirebaseProjectId='agriculture-drone-e0dc0';PublicBaseUrl=$WebsiteUrl.TrimEnd('/');MediaSigningKey=$key;EvidenceDirectory='App_Data/evidence';MaxEvidenceStorageBytes=1073741824}}
 $body | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $settings -Encoding utf8
 Write-Host 'Private server configuration saved. Copy it beside the published website DLL on the host. Do not put it in wwwroot or the mobile/desktop app.'
} finally {[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)}
