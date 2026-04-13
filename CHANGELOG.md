# CHANGELOG

所有功能域的重要变更记录在此文件。  
格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

---

## [未发布] — 功能域2 初步完成

**分支**: `hws-ride-dev`  
**负责人**: hws、zj  
**日期**: 2026-04-14

### 新增

#### 后端（`backend/ride/`）
- 实现订单全生命周期的 10 个接口（发布、搜索、列表、详情、修改、取消、拼单、接单、完成、查车辆）
- 订单状态机：`published → locked → completed`，支持 `full`（已满员）和 `cancelled`
- 标签功能：发布时可附加多个标签，搜索时支持多标签全匹配筛选
- 管理员权限：通过 `X-User-Role: admin` header，管理员可强制取消任意未完成订单
- Mock/MySQL 双模式：`RIDE_USE_MOCK=true`（默认）走内存 Mock，改为 `false` 走真实数据库
- Mock 种子数据：4 条订单覆盖 published/locked/completed 状态，1 辆测试车辆

#### 前端（`frontend/src/`）
- 新增 `api/ride.js`：统一封装全部接口调用，导出 `STATUS_MAP`、`AVAILABLE_TAGS`、`LOCATION_SUGGESTIONS`、`calcPerPersonPrice`
- 乘客端：首页、发布订单、搜索订单、我的订单（含状态 tab）、订单详情（含拼单/取消）
- 车主端：首页（含待接单数实时统计）、可接订单列表（含接单弹窗选车辆）、我的接单（含标记完成）
- 管理员端：订单管理（含关键词搜索、状态筛选、强制取消）

#### 文档
- `docs/apis/ride.md`：完整 API 契约（10 个接口的请求/响应/错误码）
- `docs/功能域2-开发说明.md`：面向全体组员的开发说明（界面介绍、启动方式、对接约定、测试流程、FAQ）

### 修改（相对原框架骨架）

- `backend/ride/service.py`：原仅有 4 个无参数骨架接口，重写为完整的 10 个带校验接口
- `backend/ride/ride_domain.py`：原字段为驼峰命名、仅1条种子数据，重写为下划线命名 + 完整业务逻辑
- `backend/gateway/main.py`：转发端口从 8002 改为 7002（整体端口段 8000-8003 → 7000-7003）
- `sql/ride/001_init.sql`：字段与 ride_domain.py 对齐
- `frontend/vite.config.js`：代理从 8000 改为 7000

### 修复（原框架存在的问题）

- `frontend/src/layouts/AppLayout.vue`：`session` 使用 `computed(() => getSession())` 无响应式依赖，切换角色后 Tab 栏不刷新。改为 `ref(getSession())` 并在切换/登出时显式更新。

### 配置变更

- 端口统一改为 `7000-7003`（原 `8000-8003`），原因：Windows Docker Desktop 保留了 8000-8003 端口段，导致启动报错
- `backend/.env` 新增 `RIDE_USE_MOCK=true`、`RIDE_DB_PORT=7002`
- `frontend/.env` 新增 `VITE_API_BASE=http://localhost:7000`

---

> 其他功能域的变更由对应负责人补充到本文件。
