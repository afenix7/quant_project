# 金融分析团队使用指南

## 快速启动

在 opencode 中直接发送分析请求：

```
分析股票 603893 瑞芯微
```

或

```
Team Leader，分析一下股票 603893
```

## 分析流程

团队会自动执行以下步骤：

1. **基本面分析** - 财务数据、估值、机构评级
2. **技术分析** - K线、技术指标、趋势
3. **情绪分析** - 市场情绪、舆情
4. **新闻分析** - 最新消息、公告
5. **多头研究** - 利好因素
6. **空头研究** - 风险因素
7. **风险评估** - 风险等级、仓位建议
8. **最终报告** - 综合分析、投资建议

## 命令行工具

### Shell 脚本
```bash
cd ~/uni-web/frontend-html/finance-analysis
./stock-analysis.sh 603893 瑞芯微
```

### Python 脚本
```bash
cd ~/uni-web/frontend-html/finance-analysis
python stock_analysis.py 603893 瑞芯微
```

## 支持的股票类型

| 类型 | 代码示例 |
|------|----------|
| A股上证 | 603893 (瑞芯微) |
| A股深证 | 300666 (江丰电子) |
| 港股 | 00700.HK (腾讯) |
| 美股 | AAPL (苹果) |

## 输出报告

分析报告保存位置：
- `~/uni-web/frontend-html/finance-analysis/reports/`

报告格式：
- `{股票名称}基本面_YYYYMMDD.md`
- `{股票名称}技术分析_YYYYMMDD.md`
- `{股票名称}_综合分析_YYYYMMDD.md`
