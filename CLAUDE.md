# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**尾盘选股量化策略回测系统** - 基于 A 股尾盘选股策略的量化投资分析平台，包含数据获取、策略回测、股票分析和 AI 团队分析功能。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI, Backtrader, Akshare, Pandas, SQLAlchemy |
| 前端 | React, Recharts |
| 数据库 | PostgreSQL 15 |
| 认证 | JWT (python-jose) |
| AI | Claude Agent SDK + MiniMax API |

## 项目结构

```
quant_project/
├── backend/
│   ├── main.py              # FastAPI 主服务（认证、API、回测策略）
│   ├── agent_service.py     # AI 团队分析服务
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── App.js         # React 主组件
│   └── package.json
├── data_fetcher.py          # A 股数据获取
├── backtest_strategy.py     # 回测策略
├── .claude/agents/         # AI 智能体配置（7个专业分析师）
├── docker-compose.yml       # PostgreSQL
├── start.sh                # 一键启动
├── start_backend.sh        # 后端启动
└── start_frontend.sh     # 前端启动
```

## 常用命令

### 启动服务

| 命令 | 说明 |
|------|------|
| `./start.sh` | 一键启动前后端 |
| `./start_backend.sh` | 仅启动后端 |
| `./start_frontend.sh` | 仅启动前端 |
| `docker-compose up -d` | 启动 PostgreSQL |

### 手动启动

**后端**:
```bash
cd backend
uv run python main.py
```

**前端**:
```bash
cd frontend
npm install
npm start
```

### 访问地址

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 默认账户

- 用户名: `admin`
- 密码: `cjhyshlm901`

## API 端点

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/login` | 登录获取 Token | 否 |
| POST | `/api/logout` | 登出 | 是 |
| GET | `/api/health` | 健康检查 | 否 |
| POST | `/api/backtest` | 运行回测 | 是 |
| GET | `/api/stocks` | 获取股票列表 | 是 |
| POST | `/api/analyze` | 单股票分析 | 是 |
| POST | `/api/analyze-team` | AI 团队分析 | 是 |

## 策略条件

**尾盘选股筛选条件：
1. 涨幅: 2% - 5%
2. 流通市值: 50亿 - 200亿
3. 换手率: 4% - 10%
4. 量比: > 1
5. 均线多头排列: MA5 > MA10 > MA20

**交易策略：
- 买入: 满足条件当日收盘
- 卖出: T+1 次日开盘

## 核心文件说明

| 文件 | 功能 |
|------|------|
| `backend/main.py` | FastAPI 应用、JWT 认证、API 端点、回测策略 `TrackedMAVolumeStrategy` |
| `backend/agent_service.py` | Claude Agent SDK 集成，7 个 AI 智能体协调 |
| `data_fetcher.py` | 使用 akshare 获取 A 股实时数据、筛选条件股票 |
| `backtest_strategy.py` | Backtrader 策略实现 |
| `frontend/src/App.js` | React UI：登录、回测、股票分析 |

## 环境变量

| 变量 | 默认值 |
|------|--------|
| `DATABASE_URL` | `postgresql://quant_user:quant_password@localhost:5432/quant_db` |

## 注意事项

- 后端将 `sys.path` 加入了父目录，以导入 `data_fetcher.py`
- JWT Token 有效期 24 小时
- 回测数据缓存于 `data/` 目录
