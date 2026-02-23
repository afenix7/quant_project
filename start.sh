#!/bin/bash

# 启动脚本 - 启动后端和前端

echo "启动尾盘选股策略回测系统"

# 创建必要的目录
mkdir -p data

echo "
===================================="
echo "启动后端服务..."
echo "===================================="

# 检查 uv 可用
if command -v uv &> /dev/null; then
    echo "使用 uv 启动后端..."
    cd backend && uv run python main.py &
    BACKEND_PID=$!
else
    echo "使用 python 启动后端..."
    cd backend && python main.py &
    BACKEND_PID=$!
fi

cd ..

echo "后端 PID: $BACKEND_PID"
echo "后端服务运行在 http://localhost:8000"

echo ""
echo "===================================="
echo "启动前端服务..."
echo "===================================="

sleep 3

cd frontend
if [ ! -d "node_modules" ]; then
    echo "node_modules 已存在"
else
    echo "安装前端依赖..."
    npm install
fi

npm start &
FRONTEND_PID=$!

echo "前端 PID: $FRONTEND_PID"
echo "前端服务运行在 http://localhost:3000"

cd ..

echo ""
echo "===================================="
echo "系统启动完成！"
echo "后端 API: http://localhost:8000"
echo "前端页面: http://localhost:3000"
echo "===================================="
echo ""
echo "按 Ctrl+C 停止服务"

# 等待用户中断
wait $BACKEND_PID $FRONTEND_PID
