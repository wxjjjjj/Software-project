# Backend结构说明

- account/: 账号域（注册/登录/认证）
- ride/: 订单车辆域（发单/接单/状态流转）
- ops/: 交易运营域（支付/钱包/反馈/后台运营列表）
- gateway/: 网关层（统一 /api 转发）
- common/: 公共配置
- scripts/: 启动、自测、环境初始化脚本

## 具体内容

### account/
- account_db.py: account_db 连接管理
- account_domain.py: 账号域业务逻辑
- service.py: 账号域 FastAPI 入口（8001）

### ride
- ride_db.py: ride_db 连接管理
- ride_domain.py: 订单车辆域业务逻辑
- service.py: 订单域 FastAPI 入口（8002）

### ops
- ops_db.py: ops_db 连接管理
- ops_domain.py: 交易运营域业务逻辑
- service.py: 运营域 FastAPI 入口（8003）

### gateway
- main.py: 网关入口（8000），按前缀转发到三域服务

### common
- config.py: 统一读取 .env（服务地址、DB 参数、mock 开关）
- domain_models.py: 领域模型与规则（跨域共享）

### scripts
- bootstrap_env.ps1: 从 .env.example 生成 .env
- run_services.ps1: 一键启动 8001/8002/8003/8000
- run_account.ps1 / run_ride.ps1 / run_ops.ps1 / run_gateway.ps1: 单服务启动
- smoke_test_ops.ps1: 运营域接口冒烟测试

## 代码修改内容

## 【当前各个目录下已经给了一些示例文件，可以按照自己的需要增加/删除，不用跟我说】
- 账号域wyx只改 account/* 与 docs/apis/account.md、sql/account/*
- 订单域hws、zj只改 ride/* 与 docs/apis/ride.md、sql/ride/*
- 运营域yzr只改 ops/* 与 docs/apis/ops.md、sql/ops/*
- **wxj：gateway/*、common/***

## 导入与启动
- Python 导入统一使用 backend.* 包路径
  - 示例: from backend.common.config import RIDE_USE_MOCK
- 启动脚本统一从项目根运行模块
  - 示例: python -m uvicorn backend.gateway.main:app --reload --port 8000

## 快速启动
在项目根目录执行：

1. cd backend
2. ./scripts/bootstrap_env.ps1
3. ./scripts/run_services.ps1

可选自测：（冒烟测试）
1. ./scripts/smoke_test_ops.ps1
