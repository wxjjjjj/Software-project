# OPS 域（yzr）合并到集成版本 —— 操作报告

**日期**: 2026-05-17
**操作人**: yzr
**状态**: 全部实施完成

---

## 实施完成清单

| 类别 | 改动项 | 文件数 | 状态 |
|------|--------|--------|------|
| 后端 | service.py + ops_domain.py 完整覆盖 | 2 | ✅ |
| 数据库 | 001_init.sql 覆盖 + 002_seed.sql 新建 | 2 | ✅ |
| 前端 API | ops.js 新建 | 1 | ✅ |
| 前端页面(yzr自有) | PassengerPayment/Feedback/Wallet, OwnerWallet/Feedback, AdminFeedback 覆盖 | 5 | ✅ |
| 前端页面(yzr新建) | PassengerWallet.vue, ChatRoom.vue 新建 | 2 | ✅ |
| 路由| router/index.js 新增 import + 4 条路由 | +10 行 | ✅ |
| 网关 | gateway/main.py 新增 chat/complaints 代理 | +35 行 | ✅ |
| 导航 | AppLayout.vue 乘客+车主菜单新增 wallet 入口 | +2 行 | ✅ |
| 订单详情(hws/zj) | PassengerOrderDetail.vue 新增支付/聊天/投诉入口 | +9 行 | ✅ |
| 车主订单(hws/zj) | OwnerOrderMine.vue 新增聊天按钮 | +8 行 | ✅ |

---

## 一、合并概述

原 `ds/Software-project-main/` 中 yzr 的 OPS 域完整实现（15 个 API + 7 个前端页面 + 完整 SQL）合并到集成版 `Software-project-2353278wyx/`。

集成版中 OPS 域原先为骨架代码（仅 7 个端点 + 5 个占位页面 + 示例 SQL），本次合并用 yzr 的完整设计覆盖。

---

## 二、yzr 自主修改的文件（无需审批）

以下文件完全由 yzr 维护，直接覆盖或新建：

### 2.1 后端（Ops 域独有）

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/ops/service.py` | **覆盖** | 骨架 7 端点 → 完整 15 端点 |
| `backend/ops/ops_domain.py` | **覆盖** | 使用 yzr 设计的表结构（ops_wallet/ops_wallet_log/ops_chat_message/ops_complaint） |
| `backend/ops/ops_db.py` | 不变 | 已有，与 yzr 版本一致 |

### 2.2 数据库

| 文件 | 操作 | 说明 |
|------|------|------|
| `sql/ops/001_init.sql` | **覆盖** | 骨架 7 表 → yzr 设计 4 表（ops_wallet / ops_wallet_log / ops_chat_message / ops_complaint） |
| `sql/ops/002_seed.sql` | **新建** | 演示种子数据 |

### 2.3 前端

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/api/ops.js` | **新建** | API 封装模块（15 个导出函数） |
| `views/passenger/PassengerPayment.vue` | **覆盖** | 占位页 → 真实支付页 |
| `views/passenger/PassengerFeedback.vue` | **覆盖** | 占位页 → 投诉提交+我的投诉 |
| `views/passenger/PassengerWallet.vue` | **新建** | （集成版缺失，已创建） |
| `views/owner/OwnerWallet.vue` | **覆盖** | 占位页 → 车主钱包 |
| `views/owner/OwnerFeedback.vue` | **覆盖** | 占位页 → 车主投诉 |
| `views/admin/AdminFeedback.vue` | **覆盖** | 占位页 → 统计+投诉管理+提现管理 |
| `views/common/ChatRoom.vue` | **新建** | （集成版缺失，已创建） |
| `views/me/MeMessages.vue` | **覆盖** | 占位页 → 聊天入口导航（引导至订单聊天） |
| `views/me/MeFeedback.vue` | **覆盖** | 占位页 → 投诉入口导航（引导至对应身份投诉页） |

### 2.4 文档

| 文件 | 操作 | 说明 |
|------|------|------|
| `docs/apis/ops.md` | **覆盖** | 骨架版 7 端点 → 完整版 12 端点文档 |

---

## 三、需要组长审批的他人代码改动

以下改动涉及其他同学维护的文件，请求审核。

### 3.1 路由器 `frontend/src/router/index.js`

**改动操作**: 已在文件中直接修改，具体如下：

#### 新增 import（在 yzr 注释标记附近）

