# 启动三个领域服务 + 网关
# 账号域: 8001
# 订单车辆域: 8002
# 交易运营域: 8003
# 网关: 8000


$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Split-Path -Parent $scriptDir
$projectDir = Split-Path -Parent $backendDir

Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$projectDir'; python -m uvicorn backend.account.service:app --reload --port 8001"
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$projectDir'; python -m uvicorn backend.ride.service:app --reload --port 8002"
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$projectDir'; python -m uvicorn backend.ops.service:app --reload --port 8003"
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$projectDir'; python -m uvicorn backend.gateway.main:app --reload --port 8000"
