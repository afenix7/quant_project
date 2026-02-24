# TradingAgents 团队使用指南

## 团队概述

这是一个基于 TradingAgents 框架的多智能体金融交易分析团队，模拟真实交易公司的运作方式。

## 团队架构

```
┌─────────────────────────────────────────────────────────┐
│                   Team Leader (协调者)                   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │          Analyst Team (分析师团队)               │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │ 基本面   │ │ 技术面   │ │ 情绪面   │      │   │
│  │  │  分析师  │ │  分析师  │ │  分析师  │      │   │
│  │  └──────────┘ └──────────┘ └──────────┘      │   │
│  │  ┌──────────┐                                     │   │
│  │  │ 新闻     │                                     │   │
│  │  │  分析师  │                                     │   │
│  │  └──────────┘                                     │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Researcher Team (研究员团队)              │   │
│  │  ┌──────────────┐     ┌──────────────┐        │   │
│  │  │  多头研究员  │     │  空头研究员  │        │   │
│  │  └──────────────┘     └──────────────┘        │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Risk Manager (风险管理员)               │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 代理角色说明

| 代理 | 文件 | 职责 |
|-----|------|------|
| Team Leader | `team-leader.md` | 整体协调、任务分配、决策汇总 |
| Fundamentals Analyst | `fundamentals-analyst.md` | 财务分析、估值、机构观点 |
| Technical Analyst | `technical-analyst.md` | K线分析、技术指标、趋势判断 |
| Sentiment Analyst | `sentiment-analyst.md` | 情绪周期、舆情分析 |
| News Analyst | `news-analyst.md` | 新闻解读、宏观分析 |
| Bullish Researcher | `bullish-researcher.md` | 挖掘利好、构建看涨逻辑 |
| Bearish Researcher | `bearish-researcher.md` | 挖掘风险、构建看跌逻辑 |
| Risk Manager | `risk-manager.md` | 风险评估、止损设置、仓位管理 |

## 工作流程

### 标准分析流程

```
1. 用户请求分析某只股票
   ↓
2. Team Leader 接收请求，分解任务
   ↓
3. 并行执行：
   ├─ Fundamentals Analyst → 基本面分析报告
   ├─ Technical Analyst → 技术分析报告
   ├─ Sentiment Analyst → 情绪分析报告
   └─ News Analyst → 新闻分析简报
   ↓
4. Bullish Researcher 基于以上报告 → 多头研究报告
   ↓
5. Bearish Researcher 基于以上报告 → 空头研究报告
   ↓
6. Risk Manager 综合所有报告 → 风险管理报告
   ↓
7. Team Leader 汇总所有报告 → 最终综合分析报告
```

## 目录结构

```
finance-analysis/
├── .claude/
│   ├── skills/              # 已有的 skills
│   │   ├── fundamental-analysis/
│   │   ├── technical-analysis/
│   │   └── sentiment-analysis/
│   └── agents/              # 代理系统提示词（本目录）
│       ├── README.md         # 本文件
│       ├── team-leader.md
│       ├── fundamentals-analyst.md
│       ├── technical-analyst.md
│       ├── sentiment-analyst.md
│       ├── news-analyst.md
│       ├── bullish-researcher.md
│       ├── bearish-researcher.md
│       ├── risk-manager.md
│       └── REPORT_TEMPLATE.md  # 综合报告模板
├── data/                   # 数据存储
│   ├── {代码}-kline-{日期}.csv
│   └── {代码}-comments-{日期}.json
└── reports/                # 报告输出
    ├── {股票名称}基本面_{YYYYMMDD}.md
    ├── {股票名称}技术分析_{YYYYMMDD}.md
    ├── {股票名称}情绪分析报告_{YYYYMMDD}.md
    └── {股票名称}_综合分析_{YYYYMMDD}.md  # 最终报告
```

## 使用示例

### 分析一只股票

1. **启动分析**
   ```
   Team Leader，分析一下股票 300666 江丰电子
   ```

2. **各代理并行工作**
   - Fundamentals Analyst 使用 `fundamental-analysis` skill 生成基本面报告
   - Technical Analyst 使用 `technical-analysis` skill 生成技术分析报告
   - Sentiment Analyst 使用 `sentiment-analysis` skill 生成情绪分析报告
   - News Analyst 使用 `web_search` 搜索最新新闻

3. **研究员辩论**
   - Bullish Researcher 整理所有利好因素
   - Bearish Researcher 整理所有风险因素

4. **风险管理**
   - Risk Manager 评估风险、设置止损、建议仓位

5. **最终报告**
   - Team Leader 汇总生成最终综合报告

## 注意事项

1. **投资风险提示**：所有分析仅供参考，不构成投资建议
2. **数据时效性**：注意数据的时间点，优先使用最新数据
3. **客观性**：保持中立，多空双方观点都要重视
4. **风险优先**：任何决策都要先考虑风险控制
