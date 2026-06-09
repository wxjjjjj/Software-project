$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Split-Path -Parent $scriptDir
Set-Location $backendDir

if (!(Test-Path ".env") -and (Test-Path ".env.example")) {
  Copy-Item ".env.example" ".env"
  Write-Host "已创建 backend/.env（由 .env.example 复制）"
} else {
  Write-Host "backend/.env 已存在，跳过复制"
}

Write-Host "下一步："
Write-Host "1) 根据本机 MySQL 修改 backend/.env"
Write-Host "2) 执行: pip install -r requirements.txt"
Write-Host "3) 执行: ./scripts/run_services.ps1"
