#!/usr/bin/env python3
"""
整合 data_fetcher 和 backtest_strategy 的运行脚本
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from backtest_strategy import run_backtest_with_datafetcher

if __name__ == "__main__":
    # 参数说明：
    # python run_backtest.py          - 使用本地缓存数据
    # python run_backtest.py refresh   - 强制刷新数据

    force_refresh = len(sys.argv) > 1 and sys.argv[1] in ['refresh', '--refresh', '-r']

    run_backtest_with_datafetcher(
        initial_cash=100000,
        force_refresh=force_refresh
    )
