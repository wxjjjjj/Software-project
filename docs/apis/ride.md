# 订单与车辆域 API 契约

**负责人**: hws、zj  
**数据库**: ride_db  
**服务端口**: 8002（本地开发），通过网关 8000 统一暴露  
**功能范围**: 订单发布/搜索/详情/状态流转、车主接单、车辆管理、车辆认证审核

---

## 鉴权约定

所有接口通过 HTTP Header 传递用户身份，无 JWT：

| Header | 说明 | 示例 |
|--------|------|------|
| `X-User-Id` | 当前用户 ID | `dev-user-1` |
| `X-User-Role` | 用户角色（管理员操作时传入） | `admin` |
| `X-Owner-Verified` | 当前用户是否已完成车主身份认证，车辆管理和车主接单接口需要 | `true` |

> 车辆管理、车辆认证申请、车主接单等车主侧接口会同时校验 `X-Owner-Verified: true`。未完成车主身份认证的用户不能登记车辆，也不能接单。

---

## 订单接口

### 1. 发布订单

- **方法**: POST  
- **路径**: `/api/orders`  
- **权限**: 乘客（任意登录用户）

**请求 JSON**:
```json
{
  "passenger_id": "user-001",
  "start_loc": "软件园",
  "end_loc": "大学城",
  "depart_time_from": "2026-04-15T08:00:00",
  "depart_time_to": "2026-04-15T09:00:00",
  "group_size": 1,
  "extra_seats": 2,
  "expected_price": 45.0,
  "tags": ["静音", "禁烟"]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `passenger_id` | string | 发单人 ID |
| `start_loc` | string | 出发地 |
| `end_loc` | string | 目的地 |
| `depart_time_from` | ISO8601 | 最早出发时间 |
| `depart_time_to` | ISO8601 | 最晚出发时间 |
| `group_size` | int | 本人同行人数 |
| `extra_seats` | int | 额外可带人数 |
| `expected_price` | float | 期望总车费 |
| `tags` | string[] | 可选标签列表 |

**响应 JSON**:
```json
{
  "order_id": "ord-xxxxxxxx",
  "status": "published"
}
```

**错误码**: `400`（参数缺失）

---

### 2. 搜索订单

- **方法**: GET  
- **路径**: `/api/orders/search`  
- **权限**: 任意登录用户

**Query 参数**（均可选）:

| 参数 | 类型 | 说明 |
|------|------|------|
| `start_loc` | string | 出发地关键词（模糊匹配） |
| `end_loc` | string | 目的地关键词（模糊匹配） |
| `time_from` | ISO8601 | 出发时间下限 |
| `time_to` | ISO8601 | 出发时间上限 |
| `tags` | string | 标签筛选，逗号分隔，需全部命中（如 `静音,禁烟`） |

**响应 JSON**:
```json
{
  "items": [
    {
      "order_id": "ord-seed-001",
      "passenger_id": "dev-user-1",
      "start_loc": "软件园",
      "end_loc": "大学城",
      "depart_time_from": "2026-04-15T08:00:00",
      "depart_time_to": "2026-04-15T09:00:00",
      "seats_needed": 3,
      "seats_joined": 1,
      "remaining_seats": 2,
      "expected_price": 45.0,
      "owner_id": null,
      "vehicle_id": null,
      "locked_time": null,
      "status": "published",
      "tags": ["静音", "禁烟"],
      "created_at": "2026-04-13T10:00:00",
      "updated_at": "2026-04-13T10:00:00"
    }
  ]
}
```

> 仅返回 `published` / `full` 状态订单（招募中）。

---

### 3. 订单列表

- **方法**: GET  
- **路径**: `/api/orders`  
- **权限**: 登录用户

**Query 参数**（二选一）:

| 参数 | 说明 |
|------|------|
| `passenger_id` | 查询该乘客发布/参与的订单 |
| `owner_id` | 查询该车主已接的订单 |

不传参数时返回全部订单（管理员用途）。

---

### 4. 订单详情

- **方法**: GET  
- **路径**: `/api/orders/{order_id}`  
- **权限**: 登录用户

**响应**: 同搜索列表中单条结构，额外包含 `locked_time` 和 `passengers`。

**错误码**: `404`（订单不存在）

---

### 5. 修改订单

- **方法**: PUT  
- **路径**: `/api/orders/{order_id}`  
- **权限**: 发单人本人，且订单处于 `published` 状态

**请求 JSON**（仅需传需要修改的字段）:
```json
{
  "start_loc": "新出发地",
  "expected_price": 50.0
}
```

**错误码**: `403`（非本人）、`409`（状态不允许修改）

---

### 6. 取消订单

- **方法**: POST  
- **路径**: `/api/orders/{order_id}/cancel`  
- **权限**: 发单人 / 车主 / 参与乘客 / 管理员（传 `X-User-Role: admin`）

**响应 JSON**:
```json
{
  "order_id": "ord-xxx",
  "status": "cancelled",
  "penalty": true
}
```

> `penalty: true` 表示本次取消需扣除信誉积分（锁单后取消触发）。

**错误码**: `403`（无权限）、`409`（订单已结束）

---

### 7. 加入订单（拼单）

- **方法**: POST  
- **路径**: `/api/orders/{order_id}/join`  
- **权限**: 乘客（非发单人）

**响应 JSON**:
```json
{
  "order_id": "ord-xxx",
  "status": "published",
  "seats_joined": 2
}
```

> 座位满时状态自动变为 `full`。

**错误码**: `409`（已参与 / 已满员 / 状态不允许）

---

### 8. 车主接单

- **方法**: POST  
- **路径**: `/api/orders/{order_id}/accept`  
- **权限**: 已完成车主身份认证的车主（`X-User-Id` 为车主 ID，`X-Owner-Verified: true`）

**请求 JSON**:
```json
{
  "vehicle_id": "veh-001"
}
```

**响应 JSON**:
```json
{
  "order_id": "ord-xxx",
  "status": "locked",
  "owner_id": "owner-001",
  "vehicle_id": "veh-001",
  "locked_time": "2026-04-14T10:00:00"
}
```

**校验规则**:

- 订单必须处于 `published` 或 `full` 状态。
- `vehicle_id` 必须属于当前车主本人。
- 车辆必须已认证，即 `verified=true`。
- 车辆必须处于 `available` 状态，禁用车辆不能接单。

**错误码**: `403`（未完成车主身份认证 / 非本人车辆 / 无可用已认证车辆），`409`（已被接单 / 状态不允许）

---

### 9. 标记完成

- **方法**: POST  
- **路径**: `/api/orders/{order_id}/complete`  
- **权限**: 车主 / 域3支付回调

**请求 JSON**:
```json
{
  "operator": "domain3"
}
```

**响应 JSON**:
```json
{
  "order_id": "ord-xxx",
  "status": "completed"
}
```

**错误码**: `409`（订单未处于 `locked` 状态）

---

## 车辆接口

> 2026-05-04 整合后，车辆列表接口按 zj 契约返回 `{ "items": [...] }`，不再返回旧的 `{ "vehicles": [...] }`。

### 10. 查询车主名下车辆

- **方法**: GET  
- **路径**: `/api/vehicles`  
- **权限**: 已完成车主身份认证的车主（通过 `X-User-Id` 识别，并要求 `X-Owner-Verified: true`）

**响应 JSON**:
```json
{
  "items": [
    {
      "vehicle_id": "1",
      "owner_id": "123",
      "plate_no": "粤B12345",
      "brand": "本田 雅阁",
      "color": "深空黑",
      "seat_capacity": 5,
      "verified": true,
      "verify_status": "approved",
      "status": "available"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `verified` | boolean | 车辆是否已通过管理员认证 |
| `verify_status` | enum | 认证流程状态：`unsubmitted` 未提交、`pending` 审核中、`approved` 已通过 |
| `status` | enum | 车辆启停状态：`available` 可用、`disabled` 禁用 |

### 11. 新增车辆

- **方法**: POST
- **路径**: `/api/vehicles`
- **权限**: 已完成车主身份认证的车主

**请求 JSON**:
```json
{
  "plate_no": "粤B12345",
  "brand": "本田 雅阁",
  "color": "深空黑",
  "seat_capacity": 5
}
```

**校验规则**:

- 车牌号会统一转为大写。
- 车牌号必须符合大陆普通车牌或新能源车牌格式。
- 同一车牌号不能重复登记。
- 座位数必须在 2 到 9 之间。

### 12. 编辑车辆

- **方法**: PUT
- **路径**: `/api/vehicles/{vehicle_id}`
- **权限**: 已完成车主身份认证的车主，且只能编辑本人车辆

### 13. 启用或停用车辆

- **方法**: PATCH
- **路径**: `/api/vehicles/{vehicle_id}/status`
- **权限**: 已完成车主身份认证的车主，且只能操作本人车辆

**请求 JSON**:
```json
{ "status": "available" }
```

> `status` 只能是 `available` 或 `disabled`。

### 14. 删除车辆

- **方法**: DELETE
- **路径**: `/api/vehicles/{vehicle_id}`
- **权限**: 已完成车主身份认证的车主，且只能删除本人车辆

### 15. 提交车辆认证申请

- **方法**: POST
- **路径**: `/api/vehicles/{vehicle_id}/verify-request`
- **权限**: 已完成车主身份认证的车主，且只能为本人车辆提交

**请求 JSON**:
```json
{
  "owner_name": "张三",
  "id_no": "310101199001011234",
  "driver_license_no": "DL-001",
  "vehicle_license_no": "VL-001",
  "contact_phone": "13800000000",
  "remark": "补充说明"
}
```

**校验规则**:

- 已认证车辆不能重复提交认证。
- 已存在 `pending` 审核申请的车辆不能再次提交，前端会显示“该车辆认证正在审核”。


### 16. 管理员查看车辆认证申请

- **方法**: GET
- **路径**: `/api/vehicles/verify-requests`
- **权限**: 管理员（`X-User-Role: admin`）

### 17. 管理员审核车辆认证申请

- **方法**: PATCH
- **路径**: `/api/vehicles/verify-requests/{request_id}/review`
- **权限**: 管理员（`X-User-Role: admin`）

**请求 JSON**:
```json
{
  "decision": "approved",
  "review_note": "资料完整"
}
```

> `decision` 只能是 `approved` 或 `rejected`。通过后车辆 `verified` 会变为 `true`，车辆列表中的 `verify_status` 会显示为 `approved`。

---

## 订单状态流转

```
published  ──(车主接单)──▶  locked  ──(标记完成)──▶  completed
    │                         │
    └──(取消)──▶ cancelled ◀──┘(取消/强制取消)

published ──(座位满)──▶ full ──(有人退出)──▶ published
```

| 状态 | 说明 |
|------|------|
| `published` | 招募中，可搜索 |
| `full` | 已满员，不再接受加入 |
| `locked` | 已锁单（车主已接） |
| `completed` | 已完成 |
| `cancelled` | 已取消 |

---

## 数据库模式（ride_db）

```sql
-- 主表
orders(id, passenger_id, start_loc, end_loc,
       depart_time_from, depart_time_to,
       seats_needed, seats_joined, expected_price,
       owner_id, vehicle_id, locked_time,
       status, created_at, updated_at)

order_tags(order_id, tag)
order_passenger(id, order_id, passenger_id, joined_at)

vehicle(id, owner_user_id, plate_no, brand, color, seat_capacity, verified, status)
vehicle_verify_request(id, vehicle_id, owner_user_id, owner_name, id_no,
                       driver_license_no, vehicle_license_no, status, review_note)
```