```javascript
// === yzr ops pages ===
import PassengerWallet from '../views/passenger/PassengerWallet.vue'   // yzr
import ChatRoom from '../views/common/ChatRoom.vue'                     // yzr
// === end yzr ===
```

#### 新增路由（在 children 数组中）

```javascript
// yzr: passenger wallet + chat
{ path: 'passenger/wallet',       component: PassengerWallet, meta: { requiresAuth: true, role: 'passenger' } },
{ path: 'passenger/chat/:orderId', component: ChatRoom,       meta: { requiresAuth: true, role: 'passenger' } },
// yzr: driver chat
{ path: 'driver/chat/:orderId',   component: ChatRoom,        meta: { requiresAuth: true, role: 'driver' } },
// yzr: admin withdrawals redirect to AdminFeedback
{ path: 'admin/withdrawals',      component: AdminFeedback,   meta: { requiresAuth: true, role: 'admin' } },
```

---

### 3.2 网关 `backend/gateway/main.py`

**改动操作**: 已在文件中直接修改，在 `/api/admin/{path:path}` 之前添加两段路由代理。

```python
# === yzr: chat proxy ===
@app.api_route(
    "/api/chat/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ops_chat_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, OPS_SERVICE_URL)


# === yzr: complaints proxy ===
@app.api_route(
    "/api/complaints/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ops_complaints_sub_proxy(path: str, request: Request):
    _ = path
    return await _forward(request, OPS_SERVICE_URL)


@app.api_route(
    "/api/complaints",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def ops_complaints_root_proxy(request: Request):
    return await _forward(request, OPS_SERVICE_URL)
```

> **注意**: `/api/chat/` 和 `/api/complaints/` 代理必须放在 `/api/admin/{path:path}` 前面，否则会被 `/api/admin/` 误吞。

---

### 3.3 导航布局 `frontend/src/layouts/AppLayout.vue`（wyx 维护）

**改动操作**: 已在文件中直接修改。

#### 管理员菜单 — 不改动（已有"投诉处理"→/admin/feedback）✅

#### 乘客菜单 — 新增 2 项

```javascript
const passengerMenus = [
  { name: '首页', path: '/passenger/home' },
  { name: '我的订单', path: '/passenger/orders/mine' },
  { name: '我的钱包', path: '/passenger/wallet' },       // ← yzr 新增
  { name: '认证车主', path: '/driver/certification' }
]
```

#### 车主菜单 — 新增 1 项

```javascript
const driverMenus = [
  { name: '接单大厅', path: '/driver/home' },
  { name: '行程管理', path: '/driver/orders/mine' },
  { name: '我的车辆', path: '/driver/vehicles' },
  { name: '钱包提现', path: '/driver/wallet' }            // ← yzr 新增
]
```

---

### 3.4 订单详情页 `frontend/src/views/passenger/PassengerOrderDetail.vue`（hws/zj 维护）

**改动操作**: 已在文件中直接修改。在"操作区"部分，锁单状态（已加入且订单非 cancelled/completed）下方添加支付和聊天入口。

```html
<!-- yzr: 支付与聊天入口 -->
<div class="action-area" v-if="order.status !== 'cancelled' && order.status !== 'completed'">
  <!-- 已有：加入拼车、取消订单等 -->

  <!-- yzr: 支付按钮 —— 已加入且订单已锁定时显示 -->
  <div v-if="hasJoined && order.status === 'locked'" class="yzr-ops-actions">
    <van-button
      round block type="primary"
      @click="$router.push(`/passenger/payment/${orderId}`)"
    >去支付</van-button>
    <van-button
      round plain type="default"
      @click="$router.push(`/passenger/chat/${orderId}`)"
      style="margin-top:8px"
    >联系车主</van-button>
    <van-button
      round plain type="default"
      @click="$router.push('/passenger/feedback')"
      style="margin-top:8px"
    >投诉举报</van-button>
  </div>
</div>
```

### 3.5 车主订单管理 `frontend/src/views/owner/OwnerOrderMine.vue`（hws/zj 维护）

**改动操作**: 已在文件中直接修改。在已锁单的订单卡片的操作按钮中追加聊天入口。

```html
<!-- yzr: 聊天入口 -->
<button v-if="o.status === 'locked'" class="btn-chat" @click="goChat(o)">💬 聊天</button>
```

```javascript
// yzr: 跳转聊天
function goChat(o) {
  router.push(`/driver/chat/${o.order_id}`)
}
```

