# 账号域 API

账号域服务端口为 `8001`，开发和前端集成时通常通过网关 `8000` 访问。所有路径均带 `/api` 前缀。

## 当前职责

- 普通用户注册和登录。
- 管理员独立入口登录。
- 用户资料查询，用于个人中心、订单用户展示和聊天用户名展示。
- 车主身份认证申请，提交个人资质。
- 管理员用户列表与身份状态维护。
- 跨领域信誉分更新。

车辆登记和车辆认证审核属于订单车辆域，接口见 [ride.md](./ride.md)。账号域保留的 `/api/users/driver/cars/{user_id}` 是历史兼容接口，当前前端车辆主线不再使用它。

## 用户注册

`POST /api/auth/register`

请求：

```json
{
  "username": "alice",
  "password": "password123",
  "phone": "13812345678",
  "real_name": "张三",
  "id_card": "110101199001011234"
}
```

字段约束：

| 字段 | 说明 |
| --- | --- |
| `username` | 3 到 20 位 |
| `password` | 至少 6 位 |
| `phone` | 中国大陆手机号格式 |
| `real_name` | 真实姓名 |
| `id_card` | 18 位身份证号，末位可为 `X` |

响应：

```json
{
  "message": "register success",
  "userId": 4
}
```

常见错误：

- `409`：用户名、手机号或身份证号已存在。
- `422`：请求字段不符合 Pydantic 校验。

## 普通用户登录

`POST /api/auth/login`

请求：

```json
{
  "username": "alice",
  "password": "password123"
}
```

响应示例：

```json
{
  "userId": 3,
  "username": "111",
  "role": "passenger",
  "account_status": "active",
  "passenger": {
    "score": 100,
    "status": "active"
  },
  "driver": {
    "score": 100,
    "status": "unapplied"
  }
}
```

说明：

- 管理员不能从普通用户登录入口进入，必须使用 `/api/admin/login`。
- 前端根据返回的 `role`、`driver.status` 和本地会话决定当前是乘客、车主还是管理员视图。
- Mock 模式和 `sql/account/002_seed.sql` 包含常用测试账号：`admin/123456`、`yxx/yxx123`、`111/111111`、`driver1/driver1`。

常见错误：

- `401`：用户名或密码错误。
- `403`：管理员误用普通入口，或账号整体停用。

## 管理员登录

`POST /api/admin/login`

请求：

```json
{
  "username": "admin",
  "password": "123456"
}
```

响应字段与普通登录类似，但 `role` 为 `admin`。

说明：

- 管理员使用独立登录页。
- 管理员界面不显示普通用户个人中心，只保留用户、订单、车辆审核、投诉等后台工作台。

## 查询用户资料

`GET /api/users/profile/{user_id}`

响应示例：

```json
{
  "id": 3,
  "username": "111",
  "phone": "13900000001",
  "real_name": "李四",
  "id_card": "110101199001011235",
  "passenger_score": 100,
  "passenger_status": "active",
  "driver_score": 100,
  "driver_status": "unapplied",
  "role": "passenger"
}
```

当前前端用途：

- 个人中心展示当前用户资料。
- 订单详情、聊天、用户主页将用户编号转换为注册用户名展示。
- 投诉入口通过用户主页进入，表单展示“投诉用户名”。

常见错误：

- `404`：用户不存在。

## 车主身份认证申请

`POST /api/users/driver/apply/{user_id}`

请求：

```json
{
  "real_name": "张三",
  "id_card": "110101199001011234",
  "driver_license_no": "DL20260001",
  "contact_phone": "13812345678",
  "remark": "三年以上驾龄"
}
```

说明：

- 这是“成为车主”的个人资质申请，不包含车辆资料。
- 通过后用户才可以进入车辆登记与车辆认证流程。
- 车辆资料在“我的车辆 / 新增车辆并提交认证”页面一次性提交，走订单车辆域接口。
- 旧字段 `license_plate`、`car_model`、`car_color` 在模型中仅为兼容历史前端，当前主流程不会写入账号域车辆表。

响应：

```json
{
  "message": "申请已提交"
}
```

常见错误：

- `400`：用户不存在、状态不允许重复申请，或数据库更新失败。

## 历史车辆查询接口

`GET /api/users/driver/cars/{user_id}`

说明：

- 该接口来自早期账号域车辆方案。
- 当前前端车辆管理统一使用订单车辆域 `/api/vehicles`。
- 新功能不要继续依赖该接口。

## 管理员用户列表

`GET /api/users/admin/users`

响应示例：

```json
{
  "items": [
    {
      "userId": 3,
      "username": "111",
      "phone": "13900000001",
      "role": "passenger",
      "account_status": "active",
      "passenger_score": 100,
      "passenger_status": "active",
      "driver_score": 100,
      "driver_status": "unapplied"
    }
  ]
}
```

当前前端仅做用户信息和身份状态展示，不再把“封禁乘客/车主”作为主要操作按钮展示。

## 管理员更新身份状态

`POST /api/users/admin/update-status`

请求：

```json
{
  "userId": 3,
  "target_identity": "driver",
  "new_status": "banned"
}
```

字段说明：

- `target_identity`：`passenger` 或 `driver`。
- `new_status`：通常为 `active` 或 `banned`。

响应：

```json
{
  "message": "状态已更新"
}
```

说明：接口仍保留给后台治理和后续扩展使用，当前前端不再突出大按钮式封禁操作。

## 信誉分更新

`POST /api/users/score/update`

该接口用于跨领域调用，参数通过 Query 传递：

```text
/api/users/score/update?userId=3&role_type=passenger&score_change=-5
```

响应：

```json
{
  "new_score": 95
}
```

字段说明：

- `role_type`：`passenger` 或 `driver`。
- `score_change`：可正可负。
