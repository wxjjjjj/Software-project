# 订单车辆域 API 契约（示例）

hws, zj

数据库: ride_db

功能范围: 车辆增删改查、订单发布/检索/详情、车主接单、订单状态流转

## 集成环境
- 统一地址: http://<wxj主机>:8000
- 接口前缀: /api
- 约束规则: 订单主状态仅由订单车辆域维护

## 必需接口【仅一点点示例，根据自己的设计修改即可】

### 乘客发布订单
- 方法: POST
- 路径: /api/orders
- 请求 JSON:
```json
{
  "role": "passenger",
  "startLoc": "Software Park",
  "endLoc": "University Town",
  "seatsNeeded": 1,
  "expectedPrice": 35.5
}
```
- 响应 JSON:
```json
{
  "message": "order created",
  "orderId": 10002,
  "status": "CREATED"
}
```
- 错误码: 403（车主不能发单）, 400（参数错误）

### 订单搜索
- 方法: GET
- 路径: /api/orders/search
- 响应 JSON:
```json
{
  "items": [
    {
      "orderId": 10001,
      "from": "Software Park",
      "to": "University Town",
      "tag": ["Morning", "No Smoking"],
      "status": "CREATED",
      "ownerId": null,
      "vehicleId": null,
      "lockedTime": null
    }
  ]
}
```

### 车主接单
- 方法: POST
- 路径: /api/orders/{orderId}/accept-by-driver
- 请求 JSON:
```json
{
  "ownerId": 20001,
  "vehicleId": 30001
}
```
- 响应 JSON:
```json
{
  "message": "driver accepted and order locked",
  "orderId": 10001,
  "status": "LOCKED",
  "ownerId": 20001,
  "vehicleId": 30001,
  "lockedTime": "2026-03-30T20:00:00"
}
```
- 错误码: 404（订单不存在）, 409（订单已被接）

### 乘客确认拼单
- 方法: POST
- 路径: /api/orders/{orderId}/confirm-by-passenger
- 响应 JSON:
```json
{
  "message": "passenger confirmed",
  "orderId": 10001,
  "status": "PASSENGER_CONFIRMED"
}
```

## 订单状态流转【仅示例】
- CREATED -> LOCKED -> PASSENGER_CONFIRMED -> PAID -> COMPLETED
- 任意取消路径 -> CANCELED
- 非法状态跳转必须返回 409

