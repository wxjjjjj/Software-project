# 功能域2：zj补充说明（车辆管理）

**负责人**: zj  
**关联分支**: `zj-ride-dev`  
**补充日期**: 2026-04-18  
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
| 车辆管理 | `/driver/vehicles` | 新增、编辑、删除车辆；启用/停用车辆；查看车辆认证状态 |

### 交互说明

1. 车主进入“车辆”页后，先拉取车辆列表。
2. 可在表单中录入车牌号、品牌、颜色、座位数新增车辆。
3. 列表中每项支持编辑、启停和删除。
4. 删除前有确认弹窗，避免误删。

---

## 三、后端接口补充（车辆管理）

### 接口1：查询车辆列表

```http
GET /api/vehicles?ownerUserId=20001
```

响应示例：

```json
{
  "items": [
    {
      "vehicleId": 30001,
      "ownerUserId": 20001,
      "plateNo": "沪A12345",
      "brand": "比亚迪秦",
      "color": "白色",
      "seatCapacity": 5,
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
  "ownerUserId": 20001,
  "plateNo": "沪A12345",
  "brand": "比亚迪秦",
  "color": "白色",
  "seatCapacity": 5
}
```

成功响应：

```json
{
  "message": "vehicle created",
  "vehicleId": 30002,
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
  "seatCapacity": 5
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
  "vehicleId": 30002
}
```

---

## 四、Mock 与真实数据库双模式

本次车辆能力遵循订单域现有模式，通过 `RIDE_USE_MOCK` 控制。

### 模式A：Mock（`RIDE_USE_MOCK=true`）

- 使用内存数据 `VEHICLE_STORE`
- 不连接 MySQL
- 适合前后端快速联调与演示

### 模式B：真实数据库（`RIDE_USE_MOCK=false`）

- 使用 `ride_db.vehicle` 表
- 通过 `get_ride_conn()` 执行 SQL CRUD
- 适合功能验收与真实数据测试

### 运行时行为

- 前端调用路径不变，始终是 `/api/vehicles...`
- 只切换 `.env` 开关即可切换数据源

---

## 五、前端实现补充

### 1) 底部导航补充

在车主 Tab 栏新增“车辆”入口，路径 `/driver/vehicles`。

### 2) 页面能力补充

`OwnerVehicles.vue` 从占位页改为功能页，包含：

- 列表加载与空态
- 新增与编辑复用同一表单
- 状态切换（可接单/已停用）
- 删除确认弹窗
- 接口异常提示

### 3) API 封装补充

新增并使用统一封装文件：`frontend/src/api/ride.js`，主要方法：

- `fetchOwnerVehicles(ownerUserId)`
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
2. 新增一辆车，确认列表出现新记录。
3. 编辑该车辆品牌/颜色，确认更新成功。
4. 将状态切换为 `disabled`，确认状态标签变化。
5. 删除该车辆，确认列表移除。

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

- `frontend/src/layouts/AppLayout.vue`：车主 Tab 新增“车辆”入口
- `frontend/src/views/owner/OwnerVehicles.vue`：车辆管理页面功能化
- `frontend/src/api/ride.js`：新增车辆 API 请求封装

文档：

- 本文件 `docs/功能域2-zj补充.md`

---

## 八、对功能域1同学的登录须知

本节用于和功能域1（登录/账号）同学对齐联调约定，避免车辆管理页在多账号场景下读到错误用户。

### 1) 必须提供并落盘 `userId`

当前车辆管理页按以下顺序获取当前登录用户：

1. 前端从 `localStorage.session.userId` 读取。
2. 若缺失，则回退到开发兜底值 `20001`。

这意味着：

- 如果登录后没有把真实 `userId` 写入 session，切换账号后仍可能读到同一份车辆数据。

### 2) 建议登录成功响应结构（功能域1后端）

建议普通用户登录接口返回至少以下字段：

```json
{
  "message": "login success",
  "token": "dev-token-1001",
  "userId": 1001,
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
  "userId": 1001,
  "role": "user",
  "ownerVerified": true,
  "username": "alice"
}
```

其中：

- `userId`：必须为可转数字值（当前车辆页按 `Number(session.userId)` 解析）。
- `ownerVerified`：决定是否进入车主导航与车主页面。


### 4) 联调自检清单（功能域1）

1. 登录后在浏览器检查 `localStorage.session` 是否存在 `userId`。
2. 切换两个不同账号，确认 `session.userId` 随账号变化。
3. 进入 `/driver/vehicles`，确认请求参数 `ownerUserId` 与当前账号一致。

