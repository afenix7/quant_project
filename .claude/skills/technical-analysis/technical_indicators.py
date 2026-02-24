#!/usr/bin/env python3
"""
技术指标计算脚本
计算股票的 RSI、MACD、布林带等技术指标
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# 添加当前目录到 path 以便导入 data_fetcher
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from data_fetcher import fetch_data, save_data, DATA_DIR


def load_kline_data(filename: str) -> pd.DataFrame:
    """
    加载 K 线数据

    Args:
        filename: 数据文件名

    Returns:
        DataFrame
    """
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"数据文件不存在: {filepath}")

    df = pd.read_csv(filepath)

    # 统一列名
    if '日期' in df.columns:
        df['date'] = pd.to_datetime(df['日期'])
    elif 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date'])

    # 统一收盘价列名
    if '收盘' in df.columns:
        df['close'] = df['收盘']
    elif 'Close' in df.columns:
        df['close'] = df['Close']

    return df


def calculate_ma(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
    """
    计算移动平均线

    Args:
        df: K线数据
        periods: 周期列表，默认 [5, 10, 20, 60]

    Returns:
        添加了 MA 列的 DataFrame
    """
    if periods is None:
        periods = [5, 10, 20, 60]

    for period in periods:
        df[f'MA{period}'] = df['close'].rolling(window=period).mean()

    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    计算 RSI 相对强弱指标

    Formula:
    RSI = 100 - (100 / (1 + RS))
    RS = 平均涨幅 / 平均跌幅

    Args:
        df: K线数据
        period: RSI 周期，默认 14

    Returns:
        添加了 RSI 列的 DataFrame
    """
    delta = df['close'].diff()

    # 分离涨跌
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    # 计算平均涨跌幅 (使用 EMA 方式)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()

    # 计算 RS 和 RSI
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    计算 MACD 指数平滑异同移动平均线

    Formula:
    DIF = EMA(close, 12) - EMA(close, 26)
    DEA = EMA(DIF, 9)
    MACD = (DIF - DEA) * 2

    Args:
        df: K线数据
        fast: 快线周期，默认 12
        slow: 慢线周期，默认 26
        signal: 信号线周期，默认 9

    Returns:
        添加了 DIF, DEA, MACD 列的 DataFrame
    """
    # 计算 EMA
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

    # DIF (MACD Line)
    df['DIF'] = ema_fast - ema_slow

    # DEA (Signal Line)
    df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()

    # MACD Histogram
    df['MACD'] = (df['DIF'] - df['DEA']) * 2

    return df


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """
    计算布林带

    Formula:
    Middle Band = MA(close, 20)
    Upper Band = MA + 2 * StdDev
    Lower Band = MA - 2 * StdDev

    Args:
        df: K线数据
        period: 周期，默认 20
        std_dev: 标准差倍数，默认 2

    Returns:
        添加了 BB_UPPER, BB_MIDDLE, BB_LOWER 列的 DataFrame
    """
    df['BB_MIDDLE'] = df['close'].rolling(window=period).mean()
    df['BB_STD'] = df['close'].rolling(window=period).std()

    df['BB_UPPER'] = df['BB_MIDDLE'] + std_dev * df['BB_STD']
    df['BB_LOWER'] = df['BB_MIDDLE'] - std_dev * df['BB_STD']

    # 布林带位置 (0-100%)
    df['BB_POSITION'] = (df['close'] - df['BB_LOWER']) / (df['BB_UPPER'] - df['BB_LOWER']) * 100

    return df


def calculate_volume_ratio(df: pd.DataFrame, period: int = 5) -> pd.DataFrame:
    """
    计算量比

    Formula:
    量比 = 近5日平均成交量 / 今日成交量

    Args:
        df: K线数据
        period: 周期，默认 5

    Returns:
        添加了 VOL_RATIO 列的 DataFrame
    """
    # 成交量列名适配
    if '成交量' in df.columns:
        df['volume'] = df['成交量']
    elif 'Volume' in df.columns:
        df['volume'] = df['Volume']

    df['VOL_MA'] = df['volume'].rolling(window=period).mean()
    df['VOL_RATIO'] = df['volume'] / df['VOL_MA']

    return df


def calculate_bias(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
    """
    计算乖离率（BIAS）

    Formula:
    BIAS = (收盘价 - MA) / MA * 100%

    Args:
        df: K线数据
        periods: 周期列表，默认 [6, 12, 24]

    Returns:
        添加了 BIAS 列的 DataFrame
    """
    if periods is None:
        periods = [6, 12, 24]

    for period in periods:
        ma = df['close'].rolling(window=period).mean()
        df[f'BIAS{period}'] = (df['close'] - ma) / ma * 100

    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    统一列名

    Args:
        df: 原始数据

    Returns:
        列名统一后的 DataFrame
    """
    df = df.copy()

    if '日期' in df.columns:
        df['date'] = pd.to_datetime(df['日期'])
    elif 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date'])

    if '收盘' in df.columns:
        df['close'] = df['收盘']
    elif 'Close' in df.columns:
        df['close'] = df['Close']

    if '成交量' in df.columns:
        df['volume'] = df['成交量']
    elif 'Volume' in df.columns:
        df['volume'] = df['Volume']

    return df


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算所有技术指标

    Args:
        df: K线数据

    Returns:
        添加了所有技术指标的 DataFrame
    """
    df = normalize_columns(df)
    df = calculate_ma(df)
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_bollinger_bands(df)
    df = calculate_volume_ratio(df)
    df = calculate_bias(df)

    return df


def analyze_signals(df: pd.DataFrame) -> dict:
    """
    分析技术信号

    Args:
        df: 包含技术指标的数据

    Returns:
        信号字典
    """
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    signals = {}

    # 均线信号
    ma5 = latest.get('MA5', 0)
    ma10 = latest.get('MA10', 0)
    ma20 = latest.get('MA20', 0)

    if ma5 > ma10:
        signals['ma_signal'] = '金叉 (短期看多)'
    elif ma5 < ma10:
        signals['ma_signal'] = '死叉 (短期看空)'
    else:
        signals['ma_signal'] = '均线粘合'

    if ma10 > ma20:
        signals['ma_mid'] = '中期看多'
    else:
        signals['ma_mid'] = '中期看空'

    # RSI 信号
    rsi = latest.get('RSI', 50)
    if rsi > 70:
        signals['rsi'] = f'{rsi:.1f} - 超买区域'
    elif rsi < 30:
        signals['rsi'] = f'{rsi:.1f} - 超卖区域'
    else:
        signals['rsi'] = f'{rsi:.1f} - 中性区域'

    # MACD 信号
    dif = latest.get('DIF', 0)
    dea = latest.get('DEA', 0)
    prev_dif = prev.get('DIF', 0)
    prev_dea = prev.get('DEA', 0)

    # 金叉: DIF从下往上穿越DEA
    if dif > dea and prev_dif <= prev_dea:
        signals['macd'] = '金叉 (买入信号)'
    elif dif < dea and prev_dif >= prev_dea:
        signals['macd'] = '死叉 (卖出信号)'
    elif dif > dea:
        signals['macd'] = '多头排列'
    else:
        signals['macd'] = '空头排列'

    # 布林带信号
    bb_pos = latest.get('BB_POSITION', 50)
    if bb_pos > 100:
        signals['bb'] = '触及上轨 - 超买'
    elif bb_pos < 0:
        signals['bb'] = '触及下轨 - 超卖'
    elif bb_pos > 80:
        signals['bb'] = '超买区域'
    elif bb_pos < 20:
        signals['bb'] = '超卖区域'
    else:
        signals['bb'] = '中性'

    # 量比信号
    vol_ratio = latest.get('VOL_RATIO', 1)
    if vol_ratio > 2:
        signals['volume'] = '放量异常'
    elif vol_ratio > 1.5:
        signals['volume'] = '成交量放大'
    elif vol_ratio < 0.5:
        signals['volume'] = '成交量萎缩'
    else:
        signals['volume'] = '成交量正常'

    # 乖离率 BIAS 信号
    bias6 = latest.get('BIAS6', 0)
    bias12 = latest.get('BIAS12', 0)
    bias24 = latest.get('BIAS24', 0)

    # BIAS6 信号
    if bias6 > 10:
        signals['bias6'] = f'{bias6:.2f}% - 严重超买，注意回调风险'
    elif bias6 > 5:
        signals['bias6'] = f'{bias6:.2f}% - 超买区域'
    elif bias6 < -10:
        signals['bias6'] = f'{bias6:.2f}% - 严重超卖，反弹机会'
    elif bias6 < -5:
        signals['bias6'] = f'{bias6:.2f}% - 超卖区域'
    else:
        signals['bias6'] = f'{bias6:.2f}% - 正常区域'

    # BIAS12 信号
    if bias12 > 15:
        signals['bias12'] = f'{bias12:.2f}% - 严重超买'
    elif bias12 > 8:
        signals['bias12'] = f'{bias12:.2f}% - 超买'
    elif bias12 < -15:
        signals['bias12'] = f'{bias12:.2f}% - 严重超卖'
    elif bias12 < -8:
        signals['bias12'] = f'{bias12:.2f}% - 超卖'
    else:
        signals['bias12'] = f'{bias12:.2f}% - 正常'

    # BIAS24 信号
    if bias24 > 20:
        signals['bias24'] = f'{bias24:.2f}% - 严重超买'
    elif bias24 > 10:
        signals['bias24'] = f'{bias24:.2f}% - 超买'
    elif bias24 < -20:
        signals['bias24'] = f'{bias24:.2f}% - 严重超卖'
    elif bias24 < -10:
        signals['bias24'] = f'{bias24:.2f}% - 超卖'
    else:
        signals['bias24'] = f'{bias24:.2f}% - 正常'

    # BIAS 综合判断
    if bias6 > 10 or bias12 > 15 or bias24 > 20:
        signals['bias_summary'] = '整体超买，注意风险'
    elif bias6 < -10 or bias12 < -15 or bias24 < -20:
        signals['bias_summary'] = '整体超卖，关注机会'
    elif bias6 > 5 or bias12 > 8 or bias24 > 10:
        signals['bias_summary'] = '偏超买'
    elif bias6 < -5 or bias12 < -8 or bias24 < -10:
        signals['bias_summary'] = '偏超卖'
    else:
        signals['bias_summary'] = '乖离率正常'

    return signals


def generate_technical_report(code: str, name: str = None, days: int = 180) -> str:
    """
    生成技术分析报告 - 直接从 API 获取数据

    Args:
        code: 股票代码
        name: 股票名称
        days: 获取数据天数，默认 180

    Returns:
        Markdown 格式报告
    """
    print(f"正在获取 {code} 的数据...")

    # 直接从 API 获取数据
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    df = fetch_data(code, start_date=start_date, end_date=end_date)

    # 保存数据
    filename = f"{code}-kline-{end_date}.csv"
    save_data(df, filename)

    # 计算技术指标
    df = calculate_indicators(df)

    # 分析信号
    signals = analyze_signals(df)

    latest = df.iloc[-1]
    close_col = 'close'

    # 生成报告
    report = f"""# {name or code} ({code}) 技术分析报告

