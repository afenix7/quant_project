# Findings & Decisions

## Requirements

- 金融产品技术分析：股票、ETF、基金、加密币
- 使用 AkShare 获取数据
- 配合搜索工具获取最新新闻
- 生成 Markdown 格式的技术分析报告
- 报告保存在 ~/uni-web/frontend-html/finance-analysis/

## Research Findings

### AkShare 数据支持

| 类型 | 函数 | 说明 |
|------|------|------|
| A股日K | stock_zh_a_hist | 获取A股历史K线 |
| 港股日K | stock_hk_daily | 获取港股历史K线 |
| 美股数据 | stock_us_hist | 获取美股历史K线 |
| ETF数据 | fund_etf_hist_em | 获取ETF历史数据 |
| 加密币 | crypto_hist | 获取加密货币历史数据 |
| 实时行情 | stock_zh_a_spot_em | A股实时行情 |

### 技术指标

- 移动平均线 (MA5, MA10, MA20, MA60)
- RSI 相对强弱指标
- MACD 指数平滑异同移动平均线
- 布林带 (Bollinger Bands)
- 成交量分析

### 报告模板

- 行情概览
- 技术分析（均线、成交量、RSI、MACD、布林带）
- 基本面分析（最新新闻、机构观点、财务数据）
- 综合判断与操作建议

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| 使用 finance-analysis skill | 标准化分析流程 |
| 报告输出到 finance-analysis 子站 | 便于管理和展示 |
| 文件命名：标题_YYYYMMDD.md | 便于检索和归档 |

## Issues Encountered

| Issue | Resolution |
|-------|------------|

## Resources

- AkShare 文档
- ddgr 搜索工具
- webfetch 网页抓取

## Visual/Browser Findings

- 
