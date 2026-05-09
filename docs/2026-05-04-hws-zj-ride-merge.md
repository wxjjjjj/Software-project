# 2026-05-04 hws 与 zj 功能域2整合说明

## 整合范围

本次整合主要处理组长提出的 `ride.js`、`service.py`、`ride_domain.py` 不一致问题。

- 订单主流程保留 hws 实现：发布订单、搜索订单、订单详情、加入订单、车主接单、取消订单、完成订单。
- 车辆主流程合入 zj 实现：车辆新增、编辑、启用/停用、删除、车辆认证申请、管理员车辆认证审核。
- 前端新增 `/me/*` 个人中心结构，把车辆管理放到 `/me/vehicles`，车主接单仍放在 `/driver/*`。

## 当前后端职责划分

### account 域

账号域负责用户身份和车主身份状态：

- 登录、注册、用户资料。
- 车主身份申请。
- `driver_status` 或 `ownerVerified` 等身份字段。

当前 `/me/driver-application` 还是占位/半接入状态，真实车主身份申请需要和账号域继续对齐。

### ride 域

ride 域负责订单和车辆：

- 订单：`orders`、`order_tag`、`order_passenger`、`order_status_log`。
- 车辆：`vehicle`。
- 车辆认证申请：`vehicle_verify_request`。

车辆认证通过不等于用户自动成为车主。最终逻辑应为：

1. account 域确认用户具备车主身份。
2. ride 域确认某辆车已认证且可用。
3. 接单时同时校验用户、车辆归属、车辆状态和车辆认证状态。

## 初始化 SQL

本次已更新：

```text
sql/ride/001_init.sql
```

该文件现在会创建：

- `vehicle`
- `vehicle_verify_request`
- `orders`
- `order_tag`
- `order_passenger`
- `order_status_log`

本地已验证 `001_init.sql` 可以直接执行成功：

```powershell
cmd /c "docker exec -i case-mysql mysql -uroot -pRootPass123! < sql\ride\001_init.sql"
```

说明：

- `001_init.sql` 负责建库建表，足够支撑当前订单、车辆、车辆认证审核功能。
- `002_seed.sql` 是测试种子数据，不是本次整合重点；它不是幂等脚本，重复执行可能因为主键或唯一键冲突失败。

## 当前主要 API 契约

### 车辆列表

```http
GET /api/vehicles
```

响应按 zj 的接口来：

```json
{
  "items": [
    {
      "vehicle_id": "1",
      "owner_id": "123",
      "plate_no": "粤A12345",
      "brand": "Toyota",
      "color": "white",
      "seat_capacity": 5,
      "verified": true,
      "status": "available"
    }
  ]
}
```

不再返回兼容字段 `vehicles`。

### 车辆相关接口

- `POST /api/vehicles`
- `PUT /api/vehicles/{vehicle_id}`
- `PATCH /api/vehicles/{vehicle_id}/status`
- `DELETE /api/vehicles/{vehicle_id}`
- `POST /api/vehicles/{vehicle_id}/verify-request`
- `GET /api/vehicles/verify-requests`
- `PATCH /api/vehicles/verify-requests/{request_id}/review`

## 前端路由

### 个人中心

- `/me/profile`
- `/me/driver-application`
- `/me/vehicles`
- `/me/vehicles/create`
- `/me/vehicles/:vehicleId/edit`
- `/me/vehicles/:vehicleId/verify`
- `/me/messages`
- `/me/feedback`

### 车主模式

- `/driver/home`
- `/driver/orders/available`
- `/driver/orders/mine`
- `/driver/orders/:id`
- `/driver/wallet`

### 管理员

- `/admin/users`
- `/admin/orders`
- `/admin/vehicle-verifications`
- `/admin/feedback`

旧车辆路径已保留重定向：

- `/driver/vehicles` -> `/me/vehicles`
- `/driver/vehicles/create` -> `/me/vehicles/create`
- `/admin/vehicles` -> `/admin/vehicle-verifications`

## 测试说明

真实账号域车主身份申请暂未完全接通，因此提供调试入口：

```text
账号：123
密码：123
```

用该账号登录后会直接获得车主模式权限，便于测试车辆管理和车主接单流程。

已验证内容：

- 乘客发布、搜索、查看订单详情。
- 订单详情展示参与乘客。
- 车主可接订单列表和已接订单列表可进入订单详情。
- 车辆新增、编辑、启用/停用。
- 车辆认证申请提交。
- 管理员车辆认证审核页面。
- 车主接单时只允许选择属于自己、`available`、`verified` 的车辆。
