#!/bin/bash
# 启动运营域服务 (端口8003)
cd "$(dirname "$0")/../.." || exit 1
python -m uvicorn backend.ops.service:app --reload --port 8003 --host 0.0.0.0