**分析日期**: {datetime.now().strftime('%Y年%m月%d日')}
**数据来源**: AkShare

## 一、行情概览

| 指标 | 数值 |
|------|------|
| 当前价格 | ¥{latest[close_col]:.2f} |
| 涨跌幅 | {latest.get('涨跌幅', latest.get('pct_chg', 0)):+.2f}% |
| 最高价 | ¥{latest.get('最高', latest.get('High', 0)):.2f} |
| 最低价 | ¥{latest.get('最低', latest.get('Low', 0)):.2f} |
| 成交量 | {latest.get('volume', latest.get('成交量', 0)):,} |
| 成交额 | ¥{latest.get('成交额', 0)/10000:.2f}亿 |

## 二、技术分析

### 2.1 均线分析

| 均线 | 数值 | 信号 |
|------|------|------|
| MA5 | ¥{latest.get('MA5', 0):.2f} | 5日均价 |
| MA10 | ¥{latest.get('MA10', 0):.2f} | 10日均价 |
| MA20 | ¥{latest.get('MA20', 0):.2f} | 20日均价 |
| MA60 | ¥{latest.get('MA60', 0):.2f} | 60日均价 |

**均线形态**: {signals.get('ma_signal', 'N/A')}
**中期判断**: {signals.get('ma_mid', 'N/A')}

