# Skill: technical-analysis

金融产品技术分析。使用 AkShare 获取股票、ETF、基金、加密币的 K 线数据，通过 Python 脚本计算技术指标，生成 Markdown 格式的技术分析报告。

**注意**: 基本面分析请使用 `fundamental-analysis` skill。

## When to Use

- 用户要求分析股票、ETF、基金、加密币的技术面
- 需要获取 K 线数据并生成技术分析报告
- 要求将报告和数据保存到本地

## Prerequisites

确保已安装 akshare:

```bash
pip install akshare pandas numpy
```

## 数据目录

```
~/uni-web/frontend-html/finance-analysis/
├── data/                      # K线数据存储
│   └── {代码}-kline-{日期}.csv
├── reports/                   # 技术分析报告
│   └── {股票名称}技术分析_{YYYYMMDD}.md
└── task_plan.md
```

## Skill 脚本

脚本位置: `~/uni-web/frontend-html/finance-analysis/.claude/skills/`

| 脚本 | 说明 |
|------|------|
| data_fetcher.py | 数据获取脚本 |
| technical_indicators.py | 技术指标计算脚本 |

## 数据获取脚本 (data_fetcher.py)

### 核心函数

```python
from data_fetcher import fetch_data, save_data, load_data

# 获取数据
df = fetch_data("300666", start_date="20250101", end_date="20250218")

# 保存数据 (文件名格式: 代码-kline-日期.csv)
save_data(df, "300666-kline-20250218.csv")

# 加载数据
df = load_data("300666-kline-20250218.csv")
```

### 保存数据命名规则

```
{股票代码}-kline-{YYYYMMDD}.csv
```

例如: `300666-kline-20250218.csv`

## 技术指标脚本 (technical_indicators.py)

### 使用方法

```bash
# 基本用法
python technical_indicators.py <股票代码> [股票名称] [天数]

# 示例
python technical_indicators.py 300666 江丰电子 180
python technical_indicators.py 600519 贵州茅台
python technical_indicators.py 0100.HK MiniMax
```

### 计算的指标

| 指标 | 说明 | 函数 |
|------|------|------|
| MA5/10/20/60 | 移动平均线 | calculate_ma() |
| RSI | 相对强弱指标 | calculate_rsi() |
| MACD | 指数平滑异同移动平均线 | calculate_macd() |
| 布林带 | Bollinger Bands | calculate_bollinger_bands() |
| 量比 | Volume Ratio | calculate_volume_ratio() |
| BIAS6/12/24 | 乖离率 | calculate_bias() |

### 在 Python 中使用

```python
from technical_indicators import calculate_indicators, analyze_signals
from data_fetcher import fetch_data

# 获取数据
df = fetch_data("300666", start_date="20250101", end_date="20250218")

# 计算技术指标
df = calculate_indicators(df)

# 分析信号
signals = analyze_signals(df)
print(signals)
```

### 输出信号

```python
{
    'ma_signal': '金叉 (短期看多)',
    'ma_mid': '中期看多',
    'rsi': '51.8 - 中性区域',
    'macd': '金叉 (买入信号)',
    'bb': '中性',
    'volume': '成交量放大'
}
```

## 支持的金融产品类型

| 类型 | 市场 | 代码示例 | AkShare 函数 |
|------|------|----------|-------------|
| A股 | 上海/深圳 | 600519, 300666 | stock_zh_a_hist |
| 港股 | 香港联交所 | 0100.HK, 00700.HK | stock_hk_daily |
| 美股 | 纽约/纳斯达克 | AAPL, MSFT | stock_us_hist |
| ETF | A股/港股 | 510300, 02837.HK | fund_etf_hist_em |
| 加密币 | 交易所 | BTC, ETH | crypto_hist |

## 技术分析指标说明

### 移动平均线 (MA)

| 指标 | 说明 | 交易信号 |
|------|------|----------|
| MA5 | 5日均线 | 短期趋势 |
| MA10 | 10日均线 | 中期趋势 |
| MA20 | 20日均线 | 中长期趋势 |

**金叉**: MA5 > MA10 → 买入信号
**死叉**: MA5 < MA10 → 卖出信号

### RSI 相对强弱指标

| RSI值 | 信号 |
|-------|------|
| >70 | 超买区域，可能回调 |
| <30 | 超卖区域，可能反弹 |
| 50 | 多空平衡点 |

### MACD

| 信号 | 说明 |
|------|------|
| DIF > DEA | 多头排列 |
| DIF < DEA | 空头排列 |
| 金叉 | DIF上穿DEA，买入信号 |
| 死叉 | DIF下穿DEA，卖出信号 |

### 布林带

| 位置 | 信号 |
|------|------|
| 价格 > 上轨 | 超买 |
| 价格 < 下轨 | 超卖 |
| 布林带收窄 | 波动率降低，可能突破 |

### 乖离率 (BIAS)

乖离率是衡量股价偏离均线程度的指标，反映股价在波动过程中与移动平均线的偏离程度。

**公式**: `BIAS = (收盘价 - MA) / MA × 100%`

| 指标 | 说明 | 超买阈值 | 超卖阈值 |
|------|------|---------|---------|
| BIAS6 | 6日乖离率 | >10% | <-10% |
| BIAS12 | 12日乖离率 | >15% | <-15% |
| BIAS24 | 24日乖离率 | >20% | <-20% |

**信号说明**:
- BIAS > 0: 股价在均线上方，多头市场
- BIAS < 0: 股价在均线下方，空头市场
- BIAS 过大: 超买，可能回调
- BIAS 过小: 超卖，可能反弹

## 报告生成

### 输出目录

```
~/uni-web/frontend-html/finance-analysis/reports/
```

### 文件命名规则

```
{股票名称}技术分析_{YYYYMMDD}.md
```

### 使用脚本生成报告

```bash
cd ~/uni-web/frontend-html/finance-analysis/.claude/skills
python technical_indicators.py 300666 江丰电子
```

报告将输出到终端，可重定向到文件：

```bash
python technical_indicators.py 300666 江丰电子 > ../../reports/江丰电子技术分析_20250218.md
```

## 注意事项

1. **数据获取**: 每次通过 API 实时获取最新数据
2. **数据延迟**: 免费数据源可能有延迟
3. **投资风险**: 技术分析仅供参考，不构成投资建议

## 相关工具

- fundamental-analysis: 基本面分析
- ddgr: 搜索最新新闻
- webfetch: 获取网页内容
