#!/usr/bin/env python3
"""
数据获取脚本
使用 AkShare 获取股票、ETF、基金、加密币的 K 线数据
"""

import akshare as ak
import pandas as pd
import os
from datetime import datetime, timedelta


DATA_DIR = os.path.expanduser("~/uni-web/frontend-html/finance-analysis/data")


def fetch_data(code: str, start_date: str = None, end_date: str = None, adjust: str = "qfq") -> pd.DataFrame:
    """
    获取股票/ETF K 线数据

    Args:
        code: 股票代码 (如 600519, 300666, 510300)
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        adjust: 复权类型 (qfq: 前复权, hfq: 后复权, empty: 不复权)

    Returns:
        DataFrame
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    # A 股
    if code.isdigit() and len(code) == 6:
        df = ak.stock_zh_a_hist(symbol=code, start_date=start_date, end_date=end_date, adjust=adjust)
    # 港股
    elif ".HK" in code or ".hk" in code.upper():
        df = ak.stock_hk_daily(symbol=code.replace(".HK", "").replace(".hk", ""))
        df['日期'] = df['date'].dt.strftime('%Y-%m-%d')
        df['股票代码'] = code
    # 美股
    elif code.isalpha() and len(code) <= 5:
        df = ak.stock_us_hist(symbol=code, start_date=start_date.replace("-", ""), end_date=end_date.replace("-", ""))
    # ETF
    elif code.isdigit() and len(code) == 6:
        try:
            df = ak.fund_etf_hist_em(symbol=code, start_date=start_date, end_date=end_date)
        except:
            df = ak.stock_zh_a_hist(symbol=code, start_date=start_date, end_date=end_date, adjust=adjust)
    else:
        raise ValueError(f"不支持的股票代码: {code}")

    return df


def fetch_crypto_data(symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    获取加密货币数据

    Args:
        symbol: 币种符号 (如 BTC, ETH)
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        DataFrame
    """
    try:
        df = ak.crypto_hist(symbol=symbol, start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取加密货币数据失败: {e}")
        return pd.DataFrame()


def save_data(df: pd.DataFrame, filename: str) -> str:
    """
    保存数据到 CSV 文件

    Args:
        df: 数据
        filename: 文件名

    Returns:
        文件路径
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)
    df.to_csv(filepath, index=False)
    print(f"数据已保存到: {filepath}")
    return filepath


def load_data(filename: str) -> pd.DataFrame:
    """
    加载本地 CSV 数据

    Args:
        filename: 文件名

    Returns:
        DataFrame
    """
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"数据文件不存在: {filepath}")
    return pd.read_csv(filepath)


def fetch_and_save(code: str, name: str = None, days: int = 180) -> pd.DataFrame:
    """
    获取数据并保存，支持自动命名

    Args:
        code: 股票代码
        name: 股票名称 (可选)
        days: 获取天数

    Returns:
        DataFrame
    """
    print(f"获取数据: {code}")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")

    df = fetch_data(code, start_date, end_date)

    # 保存数据
    filename = f"{code}-kline-{end_date}.csv"
    save_data(df, filename)

    print(f"\n{name or code} ({code}) 数据已就绪")
    print(f"数据范围: {df['日期'].iloc[0]} ~ {df['日期'].iloc[-1]}")
    print(f"共 {len(df)} 条记录")
    return df


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python data_fetcher.py <股票代码> [股票名称] [天数]")
        print("示例: python data_fetcher.py 600519 贵州茅台 180")
        sys.exit(1)

    code = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 180

    fetch_and_save(code, name, days)
