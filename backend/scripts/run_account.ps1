$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Split-Path -Parent $scriptDir
$projectDir = Split-Path -Parent $backendDir
$condaActivate = "D:\anaconda3\Scripts\activate.bat"

cmd.exe /D /C "call `"$condaActivate`" software && cd /d `"$projectDir`" && python -m uvicorn backend.account.account_domain:app --reload --port 8001"
