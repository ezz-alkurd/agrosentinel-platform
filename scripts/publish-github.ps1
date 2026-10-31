param(
    [string]$Repository = 'agrosentinel-platform',
    [string[]]$Collaborators = @()
)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $repoRoot
$env:GIT_CONFIG_COUNT = '1'
$env:GIT_CONFIG_KEY_0 = 'safe.directory'
$env:GIT_CONFIG_VALUE_0 = $repoRoot
if ($Repository -notmatch '^[A-Za-z0-9_.-]+$') { throw 'Use a repository name without owner or shell characters.' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI is not installed. Install it and authenticate with gh auth login, then rerun.' }
& gh auth status
if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI authentication is required.' }
$login = (& gh api user --jq '.login').Trim()
if ($LASTEXITCODE -ne 0 -or $login -ne 'ezz-alkurd') { throw 'Expected the verified ezz-alkurd account.' }
if ($Collaborators.Count -ne 0 -and $Collaborators.Count -ne 4) { throw 'Supply all four verified teammate handles, or omit invitations.' }
foreach ($handle in $Collaborators) {
    if ($handle -notmatch '^[A-Za-z0-9][A-Za-z0-9-]{0,38}$' -or $handle -eq $login) { throw 'Invalid teammate handle.' }
    & gh api "users/$handle" --silent
    if ($LASTEXITCODE -ne 0) { throw "Account could not be verified: $handle" }
}
if (@($Collaborators | Select-Object -Unique).Count -ne $Collaborators.Count) { throw 'Duplicate collaborator handles.' }
$existingOrigin = & git remote get-url origin 2>$null
if ($existingOrigin) { throw 'Origin already exists; refusing to replace it or create a duplicate repository.' }
& gh repo create $Repository --private --source $repoRoot --remote origin --push --description 'Camera-based agricultural monitoring: close-up and distant plant models, fire detection, cloud and Jetson integration.'
if ($LASTEXITCODE -ne 0) { throw 'Repository creation/push failed; inspect GitHub before retrying.' }
foreach ($handle in $Collaborators) {
    & gh api --method PUT "repos/$login/$Repository/collaborators/$handle" -f permission=push --silent
    if ($LASTEXITCODE -ne 0) { throw "Repository created, but invitation failed for $handle." }
}
Write-Output "Private repository published: https://github.com/$login/$Repository"
if ($Collaborators.Count) { Write-Output 'Collaborator invitations requested; teammates must accept them.' }
