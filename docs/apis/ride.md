# 订单与车辆域 API 契约

**负责人**: hws、zj  
**数据库**: ride_db  
**服务端口**: 7002（本地开发），通过网关 7000 统一暴露  
**功能范围**: 订单发布/搜索/详情/状态流转、车主接单、车辆查询

---

## 鉴权约定

所有接口通过 HTTP Header 传递用户身份，无 JWT：

| Header | 说明 | 示例 |
|--------|------|------|
| `X-User-Id` | 当前用户 ID | `dev-user-1` |
| `X-User-Role` | 用户角色（管理员操作时传入） | `admin` |

---

## 订单接口

### 1. 发布订单

- **方法**: POST  
- **路径**: `/api/orders`  
- **权限**: 拼车人（任意登录用户）

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

**响应**: 同搜索列表中单条结构，额外包含 `locked_time`。

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
- **权限**: 拼车人（非发单人）

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
- **权限**: 车主（`X-User-Id` 为车主 ID）

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

**错误码**: `409`（已被接单 / 状态不允许）

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

### 10. 查询车主名下车辆

- **方法**: GET  
- **路径**: `/api/vehicles`  
- **权限**: 车主（通过 `X-User-Id` 识别）

**响应 JSON**:
```json
{
  "vehicles": [
    {
      "vehicle_id": "veh-mock-002",
      "owner_id": "dev-user-1",
      "plate_no": "粤B·12345",
      "brand": "本田 雅阁",
      "color": "深空黑",
      "seat_capacity": 5,
      "status": "available"
    }
  ]
}
```

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

vehicles(id, owner_id, plate_no, brand, color, seat_capacity, status)
```
