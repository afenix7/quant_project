# 尾盘选股量化策略项目

基于掘金文章的尾盘选股策略，使用akshare获取股票数据，backtrader进行回测。

## 策略条件

1. **涨幅**: 2% - 5%
2. **流通市值**: 50亿 - 200亿
3. **换手率**: 4% - 10%
4. **量比**: > 1
5. **均线多头排列**: 5日均线 > 10日均线 > 20日均线

## 项目结构

```
quant_project/
├── data_fetcher.py       # 数据获取脚本（akshare）
├── backtest_strategy.py  # 回测策略（backtrader）
├── requirements.txt      # 依赖
└── data/                 # 数据目录
```

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 1. 获取股票数据
```bash
python data_fetcher.py
```

### 2. 运行回测
```bash
python backtest_strategy.py
```

## 策略逻辑

**买入信号:**
- 收盘价 > 5日均线 > 10日均线 > 20日均线
- 涨幅2%-5%，量比>1

**卖出信号:**
- 次日开盘卖出（T+1）
