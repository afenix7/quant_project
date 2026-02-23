#!/bin/bash

# 仅启动前端服务

echo "启动尾盘选股策略回测系统 - 前端"

echo ""
echo "===================================="
echo "启动前端服务..."
echo "===================================="

cd frontend

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

npm start