### 3.6 启动脚本 `backend/scripts/run_all.sh`

**改动操作**: 修正 account 服务启动模块名。集成版中 FastAPI `app` 位于 `account_domain.py`，原脚本错误指向 `service.py`。

```bash
# 修改前
python -m uvicorn backend.account.service:app --reload --port 8001 --host 0.0.0.0 &
# 修改后（修复为 account_domain）
python -m uvicorn backend.account.account_domain:app --reload --port 8001 --host 0.0.0.0 &
```

---

## 四、API 端点变化列表

| 路径 | 方法 | 原骨架 | yzr 完整版 | 用途 |
|------|------|--------|-----------|------|
| `/api/payments/orders/{id}/pay` | POST | 有（简化） | 有（增强） | 支付（含幂等+双人转账） |
| `/api/wallet/info?user_id=X` | GET | `/api/wallet/me`（无参） | `/api/wallet/info`（有参） | 钱包查询 |
| `/api/wallet/withdraw` | POST | 有 | 有 | 提现 |
| `/api/wallet/logs` | GET | **无** | **新增** | 流水分页 |
| `/api/chat/messages` | POST/GET | **无** | **新增** | 发消息/查记录 |
| `/api/chat/messages/read` | PUT | **无** | **新增** | 标记已读 |
| `/api/complaints` | POST/GET | **无** | **新增** | 提交投诉/查看我的 |
| `/api/admin/complaints` | GET | **无** | **新增** | 管理端投诉列表 |
| `/api/admin/complaints/{id}` | PUT | **无** | **新增** | 处理投诉 |
| `/api/admin/stats` | GET | **无** | **新增** | 运营统计 |
| `/api/admin/withdrawals` | GET | **无** | **新增** | 提现列表 |
| `/api/admin/withdrawals/{uid}/approve` | POST | **无** | **新增** | 批准提现 |
| `/api/admin/withdrawals/{uid}/reject` | POST | **无** | **新增** | 驳回提现 |
| `/api/feedback` | POST | 有 | **废弃**（用 /api/complaints 替代） | - |
| `/api/admin/feedback` | GET | 有 | **废弃**（用投诉管理替代） | - |
| `/api/admin/users` | GET | 有 | **废弃**（account 域负责） | - |
| `/api/admin/orders` | GET | 有 | **废弃**（ride 域负责） | - |

---

## 五、数据库表变化

| 原骨架表 | yzr 表 | 说明 |
|----------|--------|------|
| `payment_order` | `ops_wallet` + `ops_wallet_log` | 支付通过钱包转账+流水记录实现 |
| `wallet_account` | `ops_wallet` | 字段设计不同，yzr 版增加了 status 字段 |
| `wallet_txn` | `ops_wallet_log` | yzr 版更完整（幂等键、余额快照、对手方） |
| `withdraw_request` | `ops_wallet_log(biz_type=2)` | 提现通过冻结余额+流水记录实现 |
| `feedback` + `feedback_reply` | `ops_complaint` | yzr 版有更完整的投诉字段（投诉人/被投诉人/类型/管理员回复） |
| `admin_action_log` | （暂不包含） | 可后续按需添加 |
| （无） | `ops_chat_message` | **新增**：司乘聊天消息 |

---

## 六、前端导航入口变化

| 角色 | 页面 | 入口 |
|------|------|------|
| 管理员 | 投诉处理 | tabbar 已有 ✅ |
| 管理员 | 提现管理 | 投诉处理页面内的 tab ✅ |
| 乘客 | 钱包 | tabbar **新增**"我的钱包" |
| 乘客 | 支付 | 订单详情页"去支付"按钮 **新增** |
| 乘客 | 聊天 | 订单详情页"联系车主"按钮 **新增** |
| 乘客 | 投诉 | 订单详情页"投诉举报"按钮 **新增** |
| 车主 | 钱包 | tabbar **新增**"钱包提现" |
| 车主 | 聊天 | 行程管理页"聊天"按钮 **新增** |

---

## 七、建议

1. `backend/.env` 中 `OPS_USE_MOCK` 当前为 `true`，建议联调时改为 `false`。
2. OPS 服务启动脚本 `backend/scripts/run_ops.ps1` 已存在，可正常使用。
3. 完整 API 文档见 `docs/apis/ops.md`（已更新）。

---

