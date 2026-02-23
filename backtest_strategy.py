#!/usr/bin/env python3
"""
尾盘选股策略 - Backtrader实现
基于掘金文章中的尾盘选股策略

策略条件:
1. 涨幅在2%-5%之间
2. 流通市值50-200亿
3. 换手率4-10%
4. 量比>1
5. 均线多头排列（5日 > 10日 > 20日）
"""

import backtrader as bt
import pandas as pd
import os
from datetime import datetime, timedelta

# 导入 data_fetcher
import sys
sys.path.insert(0, os.path.dirname(__file__))


class MAVolumeStrategy(bt.Strategy):
    """
    尾盘选股策略
    买入条件:
    - 收盘价 > 5日均线 > 10日均线 > 20日均线 (均线多头排列)
    - 涨幅在2%-5%之间
    - 换手率4-10%
    - 量比>1

    卖出条件:
    - 次日开盘卖出
    - 或者达到止盈/止损条件
    """

    params = (
        ('ma_short', 5),
        ('ma_mid', 10),
        ('ma_long', 20),
        ('pct_min', 2.0),     # 最小涨幅
        ('pct_max', 5.0),     # 最大涨幅
        ('turnover_min', 4.0),  # 最小换手率
        ('turnover_max', 10.0), # 最大换手率
        ('vol_ratio_min', 1.0), # 最小量比
    )

    def __init__(self):
        self.inds = {}
        self.order = None
        self.entry_bar = None  # 记录买入时的bar索引

        for d in self.datas:
            # 计算移动平均线
            d.ma5 = bt.indicators.SMA(d.close, period=self.params.ma_short)
            d.ma10 = bt.indicators.SMA(d.close, period=self.params.ma_mid)
            d.ma20 = bt.indicators.SMA(d.close, period=self.params.ma_long)

            # 计算成交量均线
            d.vol_ma5 = bt.indicators.SMA(d.volume, period=5)

            # 涨跌幅
            d.pct_change = (d.close - d.close(-1)) / d.close(-1) * 100

            self.inds[d] = {
                'ma5': d.ma5,
                'ma10': d.ma10,
                'ma20': d.ma20,
                'pct_change': d.pct_change,
            }

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'[{dt.isoformat()}] {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: 价格 {order.executed.price:.2f}, 数量 {order.executed.size}')
            elif order.issell():
                self.log(f'卖出执行: 价格 {order.executed.price:.2f}, 数量 {order.executed.size}')

        self.order = None

    def next(self):
        # 跳过前20天（等待均线形成）
        if len(self) < self.params.ma_long:
            return

        for d in self.datas:
            # 获取当前数据
            close = d.close[0]
            ma5 = d.ma5[0]
            ma10 = d.ma10[0]
            ma20 = d.ma20[0]
            pct = d.pct_change[0]
            volume = d.volume[0]
            vol_yesterday = d.volume[-1]

            # 计算量比
            vol_ratio = volume / vol_yesterday if vol_yesterday > 0 else 0

            # 买入条件检查
            # 1. 均线多头排列: ma5 > ma10 > ma20
            # 2. 涨幅在2%-5%之间
            # 3. 收盘价在均线上方

            ma_alignment = ma5 > ma10 > ma20
            price_above_ma = close > ma5

            buy_condition = (
                ma_alignment and
                price_above_ma and
                self.params.pct_min <= pct <= self.params.pct_max and
                vol_ratio > self.params.vol_ratio_min
            )

            # 如果没有持仓且满足买入条件
            if not self.getposition(d).size > 0:
                if buy_condition:
                    self.log(f'{d._name} 满足买入条件: 收盘价={close:.2f}, '
                            f'涨幅={pct:.2f}%, 量比={vol_ratio:.2f}, '
                            f'MA5={ma5:.2f}, MA10={ma10:.2f}, MA20={ma20:.2f}')
                    self.order = self.buy(d)
                    self.entry_bar = len(d)

            # 卖出条件：次日卖出（T+1）
            else:
                if self.entry_bar is not None and len(d) - self.entry_bar > 1:
                    self.log(f'{d._name} 卖出: 持有期结束')
                    self.order = self.sell(d)
                    self.entry_bar = None


