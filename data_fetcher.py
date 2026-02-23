#!/usr/bin/env python3
"""
使用akshare获取A股实时股票数据并保存到CSV
基于掘金文章中的尾盘选股策略
"""

import akshare as ak
import pandas as pd
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def get_all_stocks():
    """获取所有A股股票列表"""
    print("获取A股股票列表...")
    df = ak.stock_info_a_code_name()
    print(f"共获取 {len(df)} 只股票")
    return df


def get_realtime_quotes(symbols=None):
    """获取实时行情数据"""
    print("获取实时行情数据...")
    
    if symbols is None:
        df = ak.stock_zh_a_spot_em()
    else:
        df = ak.stock_zh_a_spot_em()
        df = df[df['代码'].isin(symbols)]
    
    print(f"获取到 {len(df)} 条行情数据")
    return df


def get_historical_data(symbol, period='daily', start_date=None, end_date=None):
    """获取历史K线数据"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date or (datetime.now().strftime('%Y%m%d') if start_date is None else start_date),
            end_date=end_date or datetime.now().strftime('%Y%m%d'),
            adjust="qfq"
        )
        return df
    except Exception as e:
        print(f"获取 {symbol} 历史数据失败: {e}")
        return None


def get_stock_daily_basic(symbol):
    """获取股票每日基本指标（换手率、市值等）"""
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        return df
    except Exception as e:
        print(f"获取 {symbol} 基本信息失败: {e}")
        return None


def get_market_value(symbol):
    """获取股票市值数据"""
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol)
        return df
    except Exception as e:
        print(f"获取 {symbol} 市值数据失败: {e}")
        return None


def fetch_and_save_data():
    """获取所有数据并保存到CSV"""
    
    print("=" * 50)
    print("开始获取A股数据...")
    print("=" * 50)
    
    # 1. 获取实时行情
    realtime_df = get_realtime_quotes()
    
    # 保存实时行情
    realtime_file = os.path.join(DATA_DIR, 'realtime_quotes.csv')
    realtime_df.to_csv(realtime_file, index=False, encoding='utf-8-sig')
    print(f"实时行情已保存到: {realtime_file}")
    
    # 2. 筛选符合尾盘选股条件的股票
    # 条件1: 涨幅在2%-5%之间
    # 条件2: 换手率4-10%
    # 条件3: 量比>1
    # 条件4: 流通市值50-200亿
    
    print("\n筛选符合尾盘选股条件的股票...")
    
    # 解析涨跌幅
    if '涨跌幅' in realtime_df.columns:
        realtime_df['涨跌幅'] = pd.to_numeric(realtime_df['涨跌幅'], errors='coerce')
        condition_pct = (realtime_df['涨跌幅'] >= 2) & (realtime_df['涨跌幅'] <= 5)
    else:
        condition_pct = pd.Series([False] * len(realtime_df), index=realtime_df.index)
    
    # 解析换手率
    if '换手率' in realtime_df.columns:
        realtime_df['换手率'] = pd.to_numeric(realtime_df['换手率'].str.replace('%', ''), errors='coerce')
        condition_turnover = (realtime_df['换手率'] >= 4) & (realtime_df['换手率'] <= 10)
    else:
        condition_turnover = pd.Series([False] * len(realtime_df), index=realtime_df.index)
    
    # 解析量比
    if '量比' in realtime_df.columns:
        realtime_df['量比'] = pd.to_numeric(realtime_df['量比'], errors='coerce')
        condition_volume = realtime_df['量比'] > 1
    else:
        condition_volume = pd.Series([False] * len(realtime_df), index=realtime_df.index)
    
    # 解析市值（单位：亿）
    if '总市值' in realtime_df.columns:
        realtime_df['总市值_亿'] = pd.to_numeric(realtime_df['总市值'], errors='coerce')
        condition_market_cap = (realtime_df['总市值_亿'] >= 50) & (realtime_df['总市值_亿'] <= 200)
    else:
        condition_market_cap = pd.Series([False] * len(realtime_df), index=realtime_df.index)
    
    # 综合筛选
    filtered_df = realtime_df[condition_pct & condition_turnover & condition_volume]
    
    print(f"涨幅2-5%: {condition_pct.sum()}")
    print(f"换手率4-10%: {condition_turnover.sum()}")
    print(f"量比>1: {condition_volume.sum()}")
    print(f"市值50-200亿: {condition_market_cap.sum()}")
    print(f"\n初步筛选出 {len(filtered_df)} 只股票")
    
    # 保存筛选结果
    if len(filtered_df) > 0:
        filtered_file = os.path.join(DATA_DIR, 'filtered_stocks.csv')
        filtered_df.to_csv(filtered_file, index=False, encoding='utf-8-sig')
        print(f"筛选结果已保存到: {filtered_file}")
    
    # 3. 获取符合条件股票的历史数据（用于均线判断）
    print("\n获取符合条件股票的历史数据...")
    
    sample_symbols = filtered_df['代码'].head(10).tolist() if len(filtered_df) > 0 else []
    
    history_data = []
    for symbol in sample_symbols[:5]:  # 限制数量避免请求过多
        print(f"获取 {symbol} 历史数据...")
        hist_df = get_historical_data(symbol, period='daily')
        if hist_df is not None and len(hist_df) > 0:
            hist_df['symbol'] = symbol
            history_data.append(hist_df)
    
    if history_data:
        all_history = pd.concat(history_data, ignore_index=True)
        history_file = os.path.join(DATA_DIR, 'historical_data.csv')
        all_history.to_csv(history_file, index=False, encoding='utf-8-sig')
        print(f"历史数据已保存到: {history_file}")
    
    print("\n" + "=" * 50)
    print("数据获取完成!")
    print("=" * 50)
    
    return realtime_df, filtered_df


def load_data_from_csv():
    """从CSV加载数据"""
    realtime_file = os.path.join(DATA_DIR, 'realtime_quotes.csv')
    filtered_file = os.path.join(DATA_DIR, 'filtered_stocks.csv')
    history_file = os.path.join(DATA_DIR, 'historical_data.csv')
    
    data = {}
    
    if os.path.exists(realtime_file):
        data['realtime'] = pd.read_csv(realtime_file)
    
    if os.path.exists(filtered_file):
        data['filtered'] = pd.read_csv(filtered_file)
    
    if os.path.exists(history_file):
        data['history'] = pd.read_csv(history_file)
    
    return data


if __name__ == "__main__":
    realtime_df, filtered_df = fetch_and_save_data()
    
    print("\n实时行情数据预览:")
    print(realtime_df.head())
    
    print("\n筛选后的股票:")
    print(filtered_df)
