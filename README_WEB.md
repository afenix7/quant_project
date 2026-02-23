# 尾盘选股策略回测系统

基于 FastAPI + React 的尾盘选股策略回测可视化系统。

## 项目结构

```
quant_project/
├── backend/              # FastAPI 后端
│   ├── main.py        # 后端服务主文件
│   └── requirements.txt
├── frontend/           # React 前端
│   ├── public/
│   ├── src/
│   │   ├── App.js     # 主组件
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
├── data_fetcher.py      # 数据获取
├── backtest_strategy.py # 回测策略
└── start.sh          # 一键启动脚本
├── start_backend.sh  # 仅启动后端
└── start_frontend.sh # 仅启动前端
```

## 功能特性

1. **回测参数配置
   - 初始资金设置
   - 股票数量限制
   - 数据刷新控制

2. **回测指标展示
   - 初始资金/最终资金
   - 总收益率
   - 夏普比率
   - 最大回撤
   - 年化收益率
   - 交易统计

3. **图表可视化**
   - 策略 vs 基准净值曲线
   - 股票走势图（带买卖点标记）
   - 交易记录表格

## 快速开始

### 方式一：一键启动（推荐）

```bash
./start.sh
```

### 方式二：分别启动

**启动后端：
```bash
./start_backend.sh
```

**启动前端（新终端）：
```bash
./start_frontend.sh
```

### 方式三：手动启动

**后端：
```bash
cd backend
uv run python main.py
```

**前端：**
```bash
cd frontend
npm install  # 首次运行需要
npm start
```

## 访问地址

- **前端页面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## API 接口

### POST /api/backtest

运行回测

**请求体**:
```json
{
  "initial_cash": 100000,
  "force_refresh": false,
  "stock_limit": 10
}
```

**响应**:
```json
{
  "success": true,
  "message": "回测完成",
  "initial_cash": 100000,
  "final_value": 142964.79,
  "total_return": 42.96,
  "sharpe_ratio": 0.15,
  "max_drawdown": 36.27,
  "annual_return": 3.22,
  "total_trades": 56,
  "winning_trades": 32,
  "losing_trades": 15,
  "trades": [...],
  "equity_curve": [...],
  "stock_data": {...}
}
```

### GET /api/health

健康检查

### GET /api/stocks

获取筛选后的股票列表

## 技术栈

- **后端**: FastAPI, Backtrader, Akshare, Pandas
- **前端**: React, Recharts
