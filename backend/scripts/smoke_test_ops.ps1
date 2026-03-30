param(
  [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
  param(
    [string]$Name,
    [string]$Method,
    [string]$Url,
    [hashtable]$Body
  )

  Write-Host "`n=== $Name ===" -ForegroundColor Cyan
  try {
    if ($Body) {
      $json = $Body | ConvertTo-Json -Depth 5
      $resp = Invoke-RestMethod -Method $Method -Uri $Url -ContentType "application/json" -Body $json
    } else {
      $resp = Invoke-RestMethod -Method $Method -Uri $Url
    }
    $resp | ConvertTo-Json -Depth 8
  } catch {
    Write-Host "FAILED: $Name" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
  }
}

Write-Host "开始运营域接口自测，网关地址: $BaseUrl" -ForegroundColor Green
Write-Host "请确保四个服务已启动（8000/8001/8002/8003）。" -ForegroundColor DarkYellow

Invoke-Step -Name "健康检查" -Method "GET" -Url "$BaseUrl/api/health"

Invoke-Step -Name "订单支付" -Method "POST" -Url "$BaseUrl/api/payments/orders/10001/pay" -Body @{
  payerUserId = 1001
  amount = 35.5
}

Invoke-Step -Name "钱包信息" -Method "GET" -Url "$BaseUrl/api/wallet/me"

Invoke-Step -Name "钱包提现" -Method "POST" -Url "$BaseUrl/api/wallet/withdraw" -Body @{
  ownerUserId = 20001
  amount = 20.0
}

Invoke-Step -Name "提交反馈" -Method "POST" -Url "$BaseUrl/api/feedback" -Body @{
  userId = 1001
  orderId = 10001
  content = "联调脚本自动提交反馈"
}

Invoke-Step -Name "管理员用户列表" -Method "GET" -Url "$BaseUrl/api/admin/users"
Invoke-Step -Name "管理员订单列表" -Method "GET" -Url "$BaseUrl/api/admin/orders"
Invoke-Step -Name "管理员反馈列表" -Method "GET" -Url "$BaseUrl/api/admin/feedback"

Write-Host "`n运营域自测结束。" -ForegroundColor Green