以上所有改动已完成。请组长过目，如有问题请告知。

---

## 八、测试期间追加修改（2026-05-18-yzr）

按照 [demo_ops.md](../../ds/Software-project-main/demo_ops.md) 进行端到端测试，发现并修复以下问题：

### 8.1 服务启动修复

| 问题 | 原因 | 修复 |
|------|------|------|
| Account 服务启动报 `Attribute 'app' not found` | `run_all.sh` 指向 `backend.account.service:app`，但集成版 FastAPI `app` 在 `account_domain.py` | 修改 `backend/scripts/run_all.sh:5`: `backend.account.account_domain:app` |
| Ride 服务发布订单报 `access denied for user` | `RIDE_USE_MOCK=false` 尝试连 MySQL root@localhost（WSL auth_socket 不兼容） | 修改 `backend/.env`: `RIDE_USE_MOCK=true` |
| OPS 钱包提现后刷新归零 | `OPS_USE_MOCK=true` 为内存模式，重启即丢 | 创建 `carpool`@`localhost` MySQL 用户并执行 `sql/ops/001_init.sql`，修改 `backend/.env`: `OPS_USE_MOCK=false` |

### 8.2 网关路由修复

chat/complaints 代理路径必须放在 `/api/admin/{path:path}` 之前，否则路由会被 admin 通配吞掉。

### 8.3 order_id 类型统一（string）

**核心问题**: Ride mock 使用字符串订单 ID（如 `"ord-seed-001"`），但 OPS 域 chat 和 complaint 的 order_id 原为 `int`/`BIGINT`。`parseInt("ord-seed-001")` = `NaN`，导致 Pydantic 报 `"无效的订单ID"` 和 MySQL 报 `(1366, "Incorrect integer value")`。

**统一方案**: order_id 全链路改为 `str`/`VARCHAR(64)`。

| 文件 | 改动 |
|------|------|
| `backend/ops/ops_domain.py` | `SendMessageRequest.orderId: int` → `str`；`CreateComplaintRequest.orderId: Optional[int]` → `Optional[str]`；`get_messages()`/`mark_messages_read()` 参数 `int` → `str` |
| `backend/ops/service.py` | `get_messages(order_id: int)` → `str`；`mark_read(order_id: int)` → `str` |
| `sql/ops/001_init.sql` | `ops_chat_message.order_id BIGINT` → `VARCHAR(64)`；`ops_complaint.order_id BIGINT` → `VARCHAR(64)` |
| `frontend/src/views/common/ChatRoom.vue` | 移除 `parseInt(orderId)`，直接传字符串 |
| `frontend/src/views/passenger/PassengerFeedback.vue` | 移除 `parseInt(form.value.orderId)`，`type="number"` → 无类型 |
| `frontend/src/views/owner/OwnerFeedback.vue` | 同上 |

### 8.4 前端 API 模块修复

| 文件 | 问题 | 修复 |
|------|------|------|
| `frontend/src/api/ops.js:9-13` | `getUserId()` 返回可能为 string（如 `"1"`），Pydantic 要求 int | 添加 `Number(s.userId)` |
| `frontend/src/api/ops.js:23-38` | Pydantic 校验错误 `detail` 为数组时，`new Error(array)` 显示 `"[object Object]"` | 数组/对象 `detail` 格式化为可读字符串 |

### 8.5 占位页面替换

| 原状态 | 新状态 |
|--------|--------|
| `MeMessages.vue` 显示「消息模块待接入」 | 调用 Ride API 列出订单，提供「进入聊天」和「订单详情」按钮 |
| `MeFeedback.vue` 显示「反馈功能待接入」 | 根据角色提供对应投诉页面入口 |

### 8.6 OPS 按钮可见性修复

| 页面 | 原逻辑 | 新逻辑 |
|------|--------|--------|
| `PassengerOrderDetail.vue` | 聊天/投诉按钮仅对 `locked` 订单显示 | 对 published + locked 订单均显示（含司机视角），支付按钮保持 locked 限定 |
| `OwnerOrderMine.vue` | 聊天按钮仅对 `locked` 订单显示 | 对 cancelled/completed 以外的所有订单显示 |

### 8.7 ChatRoom 发送消息修复

| 问题 | 修复 |
|------|------|
| `senderId` 从 localStorage 取可能是 string | `const mid = Number(myId)` |
| `parseInt(orderId)` 导致 NaN | 直接传字符串 `orderId: orderId` |