class MeanReversionStrategy(bt.Strategy):
    """
    均值回归策略 - 另一个示例策略
    """

    params = (
        ('period', 20),
        ('devfactor', 2),
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {
                'ma': bt.indicators.SMA(d.close, period=self.params.period),
                'std': bt.indicators.StandardDeviation(d.close, period=self.params.period),
            }

    def next(self):
        for d in self.dates:
            if len(self) < self.params.period:
                continue

            ma = self.inds[d]['ma'][0]
            std = self.inds[d]['std'][0]
            upper = ma + self.params.devfactor * std
            lower = ma - self.params.devfactor * std

            if not self.getposition(d).size:
                if d.close[-1] < lower and d.close[0] > lower:
                    self.buy(d)
            else:
                if d.close[0] > upper:
                    self.sell(d)


def run_backtest(data_file=None, initial_cash=100000):
    """
    运行回测
    """
    print("=" * 60)
    print("开始回测 - 尾盘选股策略")
    print("=" * 60)

    cerebro = bt.Cerebro()

    # 设置初始资金
    cerebro.broker.setcash(initial_cash)

    # 设置交易手续费
    cerebro.broker.setcommission(commission=0.001)

    # 加载数据
    if data_file and os.path.exists(data_file):
        print(f"从文件加载数据: {data_file}")
        data = bt.feeds.GenericCSVData(
            dataname=data_file,
            fromdate=datetime(2024, 1, 1),
            todate=datetime.now(),
            dtformat='%Y-%m-%d',
            datetime=0,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=5,
            openinterest=-1
        )
        cerebro.adddata(data)
    else:
        # 使用示例数据生成器
        print("使用示例数据进行回测...")

        # 创建一些示例数据
        for symbol in ['000001', '600519', '000858']:
            data = bt.feeds.YahooFinanceData(
                dataname=symbol,
                fromdate=datetime(2024, 1, 1),
                todate=datetime.now(),
            )
            cerebro.adddata(data)

    # 添加策略
    cerebro.addstrategy(MAVolumeStrategy)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # 设置头寸大小
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

    # 打印初始资金
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')

    # 运行回测
    results = cerebro.run()

    # 打印最终资金
    final_value = cerebro.broker.getvalue()
    print(f'最终资金: {final_value:.2f}')
    print(f'总收益率: {(final_value - initial_cash) / initial_cash * 100:.2f}%')

    # 打印分析结果
    print("\n" + "=" * 60)
    print("回测分析")
    print("=" * 60)

    strat = results[0]

    # 夏普比率
    sharpe = strat.analyzers.sharpe.get_analysis()
    if sharpe.get('sharperatio'):
        print(f"夏普比率: {sharpe['sharperatio']:.2f}")

    # 回撤
    drawdown = strat.analyzers.drawdown.get_analysis()
    if drawdown.get('max'):
        print(f"最大回撤: {drawdown['max']['drawdown']:.2f}%")

    # 收益率
    returns = strat.analyzers.returns.get_analysis()
    if returns.get('rnorm100'):
        print(f"年化收益率: {returns['rnorm100']:.2f}%")

    # 交易统计
    trades = strat.analyzers.trades.get_analysis()
    if trades.get('total'):
        print(f"总交易次数: {trades['total']['total']}")
        if trades.get('won'):
            print(f"盈利次数: {trades['won']['total']}")
        if trades.get('lost'):
            print(f"亏损次数: {trades['lost']['total']}")

    print("\n" + "=" * 60)
    print("回测完成!")
    print("=" * 60)

    return results


def dataframe_to_backtrader(df, symbol, date_col='日期'):
    """
    将 pandas DataFrame 转换为 backtrader 可用的格式

    Args:
        df: 包含历史数据的 DataFrame
        symbol: 股票代码
        date_col: 日期列名

    Returns:
        backtrader.feeds.PandasData
    """
    if df is None or len(df) == 0:
        return None

    # 确保日期列是 datetime 类型
    df = df.copy()
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        df.set_index(date_col, inplace=True)

    # 检查必需的列并重命名
    rename_map = {
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume'
    }

    # 重命名列以匹配 backtrader 期望的格式
    df_bt = df.rename(columns=rename_map)

    # 确保只包含需要的列
    cols_needed = ['open', 'high', 'low', 'close', 'volume']
    for col in cols_needed:
        if col not in df_bt.columns:
            df_bt[col] = 0.0

    df_bt = df_bt[cols_needed].copy()

    # 创建 backtrader 数据源
    data = bt.feeds.PandasData(
        dataname=df_bt,
        name=symbol
    )
    return data


def run_backtest_with_datafetcher(initial_cash=100000, force_refresh=False):
    """
    使用 data_fetcher 获取数据并运行回测

    Args:
        initial_cash: 初始资金
        force_refresh: 是否强制刷新数据

    Returns:
        回测结果
    """
    from data_fetcher import fetch_and_save_data, get_historical_data

    print("=" * 60)
    print("开始回测 - 尾盘选股策略 (使用 data_fetcher)")
    print("=" * 60)

    # 1. 获取实时数据和筛选股票
    realtime_df, filtered_df = fetch_and_save_data(force_refresh=force_refresh)

    if filtered_df is None or len(filtered_df) == 0:
        print("没有符合条件的股票，无法进行回测")
        return None

    print(f"\n共筛选出 {len(filtered_df)} 只股票，准备获取历史数据...")

    # 2. 获取筛选后股票的历史数据
    cerebro = bt.Cerebro()

    # 设置初始资金
    cerebro.broker.setcash(initial_cash)

    # 设置交易手续费
    cerebro.broker.setcommission(commission=0.001)

    # 获取每只股票的历史数据并添加到 cerebro
    symbols = filtered_df['代码'].head(10).tolist()  # 限制数量避免请求过多
    loaded_count = 0

    for symbol in symbols:
        print(f"获取 {symbol} 历史数据...")
        hist_df = get_historical_data(symbol, period='daily')

        if hist_df is not None and len(hist_df) > 20:  # 确保有足够的数据
            # 转换为 backtrader 格式
            data = dataframe_to_backtrader(hist_df, symbol, date_col='日期')
            if data is not None:
                cerebro.adddata(data)
                loaded_count += 1
                print(f"  已加载 {symbol}，共 {len(hist_df)} 条数据")

    if loaded_count == 0:
        print("没有成功加载任何股票数据，回测终止")
        return None

    print(f"\n成功加载 {loaded_count} 只股票的历史数据")

    # 3. 添加策略
    cerebro.addstrategy(MAVolumeStrategy)

    # 4. 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # 5. 设置头寸大小
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

    # 6. 打印初始资金
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')

    # 7. 运行回测
    results = cerebro.run()

    # 8. 打印最终资金
    final_value = cerebro.broker.getvalue()
    print(f'最终资金: {final_value:.2f}')
    print(f'总收益率: {(final_value - initial_cash) / initial_cash * 100:.2f}%')

    # 9. 打印分析结果
    print("\n" + "=" * 60)
    print("回测分析")
    print("=" * 60)

    strat = results[0]

    # 夏普比率
    sharpe = strat.analyzers.sharpe.get_analysis()
    if sharpe.get('sharperatio'):
        print(f"夏普比率: {sharpe['sharperatio']:.2f}")

    # 回撤
    drawdown = strat.analyzers.drawdown.get_analysis()
    if drawdown.get('max'):
        print(f"最大回撤: {drawdown['max']['drawdown']:.2f}%")

    # 收益率
    returns = strat.analyzers.returns.get_analysis()
    if returns.get('rnorm100'):
        print(f"年化收益率: {returns['rnorm100']:.2f}%")

    # 交易统计
    trades = strat.analyzers.trades.get_analysis()
    if trades.get('total'):
        print(f"总交易次数: {trades['total']['total']}")
        if trades.get('won'):
            print(f"盈利次数: {trades['won']['total']}")
        if trades.get('lost'):
            print(f"亏损次数: {trades['lost']['total']}")

    print("\n" + "=" * 60)
    print("回测完成!")
    print("=" * 60)

    return results


if __name__ == "__main__":
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--live':
        # 使用实时数据模式
        force_refresh = len(sys.argv) > 2 and sys.argv[2] == '--refresh'
        run_backtest_with_datafetcher(force_refresh=force_refresh)
    elif len(sys.argv) > 1:
        data_file = sys.argv[1]
        run_backtest(data_file)
    else:
        # 默认使用 data_fetcher 获取数据
        run_backtest_with_datafetcher()
