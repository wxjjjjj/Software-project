# 订单车辆域 API

订单车辆域服务端口为 `8002`，通常通过网关 `8000` 访问。所有路径均带 `/api` 前缀。

## 当前职责

- 乘客发布拼车订单、搜索订单、加入拼单、查看自己的订单。
- 车主查看可接订单、选择已认证车辆接单、完成订单。
- 乘客、车主或管理员取消订单。
- 车主新增车辆并一次性提交车辆认证资料。
- 管理员审核车辆认证申请。

## Header 约定

| Header | 说明 |
| --- | --- |
| `X-User-Id` | 当前登录用户 ID。数据库模式必传，Mock 模式缺省时才会使用内置默认值。 |
| `X-User-Role` | 当前角色，管理员取消订单或审核车辆时传 `admin`。 |
| `X-Owner-Verified` | 当前用户是否已通过车主身份认证。车辆管理和接单接口要求为 `true`。 |

前端由登录会话自动组装这些 Header。数据库模式不再自动回退到 Mock 用户，缺少 `X-User-Id` 会返回 `401`。

## 订单状态

| 状态 | 说明 | 前端展示 |
| --- | --- | --- |
| `published` | 招募中，可搜索、可加入、可被车主接单 | 展示 |
| `full` | 拼单人数已满，可被车主接单 | 展示 |
| `locked` | 车主已接单，等待完成 | 展示 |
| `completed` | 已完成 | 展示 |
| `cancelled` | 已取消 | 后端保留，前端列表和详情不展示 |

状态流转：

```text
published -> full
published/full -> locked -> completed
published/full/locked -> cancelled
```

## 发布订单

`POST /api/orders`

请求：

```json
{
  "start_loc": "大学城",
  "end_loc": "广州南站",
  "depart_time_from": "2026-06-04T09:00:00",
  "depart_time_to": "2026-06-04T10:00:00",
  "group_size": 1,
  "extra_seats": 2,
  "expected_price": 45,
  "tags": ["准时出发", "禁烟"]
}
```

说明：

- 发单人由 `X-User-Id` 决定，前端不再提交 `passenger_id`。
- `seats_needed = group_size + extra_seats`，至少为 `1`。

响应：

```json
{
  "order_id": "ord-xxxx",
  "status": "published"
}
```

## 搜索订单

`GET /api/orders/search`

Query 参数均可选：

| 参数 | 说明 |
| --- | --- |
| `start_loc` | 出发地关键词 |
| `end_loc` | 目的地关键词 |
| `time_from` | 最早出发时间下限 |
| `time_to` | 最晚出发时间上限 |
| `tags` | 逗号分隔标签，例如 `禁烟,准时出发` |

响应：

```json
{
  "items": [
    {
      "order_id": "ord-seed-001",
      "passenger_id": "3",
      "start_loc": "软件园",
      "end_loc": "大学城",
      "depart_time_from": "2026-04-15T08:00:00",
      "depart_time_to": "2026-04-15T09:00:00",
      "seats_needed": 3,
      "seats_joined": 1,
      "remaining_seats": 2,
      "expected_price": 45,
      "owner_id": null,
      "vehicle_id": null,
      "locked_time": null,
      "status": "published",
      "tags": ["禁烟", "准时出发"],
      "created_at": "2026-04-13T10:00:00",
      "updated_at": "2026-04-13T10:00:00"
    }
  ]
}
```

说明：搜索接口只返回 `published` 和 `full` 状态订单。

## 订单列表

`GET /api/orders`

Query：

| 参数 | 说明 |
| --- | --- |
| `passenger_id` | 查询该乘客发布或参与的订单 |
| `owner_id` | 查询该车主已接的订单 |

不传参数时返回全部订单，当前管理员订单页使用该方式。前端会统一过滤 `cancelled` 订单，因此乘客、车主、管理员界面都不会显示已取消订单。

## 订单详情

`GET /api/orders/{order_id}`

响应为订单对象，包含基础订单字段、`tags` 和 `passengers`。

说明：

- 当前详情页会把 `passenger_id`、`owner_id`、参与乘客 ID 转换成注册用户名展示。
- 若前端拿到 `cancelled` 订单，会当作不可见订单处理并提示返回列表。

## 修改订单

`PUT /api/orders/{order_id}`

请求只传需要修改的字段：

```json
{
  "start_loc": "新出发地",
  "end_loc": "新目的地",
  "depart_time_from": "2026-06-04T09:30:00",
  "depart_time_to": "2026-06-04T10:30:00",
  "seats_needed": 3,
  "expected_price": 50,
  "tags": ["不绕路"]
}
```

约束：

- 只有发单人本人可以修改。
- 仅 `published` 状态允许修改。

## 取消订单

`POST /api/orders/{order_id}/cancel`

响应：

```json
{
  "order_id": "ord-xxxx",
  "status": "cancelled",
  "penalty": true
}
```

说明：

- 发单人、参与乘客、接单车主或管理员可以取消。
- 锁单后取消可能产生 `penalty: true`，用于后续信誉分或运营处理。
- 前端收到取消成功后会返回列表；取消后的订单不再出现在乘客、车主、管理员界面。

## 加入拼单

`POST /api/orders/{order_id}/join`

约束：

- 由 `X-User-Id` 识别加入用户。
- 发单人不能加入自己的订单。
- 订单必须处于 `published` 或 `full` 可拼单流程中，且仍有剩余座位。

