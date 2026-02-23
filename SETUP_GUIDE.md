# 安装和使用指南

## 前置条件

- Python 3.8+
- Node.js 16+
- npm 或 yarn

## 安装步骤

### 1. 安装 Python 依赖

```bash
# 在项目根目录运行
uv pip install fastapi uvicorn pydantic
```

或者使用 pip:

```bash
pip install fastapi uvicorn pydantic
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

## 启动服务

### 启动后端

```bash
cd backend
uv run python main.py
```

后端将运行在 http://localhost:8000

### 启动前端（新终端）

```bash
cd frontend
npm start
```

前端将运行在 http://localhost:3000

## 使用说明

1. 打开浏览器访问 http://localhost:3000
2. 设置回测参数（初始资金、股票数量等）
3. 点击"开始回测"按钮
4. 等待回测完成，查看结果图表和指标

## 项目文件说明

```
quant_project/
├── backend/
│   └── main.py                 # FastAPI 后端服务
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js            # 主组件
│   │   ├── index.js          # 入口文件
│   │   └── index.css         # 样式文件
│   └── package.json          # 前端依赖
├── data_fetcher.py             # 数据获取模块
├── backtest_strategy.py        # 回测策略模块
├── start_backend.sh            # 后端启动脚本
├── start_frontend.sh           # 前端启动脚本
└── README_WEB.md             # 项目说明文档
```
