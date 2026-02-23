#!/usr/bin/env python3
"""测试 akshare 接口"""

import akshare as ak
from datetime import datetime, timedelta

print("测试 akshare 接口...")

symbol = "603268"

print(f"\n尝试获取 {symbol} 的历史数据...")

# 测试 1: 默认参数
try:
    df1 = ak.stock_zh_a_hist(symbol=symbol)
    print(f"默认参数: 获取到 {len(df1)} 条数据")
    if len(df1) > 0:
        print(f"列名: {df1.columns.tolist()}")
        print(df1.head())
except Exception as e:
    print(f"默认参数失败: {e}")

# 测试 2: 用最近30天
end_date = datetime.now()
start_date = end_date - timedelta(days=90)
start_str = start_date.strftime('%Y%m%d')
end_str = end_date.strftime('%Y%m%d')

print(f"\n尝试日期范围: {start_str} - {end_str}")

try:
    df2 = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_str,
        end_date=end_str,
        adjust="qfq"
    )
    print(f"指定日期: 获取到 {len(df2)} 条数据")
    if len(df2) > 0:
        print(f"列名: {df2.columns.tolist()}")
        print(df2.head())
except Exception as e:
    print(f"指定日期失败: {e}")
