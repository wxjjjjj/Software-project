# 功能域2：zj补充说明（车辆管理）

**负责人**: zj  
**关联分支**: `zj-ride-dev`  
**补充日期**: 2026-04-25  
**文档面向**: 全体组员，无需了解本域代码也能读懂

---

## 目录

1. [补充范围](#一补充范围)
2. [用户可见能力补充](#二用户可见能力补充)
3. [后端接口补充（车辆管理）](#三后端接口补充车辆管理)
4. [Mock 与真实数据库双模式](#四mock-与真实数据库双模式)
5. [前端实现补充](#五前端实现补充)
6. [本地联调与测试建议](#六本地联调与测试建议)
7. [代码改动清单](#七代码改动清单)
8. [对功能域1同学的登录须知](#八对功能域1同学的登录须知)
9. [对功能域3同学的对接须知（运营域）](#九对功能域3同学的对接须知运营域)

---

## 一、补充范围

本补充文档仅记录我（zj）在功能域2中新增或落地的工作，重点是**车主车辆管理能力**，不重复主文档中已有的订单主流程说明。

本次补充目标：

- 在车主端新增“车辆”入口，形成可操作页面
- 在订单域后端新增车辆 CRUD 与状态切换接口
- 保持与现有订单域一致的 Mock/真实数据库双模式
- 前端统一走 `/api/vehicles` 接口，避免页面本地逻辑与后端脱节

---

## 二、用户可见能力补充

### 车主视角新增页面

| 页面 | 访问路径 | 功能 |
|------|----------|------|
| 车辆主页 | `/driver/vehicles` | 车辆列表管理页；展示统计信息；支持编辑、删除、启停、认证入口 |
| 新增车辆 | `/driver/vehicles/create` | 独立新增页面，录入车辆信息并提交 |
| 编辑车辆 | `/driver/vehicles/{vehicleId}/edit` | 独立编辑页面，回填并保存车辆信息 |
| 车辆认证 | `/driver/vehicles/{vehicleId}/verify` | 提交认证资料；支持返回车辆主页 |

### 交互说明

1. 车主进入“车辆”页后，先拉取车辆列表。
2. 点击“新增车辆”会跳转到独立页面 `/driver/vehicles/create`，提交后返回车辆主页。
3. 列表中点击“编辑”会跳转到 `/driver/vehicles/{vehicleId}/edit`，表单自动回填当前车辆信息。
4. 点击“车辆认证”时：
  - 无待认证车辆：提示当前没有待认证车辆。
  - 仅 1 辆待认证：直接进入该车认证页。
  - 多辆待认证：弹出底部选择栏，先选车辆再进入认证页。
5. 认证页新增“返回车辆主页”入口，用户可随时返回 `/driver/vehicles`。
6. 删除前有确认弹窗，避免误删。

---

## 三、后端接口补充（车辆管理）

### 接口1：查询车辆列表

```http
GET /api/vehicles
X-User-Id: dev-user-1
```

响应示例：

```json
{
  "items": [
    {
      "vehicle_id": 30001,
      "owner_id": "dev-user-1",
      "plate_no": "沪A12345",
      "brand": "比亚迪秦",
      "color": "白色",
      "seat_capacity": 5,
      "verified": false,
      "status": "available"
    }
  ]
}
```

---

### 接口2：新增车辆

```http
POST /api/vehicles
Content-Type: application/json
```

请求示例：

```json
{
  "owner_id": "dev-user-1",
  "plate_no": "沪A12345",
  "brand": "比亚迪秦",
  "color": "白色",
  "seat_capacity": 5
}
```

成功响应：

```json
{
  "message": "vehicle created",
  "vehicle_id": 30002,
  "status": "available"
}
```

---

### 接口3：编辑车辆

```http
PUT /api/vehicles/{vehicle_id}
Content-Type: application/json
```

请求示例（按需字段）：

```json
{
  "brand": "本田 雅阁",
  "color": "深空黑",
  "seat_capacity": 5
}
```

---

### 接口4：修改车辆状态

```http
PATCH /api/vehicles/{vehicle_id}/status
Content-Type: application/json
```

请求示例：

```json
{
  "status": "disabled"
}
```

状态限制：仅允许 `available` / `disabled`。

---

### 接口5：删除车辆

```http
DELETE /api/vehicles/{vehicle_id}
```

成功响应：

```json
{
  "message": "vehicle deleted",
  "vehicle_id": 30002
}
```

---

### 接口6：管理员修改车辆认证状态

```http
PATCH /api/vehicles/{vehicle_id}/verified
X-User-Role: admin
Content-Type: application/json
```

请求示例：

```json
{
  "verified": true
}
```

成功响应：

```json
{
  "message": "vehicle verification updated",
  "vehicle_id": 30002,
  "verified": true
}
```

说明：该接口仅管理员可调用，普通用户调用返回 `403`。

---

## 四、Mock 与真实数据库双模式

本次车辆能力遵循订单域现有模式，通过 `RIDE_USE_MOCK` 控制。

### 模式A：Mock（`RIDE_USE_MOCK=true`）

- 使用运行期内存数据 `VEHICLE_STORE`（不内置固定测试样例）
- 不连接 MySQL
- 适合前后端快速联调与演示

### 模式B：真实数据库（`RIDE_USE_MOCK=false`）

- 使用 `ride_db.vehicle` 表
- 通过 `get_ride_conn()` 执行 SQL CRUD
- 使用 `sql/ride/002_seed.sql` 初始化测试数据
- 适合功能验收与真实数据测试

### 运行时行为

- 前端调用路径不变，始终是 `/api/vehicles...`
- 只切换 `.env` 开关即可切换数据源

---

## 五、前端实现补充

### 1) 底部导航补充

在车主 Tab 栏新增“车辆”入口，路径 `/driver/vehicles`。

### 2) 页面能力补充

`OwnerVehicles.vue` 进一步收敛为“列表管理主页”，包含：

- 统计横幅（我的车辆 / 已认证 / 待认证）
- 快捷入口（新增车辆、车辆认证）
- 列表加载与空态
- 编辑跳转到独立编辑页
- 状态切换（可接单/已停用）
- 删除确认弹窗
- 接口异常提示
- 多待认证车辆时的底部选择栏（ActionSheet）

`OwnerVehicleForm.vue` 新增为独立表单页，包含：

- 新增模式：`/driver/vehicles/create`
- 编辑模式：`/driver/vehicles/{vehicleId}/edit`
- 与认证页风格一致（`page-card + hint + 表单`）
- 提交后回到车辆主页

`OwnerCertification.vue` 补充：

- 新增“返回车辆主页”按钮，便于中断认证流程并返回管理页

`router/index.js` 补充：

- 新增路由：`/driver/vehicles/create`、`/driver/vehicles/{vehicleId}/edit`
- 新增 owner 语义重定向：`/owner/vehicles/create`、`/owner/vehicles/{vehicleId}/edit`

`AppLayout.vue` 修复：

- 修复“切换身份后需手动刷新才生效”的问题
- 将 session 改为响应式状态并在路由切换时同步 localStorage
- 现在身份切换后导航标题、角色标识、底部 Tab 可立即刷新

### 3) API 封装补充

新增并使用统一封装文件：`frontend/src/api/ride.js`，主要方法：

- `fetchOwnerVehicles()`
- `createOwnerVehicle(payload)`
- `updateOwnerVehicle(vehicleId, payload)`
- `updateOwnerVehicleStatus(vehicleId, status)`
- `deleteOwnerVehicle(vehicleId)`

---

## 六、本地联调与测试建议

### 启动建议

按项目当前脚本与配置启动网关和订单域服务，再启动前端。

### 冒烟流程（车辆）

1. 车主进入 `/driver/vehicles`，确认列表可加载。
2. 点击“新增车辆”进入 `/driver/vehicles/create`，提交后确认返回车辆主页且列表出现新记录。
3. 点击车辆“编辑”进入 `/driver/vehicles/{vehicleId}/edit`，修改品牌/颜色并保存，确认列表更新。
4. 准备 2 辆待认证车辆后点击“车辆认证”，确认出现底部选择栏，可选择目标车辆进入认证页。
5. 在认证页点击“返回车辆主页”，确认可直接回到 `/driver/vehicles`。
6. 将状态切换为 `disabled`，确认状态标签变化。
7. 删除该车辆，确认列表移除。
8. 在右上角切换身份（拼车人/车主/管理员），确认页面信息即时变化，无需手动刷新。

### 模式切换测试

1. `.env` 设 `RIDE_USE_MOCK=true`：验证无数据库也可跑通。
2. `.env` 设 `RIDE_USE_MOCK=false`：验证数据落库和重启后可保留。

---

## 七、代码改动清单

后端：

- `backend/ride/ride_domain.py`：新增车辆数据模型、校验与 CRUD 逻辑（Mock/DB 双分支）
- `backend/ride/service.py`：新增车辆管理接口路由
- `backend/gateway/main.py`：补充 `/api/vehicles` 根路径代理

前端：

- `frontend/src/layouts/AppLayout.vue`：车主 Tab 新增“车辆”入口；修复角色切换后页面需刷新问题
- `frontend/src/router/index.js`：新增车辆新增/编辑路由及 owner 重定向
- `frontend/src/views/owner/OwnerVehicles.vue`：车辆主页改为列表管理页；新增认证车辆选择栏
- `frontend/src/views/owner/OwnerVehicleForm.vue`：新增独立车辆新增/编辑页面
- `frontend/src/views/owner/OwnerCertification.vue`：新增返回车辆主页入口
- `frontend/src/api/ride.js`：新增车辆 API 请求封装

文档：

- 本文件 `docs/功能域2-zj补充.md`

---

## 八、对功能域1同学的登录须知

本节用于和功能域1（登录/账号）同学对齐联调约定，避免车辆管理页在多账号场景下读到错误用户。

### 1) 必须提供并落盘 `userId`

当前车辆管理页按以下顺序获取当前登录用户：

1. 前端从 `localStorage.session.userId` 读取。
2. 若缺失，则回退读取 `localStorage.session.username`。
3. 若两者都缺失，才回退到开发兜底值 `dev-user-1`。

这意味着：

- 如果登录后没有把稳定 `userId` 写入 session，会依赖 `username` 兜底，可能导致跨域联调时用户标识口径不一致。

### 2) 建议登录成功响应结构（功能域1后端）

建议普通用户登录接口返回至少以下字段：

```json
{
  "message": "login success",
  "token": "dev-token-1001",
  "userId": "dev-user-1",
  "role": "user",
  "ownerVerified": true,
  "username": "alice"
}
```

管理员登录同理，建议也返回 `userId`（管理员主键）。

### 3) 建议前端 session 最小字段（功能域1前端登录页）

登录成功后请保证 session 至少包含：

```json
{
  "token": "...",
  "userId": "dev-user-1",
  "role": "user",
  "ownerVerified": true,
  "username": "alice"
}
```

其中：

- `userId`：建议使用稳定字符串主键（示例：`dev-user-1`），避免和展示名混用。
- `ownerVerified`：决定是否进入车主导航与车主页面。


### 4) 联调自检清单（功能域1）

1. 登录后在浏览器检查 `localStorage.session` 是否存在 `userId`。
2. 切换两个不同账号，确认 `session.userId` 随账号变化。
3. 进入 `/driver/vehicles`，确认请求 Header `X-User-Id` 与当前账号一致（不再使用 `ownerUserId` 查询参数）。
4. 在页面右上角切换身份后，确认导航标题、角色标签、底部 Tab 立即变化（无需刷新页面）。

---

## 九、对功能域3同学的对接须知（运营域）

本节用于和功能域3（运营域）对齐“管理员车辆审核”和“订单取消惩罚联动”两类事项

### 1) 管理员车辆认证接口（新增）

运营域管理员端如需做车辆审核，可直接调用订单域接口：

```http
PATCH /api/vehicles/{vehicle_id}/verified
X-User-Role: admin
Content-Type: application/json
```

请求示例：

```json
{
  "verified": true
}
```

响应示例：

```json
{
  "message": "vehicle verification updated",
  "vehicle_id": 30002,
  "verified": true
}
```

错误码约定：

- `403`：非管理员调用（未携带或错误携带 `X-User-Role: admin`）
- `404`：车辆不存在

### 2) 订单取消惩罚联动（运营域处理）

当订单域取消接口返回 `penalty: true` 时，表示该次取消应触发信誉/惩罚逻辑；惩罚规则和执行落地由运营域处理。

建议运营域在收到该标记后：

1. 记录惩罚流水（含 `order_id`、操作者、时间）。
2. 执行对应扣分/限制策略。
3. 保证同一订单取消事件幂等处理（避免重复扣罚）。

### 3) 联调时的身份字段约定

运营域若通过前端或网关转发调用上述接口，请统一使用账号域落盘的 `session.userId` 作为用户标识，避免与 `username` 混用造成数据归属偏差。


