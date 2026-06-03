# 后端结构说明

当前后端采用 FastAPI 多服务结构：账号域、订单车辆域、交易运营域分别独立运行，再由网关统一暴露 `/api` 前缀。开发时既可以只启动单个域服务，也可以通过脚本一次启动全部服务。

## 服务与端口

| 模块 | 默认端口 | 主要职责 |
| --- | --- | --- |
| `backend/account` | `8001` | 注册、登录、管理员登录、用户资料、车主身份认证、用户状态和信誉分 |
| `backend/ride` | `8002` | 拼车订单、接单、取消、完成、车辆登记、车辆认证审核 |
| `backend/ops` | `8003` | 支付、钱包、聊天、投诉、管理员运营统计和提现审核 |
| `backend/gateway` | `8000` | 统一入口，按路径转发到三个领域服务 |

前端默认访问 `http://localhost:8000/api`，开发代理配置位于 `frontend/vite.config.js`。

## 目录说明

### `account/`

- `account_domain.py`：账号域 FastAPI 入口、请求模型和路由定义。
- `service.py`：账号域业务逻辑，包含 Mock/数据库两套实现。
- `account_db.py`：`account_db` MySQL 连接管理。

主要接口包括：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/admin/login`
- `GET /api/users/profile/{user_id}`
- `POST /api/users/driver/apply/{user_id}`
- `GET /api/users/admin/users`
- `POST /api/users/admin/update-status`
- `POST /api/users/score/update`

### `ride/`

- `service.py`：订单车辆域 FastAPI 入口和 Header 鉴权约束。
- `ride_domain.py`：订单状态机、乘客拼单、车主接单、车辆和车辆认证业务逻辑。
- `ride_db.py`：`ride_db` MySQL 连接管理。

当前产品规则：

- 数据库模式必须由前端传入 `X-User-Id`；不会自动兜底到 Mock 用户。
- 车主侧车辆和接单接口需要 `X-Owner-Verified: true`。
- 前端隐藏 `cancelled` 订单；后端仍保留取消状态，便于审计和统计扩展。
- 新增车辆时一次性填写车辆认证资料，提交后等待管理员审核；审核前用户只能撤回申请。

### `ops/`

- `service.py`：交易运营域 FastAPI 入口。
- `ops_domain.py`：支付、钱包、聊天、投诉、管理员统计和提现审核业务逻辑。
- `ops_db.py`：`ops_db` MySQL 连接管理。

当前前端主要使用：

- `POST /api/payments/orders/{order_id}/pay`
- `GET /api/wallet/info`
- `POST /api/wallet/withdraw`
- `GET /api/wallet/logs`
- `POST /api/chat/messages`
- `GET /api/chat/messages`
- `PUT /api/chat/messages/read`
- `POST /api/complaints`
- `GET /api/admin/complaints`
- `PUT /api/admin/complaints/{ticket_id}`

### `gateway/`

- `main.py`：统一入口服务。开发时建议前端只连网关，避免每个页面单独处理三个服务地址。

### `common/`

- `config.py`：统一读取 `backend/.env` 中的服务地址、数据库参数和 Mock 开关。
- `domain_models.py`：跨领域共享的轻量模型和约束。

### `scripts/`

- `bootstrap_env.ps1`：从 `.env.example` 生成 `backend/.env`。
- `run_services.ps1`：启动账号域、订单车辆域、交易运营域和网关。
- `run_account.ps1` / `run_ride.ps1` / `run_ops.ps1` / `run_gateway.ps1`：单服务启动脚本。
- `smoke_test_ops.ps1`：运营域基础冒烟测试。

## 启动建议

在项目根目录执行：

```powershell
cd backend
.\scripts\bootstrap_env.ps1
.\scripts\run_services.ps1
```

单独启动某个服务时，也建议从项目根目录或 `backend` 目录使用模块路径启动，例如：

```powershell
python -m uvicorn backend.gateway.main:app --reload --port 8000
```

## Mock 与数据库模式

三个领域分别由 `.env` 中的开关控制：

```env
ACCOUNT_USE_MOCK=true
RIDE_USE_MOCK=true
OPS_USE_MOCK=true
```

- `true`：使用服务内置 Mock 数据，适合无数据库联调。
- `false`：连接对应 MySQL 数据库，读取真实数据。
- 数据库模式不会自动混入 Mock 数据。演示数据需要显式执行 `sql/*` 下的可选种子脚本。
