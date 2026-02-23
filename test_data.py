#!/usr/bin/env python3
"""测试数据格式"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from data_fetcher import get_historical_data, load_data_from_csv

print("测试 1: 获取一只股票的历史数据")
symbol = "603268"
df = get_historical_data(symbol)

if df is not None:
    print(f"\n成功获取 {symbol} 数据")
    print(f"数据行数: {len(df)}")
    print(f"\n列名: {df.columns.tolist()}")
    print(f"\n前5行数据:")
    print(df.head())
    print(f"\n数据类型:")
    print(df.dtypes)
else:
    print("获取数据失败")

print("\n" + "="*60)
print("测试 2: 查看已筛选的股票")
data = load_data_from_csv()
if 'filtered' in data:
    filtered_df = data['filtered']
    print(f"筛选出 {len(filtered_df)} 只股票")
    print("\n前10只股票:")
    print(filtered_df[['代码', '名称']].head(10))
