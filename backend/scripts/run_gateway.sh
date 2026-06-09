#!/bin/bash
# 启动网关服务 (端口8000)
cd "$(dirname "$0")/../.." || exit 1
python -m uvicorn backend.gateway.main:app --reload --port 8000 --host 0.0.0.0
