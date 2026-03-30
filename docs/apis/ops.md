# 交易运营API
yzr

数据库: ops_db

功能范围: 支付、钱包、提现、反馈、管理端运营接口

## 集成环境
- 统一地址: http://<wxj主机>:8000
- 接口前缀: /api
- 约束规则: 钱包和支付流水仅由交易运营域维护

## 必需接口【仅一点点示例，根据自己的设计修改即可】

### 订单支付
- 方法: POST
- 路径: /api/payments/orders/{orderId}/pay
- 请求 JSON:
```json
{
  "payerUserId": 1001,
  "amount": 35.5
}
```
- 响应 JSON:
```json
{
  "message": "payment success",
  "orderId": 10001,
  "status": "PAID"
}
```
- 错误码:
  - 400: amount <= 0
  - 409: 该用户对该订单已支付
  - 500: ops_db连接或SQL异常

### 钱包信息查询
- 方法: GET
- 路径: /api/wallet/me
- 说明: 当前V1默认查询 ownerUserId=20001（后续接登录态再替换）
- 响应 JSON:
```json
{
  "balance": 512.5,
  "currency": "CNY"
}
```

- 错误码:
  - 500: ops_db连接或SQL异常

### 钱包提现
- 方法: POST
- 路径: /api/wallet/withdraw
- 请求 JSON:
```json
{
  "ownerUserId": 20001,
  "amount": 100.0
}
```
- 响应 JSON:
```json
{
  "message": "withdraw request accepted",
  "requestId": 7788
}
```
- 错误码:
  - 400: amount <= 0
  - 404: 钱包不存在
  - 409: 余额不足
  - 500: ops_db连接或SQL异常

- 事务约束:
  - 提现时同时更新 wallet_account.balance / frozen_amount
  - 同时写 withdraw_request 与 wallet_txn

### 提交反馈
- 方法: POST
- 路径: /api/feedback
- 请求 JSON:
```json
{
  "userId": 1001,
  "orderId": 10001,
  "content": "Driver arrived late"
}
```
- 响应 JSON:
```json
{
  "message": "feedback submitted",
  "feedbackId": 9001
}
```

- 错误码:
  - 400: content为空
  - 500: ops_db连接或SQL异常

### 管理端反馈列表
- 方法: GET
- 路径: /api/admin/feedback
- 响应 JSON:
```json
{
  "items": [
    {
      "feedbackId": 9001,
      "status": "open"
    }
  ]
}
```

### 管理端用户列表
- 方法: GET
- 路径: /api/admin/users
- 响应 JSON:
```json
{
  "items": [
    {
      "userId": 1001,
      "username": "user_1001",
      "status": "active"
    }
  ]
}
```

### 管理端订单列表
- 方法: GET
- 路径: /api/admin/orders
- 响应 JSON:
```json
{
  "items": [
    {
      "orderId": 10001,
      "status": "PAID"
    }
  ]
}
```

## 支付状态流转（状态图，自己设计的）
- UNPAID -> PAID -> REFUNDING -> REFUNDED
- 非法状态跳转必须返回 409

## mock / 真库切换
- 配置文件: backend/.env
- 开关: OPS_USE_MOCK=true/false
- true: 返回固定mock数据，便于并行开发
- false: 走ops_db真实读写
