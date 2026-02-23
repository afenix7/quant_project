#!/usr/bin/env python3
"""
FastAPI 后端 - 尾盘选股策略回测服务
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import backtrader as bt

from data_fetcher import fetch_and_save_data, get_historical_data

app = FastAPI(title="尾盘选股策略回测 API")

# 允许 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BacktestRequest(BaseModel):
    initial_cash: float = 100000.0
    force_refresh: bool = False
    stock_limit: int = 10


class TradeRecord(BaseModel):
    date: str
    symbol: str
    action: str  # 'buy' or 'sell'
    price: float
    size: float


class EquityPoint(BaseModel):
    date: str
    strategy: float
    benchmark: float


class StockDataPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class BacktestResult(BaseModel):
    success: bool
    message: str
    initial_cash: float
    final_value: float
    total_return: float
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    annual_return: Optional[float]
    total_trades: int
    winning_trades: int
    losing_trades: int
    trades: List[TradeRecord]
    equity_curve: List[EquityPoint]
    stock_data: Dict[str, List[StockDataPoint]]


# 自定义策略，记录交易
class TrackedMAVolumeStrategy(bt.Strategy):
    params = (
        ('ma_short', 5),
        ('ma_mid', 10),
        ('ma_long', 20),
        ('pct_min', 2.0),
        ('pct_max', 5.0),
        ('turnover_min', 4.0),
        ('turnover_max', 10.0),
        ('vol_ratio_min', 1.0),
    )

    def __init__(self):
        self.inds = {}
        self.order = None
        self.entry_bar = None
        self.trade_list = []
        self.equity_curve = []

        for d in self.datas:
            d.ma5 = bt.indicators.SMA(d.close, period=self.params.ma_short)
            d.ma10 = bt.indicators.SMA(d.close, period=self.params.ma_mid)
            d.ma20 = bt.indicators.SMA(d.close, period=self.params.ma_long)
            d.vol_ma5 = bt.indicators.SMA(d.volume, period=5)

            self.inds[d] = {
                'ma5': d.ma5,
                'ma10': d.ma10,
                'ma20': d.ma20,
            }

    def next(self):
        # 记录权益
        dt = self.datas[0].datetime.date(0)
        self.equity_curve.append({
            'date': dt.isoformat(),
            'value': self.broker.getvalue()
        })

        if len(self) < self.params.ma_long:
            return

        for d in self.datas:
            close = d.close[0]
            close_prev = d.close[-1]
            ma5 = d.ma5[0]
            ma10 = d.ma10[0]
            ma20 = d.ma20[0]
            volume = d.volume[0]
            vol_yesterday = d.volume[-1]

            # 安全计算涨跌幅
            if close_prev > 0:
                pct = (close - close_prev) / close_prev * 100
            else:
                pct = 0

            # 安全计算量比
            vol_ratio = volume / vol_yesterday if vol_yesterday > 0 else 0

            # 安全检查均线值
            if ma5 <= 0 or ma10 <= 0 or ma20 <= 0:
                continue

            ma_alignment = ma5 > ma10 > ma20
            price_above_ma = close > ma5

            buy_condition = (
                ma_alignment and
                price_above_ma and
                self.params.pct_min <= pct <= self.params.pct_max and
                vol_ratio > self.params.vol_ratio_min
            )

            dt_str = dt.isoformat()
            symbol = d._name

            if not self.getposition(d).size > 0:
                if buy_condition:
                    self.order = self.buy(d)
                    self.entry_bar = len(d)
                    self.trade_list.append({
                        'date': dt_str,
                        'symbol': symbol,
                        'action': 'buy',
                        'price': close,
                        'size': 0
                    })
            else:
                if self.entry_bar is not None and len(d) - self.entry_bar > 1:
                    self.order = self.sell(d)
                    self.trade_list.append({
                        'date': dt_str,
                        'symbol': symbol,
                        'action': 'sell',
                        'price': close,
                        'size': 0
                    })
                    self.entry_bar = None


def dataframe_to_backtrader(df, symbol, date_col='日期'):
    """将 pandas DataFrame 转换为 backtrader 可用的格式"""
    if df is None or len(df) == 0:
        return None

    df = df.copy()
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        df.set_index(date_col, inplace=True)

    rename_map = {
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume'
    }

    df_bt = df.rename(columns=rename_map)
    cols_needed = ['open', 'high', 'low', 'close', 'volume']
    for col in cols_needed:
        if col not in df_bt.columns:
            df_bt[col] = 0.0

    df_bt = df_bt[cols_needed].copy()

    data = bt.feeds.PandasData(
        dataname=df_bt,
        name=symbol
    )
    return data


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/api/backtest", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest):
    """运行回测并返回结果"""
    try:
        print(f"开始回测: 初始资金={request.initial_cash}, 刷新数据={request.force_refresh}")

        # 1. 获取实时数据和筛选股票
        realtime_df, filtered_df = fetch_and_save_data(force_refresh=request.force_refresh)

        if filtered_df is None or len(filtered_df) == 0:
            return BacktestResult(
                success=False,
                message="没有符合条件的股票",
                initial_cash=request.initial_cash,
                final_value=request.initial_cash,
                total_return=0,
                sharpe_ratio=None,
                max_drawdown=None,
                annual_return=None,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                trades=[],
                equity_curve=[],
                stock_data={}
            )

        print(f"筛选出 {len(filtered_df)} 只股票")

        # 2. 获取历史数据
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(request.initial_cash)
        cerebro.broker.setcommission(commission=0.001)

        symbols = filtered_df['代码'].head(request.stock_limit).tolist()
        stock_data_dict = {}
        all_dates = []

        for symbol in symbols:
            hist_df = get_historical_data(symbol, period='daily')
            if hist_df is not None and len(hist_df) > 20:
                data = dataframe_to_backtrader(hist_df, symbol, date_col='日期')
                if data is not None:
                    cerebro.adddata(data)
                    # 保存股票数据用于前端展示
                    stock_data_dict[symbol] = []
                    for _, row in hist_df.iterrows():
                        date_str = pd.to_datetime(row['日期']).isoformat()[:10]
                        stock_data_dict[symbol].append(StockDataPoint(
                            date=date_str,
                            open=float(row['开盘']),
                            high=float(row['最高']),
                            low=float(row['最低']),
                            close=float(row['收盘']),
                            volume=float(row['成交量'])
                        ))
                        all_dates.append(date_str)

        if not stock_data_dict:
            return BacktestResult(
                success=False,
                message="没有成功加载任何股票数据",
                initial_cash=request.initial_cash,
                final_value=request.initial_cash,
                total_return=0,
                sharpe_ratio=None,
                max_drawdown=None,
                annual_return=None,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                trades=[],
                equity_curve=[],
                stock_data={}
            )

        # 3. 添加策略和分析器
        cerebro.addstrategy(TrackedMAVolumeStrategy)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

        # 4. 运行回测
        results = cerebro.run()
        strat = results[0]

        # 5. 收集结果
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - request.initial_cash) / request.initial_cash * 100

        # 提取交易记录
        trades = [TradeRecord(**t) for t in strat.trade_list]

        # 构建权益曲线
        equity_curve = []
        strategy_equity = {p['date']: p['value'] for p in strat.equity_curve}

        # 计算基准收益（使用第一只股票作为基准）
        first_symbol = list(stock_data_dict.keys())[0]
        benchmark_equity = {}
        benchmark_value = request.initial_cash

        if first_symbol in stock_data_dict:
            stock_points = stock_data_dict[first_symbol]
            for i, point in enumerate(stock_points):
                if i == 0:
                    benchmark_value = request.initial_cash
                else:
                    prev_close = stock_points[i-1].close
                    curr_close = point.close
                    if prev_close > 0:
                        benchmark_value = benchmark_value * (curr_close / prev_close)
                benchmark_equity[point.date] = benchmark_value

        # 合并日期
        all_dates_sorted = sorted(set(strategy_equity.keys()) | set(benchmark_equity.keys()))

        for date in all_dates_sorted:
            strategy_val = strategy_equity.get(date)
            benchmark_val = benchmark_equity.get(date)

            # 如果某天没有数据，用前一天的数据填充
            if strategy_val is None and equity_curve:
                strategy_val = equity_curve[-1].strategy
            if benchmark_val is None and equity_curve:
                benchmark_val = equity_curve[-1].benchmark

            if strategy_val is not None and benchmark_val is not None:
                equity_curve.append(EquityPoint(
                    date=date,
                    strategy=strategy_val,
                    benchmark=benchmark_val
                ))

        # 提取分析指标
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        returns = strat.analyzers.returns.get_analysis()
        trade_analysis = strat.analyzers.trades.get_analysis()

        sharpe_ratio = sharpe.get('sharperatio') if sharpe.get('sharperatio') else None
        max_dd = drawdown.get('max', {}).get('drawdown') if drawdown.get('max') else None
        annual_ret = returns.get('rnorm100') if returns.get('rnorm100') else None

        total_trades = trade_analysis.get('total', {}).get('total', 0) if trade_analysis.get('total') else 0
        winning_trades = trade_analysis.get('won', {}).get('total', 0) if trade_analysis.get('won') else 0
        losing_trades = trade_analysis.get('lost', {}).get('total', 0) if trade_analysis.get('lost') else 0

        return BacktestResult(
            success=True,
            message=f"回测完成，加载了 {len(stock_data_dict)} 只股票",
            initial_cash=request.initial_cash,
            final_value=final_value,
            total_return=total_return,
            sharpe_ratio=float(sharpe_ratio) if sharpe_ratio else None,
            max_drawdown=float(max_dd) if max_dd else None,
            annual_return=float(annual_ret) if annual_ret else None,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            trades=trades,
            equity_curve=equity_curve,
            stock_data=stock_data_dict
        )

    except Exception as e:
        print(f"回测错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks")
async def get_stocks():
    """获取筛选后的股票列表"""
    try:
        from data_fetcher import load_data_from_csv
        data = load_data_from_csv()
        if 'filtered' in data:
            df = data['filtered']
            return {
                'success': True,
                'stocks': df[['代码', '名称', '最新价', '涨跌幅', '换手率', '量比']].to_dict('records')
            }
        return {'success': False, 'stocks': []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