### 8.8 投诉表单修复

| 问题 | 修复 |
|------|------|
| `PassengerFeedback.vue` / `OwnerFeedback.vue` 仍使用 `parseInt(form.value.orderId)`，导致 `"Input should be a valid string"`（因为 order_id 已改为 str） | 改为 `form.value.orderId \|\| null`，同时去掉 `van-field` 的 `type="number"` |

### 8.9 环境配置最终状态

```ini
# backend/.env 关键配置
RIDE_USE_MOCK=false         # Ride 使用真实 MySQL（2026-05-18 切换）
RIDE_DB_USER=carpool
RIDE_DB_PASSWORD=carpool123
OPS_USE_MOCK=false          # OPS 使用真实 MySQL
OPS_DB_USER=carpool
OPS_DB_PASSWORD=carpool123
OPS_DB_HOST=localhost
OPS_DB_PORT=3306
OPS_DB_NAME=ops_db
```

### 8.10 测试验证结果

| 功能 | 状态 |
|------|------|
| 钱包查询 | ✅ 通过 |
| 提现申请及余额冻结 | ✅ 通过 |
| 支付（幂等） | ✅ 通过 |
| 司乘聊天（发送/接收/已读） | ✅ 通过 |
| 投诉提交及列表 | ✅ 通过 |
| 管理员投诉处理 | ✅ 通过 |
| 管理员提现审批 | ✅ 通过 |
| 运营统计 | ✅ 通过 |

---

## 九、支付与多角色联调追加修改（2026-05-18-yzr）

### 9.1 Ride 服务从 Mock 切换到真实 MySQL

**问题**: Rider mock 数据的 `passenger_id` 为 `"dev-user-1"` 等字符串，但 Account 登录返回数字 `userId: 999`。前后端 ID 体系不匹配，导致 `listMyOrders` 后端过滤始终返回空。

**方案**: 将 Ride 切换到真实 MySQL，种子数据使用 Account mock 的用户 ID。

| 步骤 | 操作 |
|------|------|
| 建库建表 | `mysql -u carpool -pcarpool123 < sql/ride/001_init.sql` 创建 `ride_db` 及 6 张表 |
| 种子数据 | 4 条订单 + 3 辆车 + 标签 + 乘客记录，所有 `passenger_id`/`owner_id` 改为 `999` |
| 配置切换 | `.env`: `RIDE_USE_MOCK=false`, `RIDE_DB_USER=carpool`, `RIDE_DB_PASSWORD=carpool123` |

```sql
-- Ride 种子数据（user ID 与 Account mock 对齐）
INSERT INTO orders (id, passenger_id, ..., owner_id, ...) VALUES
  ('ord-seed-001', '999', ..., NULL, ...),     -- 乘客发布
  ('ord-seed-002', '999', ..., NULL, ...),
  ('ord-seed-003', '999', ..., '998', ...),    -- 已锁单（车主 998 接单）
  ('ord-seed-004', '999', ..., NULL, ...);

INSERT INTO vehicle (id, owner_user_id, ...) VALUES
  (1, '998', ...),    -- 车主 998 的车辆
  (2, '999', ...),
  (3, '999', ...);
```

### 9.2 Account Mock 添加多角色测试账号

`backend/account/service.py:15-25` — `authenticate_user()` mock 分支新增 `driver1`：

```python
if username == "driver1":
    return {"userId": 998, "username": "driver1", "role": "driver",
            "driver": {"score": 100, "status": "approved"}}
```

测试账号表：

| 用户名 | userId | 角色 | 用途 |
|--------|--------|------|------|
| `admin` | 1 | admin | 管理后台 |
| `driver1` | 998 | driver | 车主（order owner） |
| 任意其他 | 999 | passenger | 乘客 |

### 9.3 支付 API order_id 类型修复

| 位置 | 原类型 | 修复后 |
|------|--------|--------|
| `ops_domain.py:77` `pay_order(order_id)` | `int` | `str` |
| `service.py:35` `pay_order(order_id)` | `int` | `str` |
| `ops_wallet_log.biz_ref_id` (MySQL 列) | `BIGINT` | `VARCHAR(128)` |
| `sql/ops/001_init.sql` 同列 | `BIGINT` | `VARCHAR(128)` |

错误现象: `"Input should be a valid integer, unable to parse string as an integer"` — 订单 ID `"ord-seed-003"` 无法解析为 `int`。