### 2.2 RSI 分析

- RSI (14): **{signals.get('rsi', 'N/A')}**

### 2.3 MACD 分析

| 指标 | 数值 | 信号 |
|------|------|------|
| DIF | {latest.get('DIF', 0):.4f} | |
| DEA | {latest.get('DEA', 0):.4f} | |
| MACD | {latest.get('MACD', 0):.4f} | {signals.get('macd', 'N/A')} |

### 2.4 布林带分析

| 位置 | 数值 |
|------|------|
| 上轨 | ¥{latest.get('BB_UPPER', 0):.2f} |
| 中轨 | ¥{latest.get('BB_MIDDLE', 0):.2f} |
| 下轨 | ¥{latest.get('BB_LOWER', 0):.2f} |
| 位置 | {signals.get('bb', 'N/A')} |

### 2.5 成交量分析

- 成交量: {latest.get('volume', latest.get('成交量', 0)):,}
- 量比: {latest.get('VOL_RATIO', 1):.2f}
- 信号: {signals.get('volume', 'N/A')}

### 2.6 乖离率 (BIAS) 分析

| 周期 | 数值 | 信号 |
|------|------|------|
| BIAS6 | {latest.get('BIAS6', 0):.2f}% | {signals.get('bias6', 'N/A')} |
| BIAS12 | {latest.get('BIAS12', 0):.2f}% | {signals.get('bias12', 'N/A')} |
| BIAS24 | {latest.get('BIAS24', 0):.2f}% | {signals.get('bias24', 'N/A')} |

**乖离率判断**: {signals.get('bias_summary', 'N/A')}

## 三、综合判断

| 维度 | 判断 |
|------|------|
| 均线 | {signals.get('ma_signal', 'N/A')} |
| RSI | {signals.get('rsi', 'N/A')} |
| MACD | {signals.get('macd', 'N/A')} |
| 布林带 | {signals.get('bb', 'N/A')} |
| 乖离率 | {signals.get('bias_summary', 'N/A')} |

## 四、操作建议

- 支撑位: ¥{latest.get('BB_LOWER', 0):.2f}
- 阻力位: ¥{latest.get('BB_UPPER', 0):.2f}
- 综合建议: 关注均线和MACD信号

---
*本报告仅供参考，不构成投资建议*
*数据来源: AkShare, 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python technical_indicators.py <股票代码> [股票名称] [天数]")
        print("示例: python technical_indicators.py 300666 江丰电子 180")
        sys.exit(1)

    code = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 180

    report = generate_technical_report(code, name, days)
    print(report)
