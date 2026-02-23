#!/bin/bash

# 仅启动后端服务

echo "启动尾盘选股策略回测系统 - 后端"

# 创建必要的目录
mkdir -p data

echo ""
echo "===================================="
echo "启动后端服务..."
echo "===================================="

cd backend

# 检查 uv 可用
if command -v uv &> /dev/null; then
    echo "使用 uv 启动后端..."
    uv run python main.py
else
    echo "使用 python 启动后端..."
    python main.py
fi
