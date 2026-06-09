#!/bin/bash
# 一键启动所有服务
cd "$(dirname "$0")/../.." || exit 1
echo "启动 账号域 (8001) ..."
python -m uvicorn backend.account.account_domain:app --reload --port 8001 --host 0.0.0.0 &
echo "启动 订单域 (8002) ..."
python -m uvicorn backend.ride.service:app --reload --port 8002 --host 0.0.0.0 &
echo "启动 运营域 (8003) ..."
python -m uvicorn backend.ops.service:app --reload --port 8003 --host 0.0.0.0 &
echo "启动 网关 (8000) ..."
python -m uvicorn backend.gateway.main:app --reload --port 8000 --host 0.0.0.0 &
wait
