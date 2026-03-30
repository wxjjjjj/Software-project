$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Split-Path -Parent $scriptDir
$projectDir = Split-Path -Parent $backendDir
Set-Location $projectDir
python -m uvicorn backend.gateway.main:app --reload --port 8000