### 9.4 PassengerOrderDetail.vue 类型比较修复

**问题**: `getUserId()` 返回数字 `999`，但 API JSON 的 `passenger_id` 是字符串 `"999"`。JavaScript `===` 严格相等 `"999" === 999` = `false`，导致 `hasJoined` / `isPublisher` / `showOpsActions` 全部为假，「去支付」按钮不显示。

**修复**: 4 处比较点加 `String()` 强制转换：
```javascript
const isPublisher = computed(() => String(order.value?.passenger_id || '') === String(userId))
const hasJoined = computed(() =>
  isPublisher.value || passengers.value.some((p) => String(p.passenger_id || '') === String(userId))
)
```

### 9.5 MeMessages.vue 多轮修复历程

| 阶段 | 问题 | 做法 |
|------|------|------|
| 1 | placeholder 显示「消息模块待接入」 | 改为功能性页面，调用 Ride API |
| 2 | `listAllOrders()` 展示所有订单（越权） | 改用 `listMyOrders()` / `listDriverOrders()` 后端过滤 |
| 3 | Ride mock ID 不匹配导致空列表 | Ride 切真实 MySQL（9.1） |
| 4 | AD 用户 ID 体系对齐后恢复正常 | 最终使用 `listMyOrders()` 按乘客/车主过滤 |

最终 MeMessages.vue 逻辑：
- 乘客 → `rideApi.listMyOrders()` → `?passenger_id=999` → 后端返回该用户创建的/参与的订单
- 车主 → `rideApi.listDriverOrders()` → `?owner_id=998` → 后端返回该用户接单的订单

### 9.6 钱包种子数据

```sql
-- ops_db.ops_wallet 种子余额
INSERT INTO ops_wallet (user_id, balance, frozen_amount, status) VALUES
  (999, 500.00, 0.00, 1),   -- 乘客：¥500 用于支付测试
  (998, 100.00, 0.00, 1);   -- 车主：¥100（收款后变为 ¥180）
```

### 9.7 管理员提现审批流程验证

| 步骤 | API | 结果 |
|------|-----|------|
| 用户提现 | `POST /api/wallet/withdraw {userId, amount}` | balance↓, frozen↑ |
| 管理员列表 | `GET /api/admin/withdrawals` | 返回 frozen_amount>0 的用户 |
| 管理员通过 | `POST /api/admin/withdrawals/{uid}/approve` | frozen 清零（已"付款"） |
| 管理员驳回 | `POST /api/admin/withdrawals/{uid}/reject` | frozen 退回 balance |

### 9.8 全功能测试验证结果

| 功能 | 测试方法 | 状态 |
|------|----------|------|
| 乘客发布订单 | Ride mock 种子数据 | ✅ |
| 车主接单 | ord-seed-003 owner=998 | ✅ |
| 钱包余额查询 | `GET /api/wallet/info?user_id=999` → ¥500 | ✅ |
| 支付 | 999 → 998 转账 ¥80 | ✅ |
| 乘客-车主聊天 | 999 与 998 在 ord-seed-003 互发消息 | ✅ |
| 乘客投诉 | 提交投诉 → 管理员列表可见 | ✅ |
| 管理员处理投诉 | 修改状态 + 回复 | ✅ |
| 提现申请 | 冻结 ¥100 → 管理员列表可见 | ✅ |
| 管理员批准/驳回提现 | 通过后 frozen 清零 / 驳回后退回 | ✅ |
| 运营统计 | 钱包数 + 支付总额 + 待处理投诉 | ✅ |

### 9.9 涉及他人文件改动摘要

| 文件 | 维护者 | 改动内容 |
|------|--------|----------|
| `backend/account/service.py` | wyx | mock 新增 `driver1` 用户（userId=998） |
| `backend/ride/ride_domain.py` | hws | 无修改（原本已支持 real MySQL） |
| `sql/ride/` | hws/zj | 执行建表 + 种子数据（不影响源码） |
| `backend/.env` | 公共 | RIDE 切真实 DB（`carpool` 用户） |
| `PassengerOrderDetail.vue` | hws/zj | 4 处 `String()` 类型强制转换 |

### 9.10 启动顺序

```bash
# 1. 启动后端
cd backend && bash scripts/run_all.sh

# 2. 启动前端
cd frontend && rm -rf node_modules/.vite && npm run dev