响应：

```json
{
  "order_id": "ord-xxxx",
  "status": "published",
  "seats_joined": 2
}
```

## 车主接单

`POST /api/orders/{order_id}/accept`

请求：

```json
{
  "vehicle_id": "veh-001"
}
```

约束：

- `X-Owner-Verified` 必须为 `true`。
- 订单必须为 `published` 或 `full`。
- 车辆必须属于当前车主本人。
- 车辆必须已通过管理员认证，且状态可用。

响应：

```json
{
  "order_id": "ord-xxxx",
  "status": "locked",
  "owner_id": "998",
  "vehicle_id": "veh-001",
  "locked_time": "2026-06-04T10:00:00"
}
```

## 完成订单

`POST /api/orders/{order_id}/complete`

请求：

```json
{
  "operator": "domain3"
}
```

说明：当前主要由车主端完成按钮调用；`operator` 保留给交易运营域回调。

## 查询我的车辆

`GET /api/vehicles`

约束：

- `X-User-Id` 必传。
- `X-Owner-Verified` 必须为 `true`。

响应：

```json
{
  "items": [
    {
      "vehicle_id": "veh-001",
      "owner_id": "998",
      "plate_no": "粤A12345",
      "brand": "比亚迪 秦",
      "color": "白色",
      "seat_capacity": 5,
      "verified": false,
      "verify_status": "pending",
      "status": "available",
      "pendingRequestId": "12"
    }
  ]
}
```

前端当前设计：

- 已审核通过：展示为可用于接单。
- 审核中：只展示“撤回申请”。
- 已驳回或无有效申请：提示重新提交新的车辆认证申请。
- 不再提供“补交资料”“编辑”“停用”“删除”四个用户侧操作。

## 新增车辆并提交认证

`POST /api/vehicles`

请求：

```json
{
  "plate_no": "粤A12345",
  "brand": "比亚迪 秦",
  "color": "白色",
  "seat_capacity": 5
}
```

响应返回车辆对象。前端创建成功后会立即调用车辆认证提交接口，因此用户看到的是一次完整的“新增车辆并提交认证申请”流程。

车辆字段校验：

- 车牌会统一转为大写。
- 车牌号不能重复。
- 座位数必须在 `2` 到 `9` 之间。

## 提交车辆认证申请

`POST /api/vehicles/{vehicle_id}/verify-request`

请求：

```json
{
  "owner_name": "张三",
  "id_no": "110101199001011234",
  "driver_license_no": "DL20260001",
  "vehicle_license_no": "VL20260001",
  "contact_phone": "13812345678",
  "remark": "行驶证资料完整"
}
```

说明：

- 新增车辆页会一次性填写并提交这些资料。
- 已通过认证的车辆不能重复提交。
- 已有 `pending` 申请时不能重复提交。

## 撤回车辆认证申请

`DELETE /api/vehicles/verify-requests/{request_id}`

约束：

- 只能撤回当前车主自己的待审核申请。
- 撤回后管理员审核列表不再显示该申请。
- 当前前端会同步移除该车辆认证记录。

响应：

```json
{
  "message": "申请已撤回"
}
```

## 管理员查看车辆认证申请

`GET /api/vehicles/verify-requests`

Query：

| 参数 | 说明 |
| --- | --- |
| `status` | 默认为 `pending`，也可传 `approved`、`rejected` 或空值查询更多状态 |

Header：

```text
X-User-Role: admin
```

响应：

```json
{
  "items": [
    {
      "request_id": "12",
      "vehicle_id": "veh-001",
      "owner_id": "998",
      "plate_no": "粤A12345",
      "brand": "比亚迪 秦",
      "owner_name": "张三",
      "id_no_masked": "110************234",
      "driver_license_no": "DL20260001",
      "vehicle_license_no": "VL20260001",
      "contact_phone": "13812345678",
      "status": "pending",
      "review_note": ""
    }
  ]
}
```

## 管理员审核车辆认证

`PATCH /api/vehicles/verify-requests/{request_id}/review`

请求：

```json
{
  "decision": "approved",
  "review_note": "资料完整"
}
```

说明：

- `decision` 只能为 `approved` 或 `rejected`。
- 通过后车辆的 `verified` 会变为 `true`，`verify_status` 变为 `approved`。

## 后端保留但前端当前不暴露的车辆接口

以下接口仍在后端存在，用于兼容、调试或后续扩展，但当前用户侧页面不再展示对应操作：

- `PUT /api/vehicles/{vehicle_id}`：编辑车辆基础信息。
- `PATCH /api/vehicles/{vehicle_id}/status`：启用或停用车辆。
- `DELETE /api/vehicles/{vehicle_id}`：删除车辆。
- `PATCH /api/vehicles/{vehicle_id}/verified`：管理员直接更新车辆认证布尔值。

产品主流程以“新增车辆时资料一次提交，审核前可撤回，审核后等待管理员结果”为准。

## Mock 与数据库模式

- `RIDE_USE_MOCK=true`：使用 `ride_domain.py` 内置内存数据，适合无数据库联调。
- `RIDE_USE_MOCK=false`：使用 `ride_db` 真实数据，必须先执行 `sql/ride/001_init.sql`。
- `sql/ride/002_seed.sql` 是可选演示种子。只有手动导入后，数据库模式才会出现演示订单和车辆。
