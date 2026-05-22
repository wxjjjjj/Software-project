# Start all backend services through the local conda environment.
# account: 8001
# ride: 8002
# ops: 8003
# gateway: 8000

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Split-Path -Parent $scriptDir
$projectDir = Split-Path -Parent $backendDir
$condaActivate = "D:\anaconda3\Scripts\activate.bat"
$condaEnv = "software"

function Start-ServiceWindow($module, $port) {
  $command = "call `"$condaActivate`" $condaEnv && cd /d `"$projectDir`" && python -m uvicorn $module --reload --port $port"
  Start-Process cmd.exe -ArgumentList "/D", "/K", $command
}

Start-ServiceWindow "backend.account.account_domain:app" 8001
Start-ServiceWindow "backend.ride.service:app" 8002
Start-ServiceWindow "backend.ops.service:app" 8003
Start-ServiceWindow "backend.gateway.main:app" 8000
