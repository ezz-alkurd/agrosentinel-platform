param([string]$Python)
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
$venv=Join-Path $repo '.venv'
if ($Python) { & $Python -m venv $venv }
elseif (Get-Command py -ErrorAction SilentlyContinue) { & py -3.11 -m venv $venv }
else { throw 'Install Python 3.11 (64-bit), then rerun setup, or pass -Python with its full path.' }
if ($LASTEXITCODE -ne 0) { throw 'Could not create Python 3.11 environment.' }
$runtime=Join-Path $venv 'Scripts\python.exe'
& $runtime -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip setup failed. Check internet access.' }
& $runtime -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw 'CPU model runtime installation failed.' }
& $runtime -m pip install -r (Join-Path $repo 'ai-backend\requirements-doctor.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $runtime (Join-Path $repo 'ai-backend\verify_live_demo.py')
if ($LASTEXITCODE -ne 0) { throw 'Model verification failed.' }
Write-Host 'Setup complete. Start START_DEMO.cmd. Add the private credential separately before cloud verification.'
