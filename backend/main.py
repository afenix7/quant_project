#!/usr/bin/env python3
"""
FastAPI 后端 - 尾盘选股策略回测服务
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import backtrader as bt
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from data_fetcher import fetch_and_save_data, get_historical_data

# 尝试导入 requests
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# 配置
SECRET_KEY = "quant-project-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 固定密码
FIXED_PASSWORD = "cjhyshlm901"
FIXED_USERNAME = "admin"

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://quant_user:quant_password@localhost:5432/quant_db")

# SQLAlchemy 设置
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 安全模式
security = HTTPBearer()


# 数据库模型
class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    token = Column(String, primary_key=True, index=True)
    expires_at = Column(DateTime)


# 创建表
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        # 初始化默认用户
        db = SessionLocal()
        user = db.query(User).filter(User.username == FIXED_USERNAME).first()
        if not user:
            hashed = pwd_context.hash(FIXED_PASSWORD)
            db_user = User(username=FIXED_USERNAME, hashed_password=hashed)
            db.add(db_user)
            db.commit()
        db.close()
    except Exception as e:
        print(f"数据库初始化失败: {e}")


# Pydantic 模型
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


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


class StockAnalysisRequest(BaseModel):
    code: str
    name: str = ""


class StockAnalysisResult(BaseModel):
    success: bool
    message: str
    code: str
    name: str
    quote: Optional[dict]
    fundamentals: Optional[dict]
    technical: Optional[dict]
    sentiment: Optional[dict]
    news: Optional[dict]
    score: Optional[int]
    recommendation: Optional[str]


# FastAPI 应用
app = FastAPI(title="尾盘选股策略回测 API")

# 允许 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# JWT 工具函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        # 检查 token 是否在黑名单
        blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
        if blacklisted:
            raise credentials_exception

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# 登录端点
@app.post("/api/login", response_model=Token)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """登录获取 access token"""
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """登出，将 token 加入黑名单"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expires_at = datetime.fromtimestamp(payload["exp"])
    except JWTError:
        expires_at = datetime.utcnow() + timedelta(hours=1)

    blacklisted = TokenBlacklist(token=token, expires_at=expires_at)
    db.add(blacklisted)
    db.commit()
    return {"success": True, "message": "登出成功"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


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


@app.post("/api/backtest", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest, current_user: User = Depends(get_current_user)):
    """运行回测并返回结果（需要认证）"""
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
async def get_stocks(current_user: User = Depends(get_current_user)):
    """获取筛选后的股票列表（需要认证）"""
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


# 股票分析相关函数
def safe_div(a, b):
    try:
        return float(a) / float(b) if a and b else 0
    except:
        return 0


def fetch_stock_data(code, name=""):
    print(f"Fetching {code} {name}...")
    results = {'quote': {}, 'news': []}
    market = '1' if code.startswith('6') else '0'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    def try_request(url, timeout=30, retries=3):
        for i in range(retries):
            try:
                if HAS_REQUESTS:
                    r = requests.get(url, headers=headers, timeout=timeout)
                    return r.json()
            except Exception as e:
                print(f"  Attempt {i+1} failed: {e}")
                if i < retries - 1:
                    import time
                    time.sleep(2)
        return None
    
    try:
        url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f43,f44,f45,f46,f47,f50,f51,f55,f57,f58,f59,f169,f170,f171"
        data = try_request(url)
        if data and data.get('data'):
            results['quote'] = data['data']
            print("  Quote OK")
    except Exception as e:
        print(f"  Quote failed: {e}")
    try:
        url = f"https://np-anotice-stock.eastmoney.com/api/security/ann?page=true&pageSize=10&stock={code}"
        data = try_request(url)
        if data and data.get('data') and data['data'].get('data'):
            results['news'] = data['data']['data'][:5]
            print("  News OK")
    except Exception as e:
        print(f"  News failed: {e}")
    return results


def parse_quote(data):
    if not data:
        return {}
    return {
        'price': safe_div(data.get('f43'), 100),
        'change_pct': safe_div(data.get('f169'), 100),
        'change': safe_div(data.get('f170'), 100),
        'volume': safe_div(data.get('f46'), 10000),
        'amount': safe_div(data.get('f47'), 100000000),
        'turnover': safe_div(data.get('f50'), 100),
        'pe': safe_div(data.get('f51'), 100),
    }


def analyze_fundamentals(data):
    quote = parse_quote(data.get('quote', {}))
    pe = quote.get('pe', 0)
    if pe <= 0:
        valuation = 'loss'
    elif pe < 20:
        valuation = 'undervalued'
    elif pe < 50:
        valuation = 'fair'
    else:
        valuation = 'overvalued'
    turnover = quote.get('turnover', 0)
    liquidity = 'very_active' if turnover > 10 else 'active' if turnover > 5 else 'normal' if turnover > 2 else 'low'
    return {'valuation': valuation, 'liquidity': liquidity, 'pe': pe}


def analyze_technical(data):
    quote = parse_quote(data.get('quote', {}))
    change_pct = quote.get('change_pct', 0)
    volume = quote.get('volume', 0)
    if change_pct > 3:
        trend = 'strong_up'
    elif change_pct > 0:
        trend = 'slight_up'
    elif change_pct > -3:
        trend = 'slight_down'
    else:
        trend = 'strong_down'
    if change_pct > 7:
        signal = 'overbought'
    elif change_pct < -7:
        signal = 'oversold'
    elif change_pct > 3:
        signal = 'strong'
    elif change_pct < -3:
        signal = 'weak'
    else:
        signal = 'neutral'
    vol_status = 'high_vol' if volume > 15 else 'vol_up' if volume > 8 else 'normal_vol' if volume > 4 else 'low_vol'
    return {'trend': trend, 'signal': signal, 'volume_status': vol_status}


def analyze_sentiment(data):
    quote = parse_quote(data.get('quote', {}))
    change_pct = quote.get('change_pct', 0)
    turnover = quote.get('turnover', 0)
    if change_pct > 7:
        sentiment = 'euphoric'
    elif change_pct > 3:
        sentiment = 'optimistic'
    elif change_pct > 0:
        sentiment = 'cautious'
    elif change_pct > -3:
        sentiment = 'cautious'
    else:
        sentiment = 'panic'
    capital = 'big_inflow' if turnover > 15 else 'inflow' if turnover > 8 else 'balanced' if turnover > 4 else 'outflow'
    return {'market_sentiment': sentiment, 'capital_flow': capital}


def analyze_news(data):
    news_list = data.get('news', [])
    if not news_list:
        return {'headlines': [], 'sentiment': 'no news'}
    headlines = []
    for item in news_list[:5]:
        title = item.get('title', '')[:50]
        date = item.get('showtime', '')
        headlines.append(f"{date} {title}")
    pos_words = ['增长', '突破', '获批', '合作', '利好', '涨停']
    neg_words = ['亏损', '减持', '风险', '调查', '处罚', '跌停']
    pos = sum(1 for h in headlines for w in pos_words if w in h)
    neg = sum(1 for h in headlines for w in neg_words if w in h)
    sentiment = 'positive' if pos > neg else 'negative' if neg > pos else 'neutral'
    return {'headlines': headlines, 'sentiment': sentiment}


def calculate_score(fundamentals, technical, sentiment, news):
    score = 50
    val = fundamentals.get('valuation', '')
    if val == 'undervalued':
        score += 15
    elif val == 'fair':
        score += 5
    elif val == 'overvalued':
        score -= 10
    trend = technical.get('trend', '')
    if 'up' in trend:
        score += 10
    elif 'down' in trend:
        score -= 10
    signal = technical.get('signal', '')
    if 'oversold' in signal:
        score += 10
    elif 'overbought' in signal:
        score -= 5
    ms = sentiment.get('market_sentiment', '')
    if 'optimistic' in ms:
        score += 5
    elif 'panic' in ms:
        score -= 10
    ns = news.get('sentiment', '')
    if 'positive' in ns:
        score += 5
    elif 'negative' in ns:
        score -= 5
    score = max(0, min(100, score))
    
    if score >= 75:
        rec = "强烈推荐买入"
    elif score >= 60:
        rec = "买入"
    elif score >= 40:
        rec = "持有"
    else:
        rec = "卖出"
    
    return score, rec


@app.post("/api/analyze", response_model=StockAnalysisResult)
async def analyze_stock(request: StockAnalysisRequest, current_user: User = Depends(get_current_user)):
    """股票分析接口（需要认证）"""
    try:
        code = request.code
        name = request.name
        
        if not code:
            return StockAnalysisResult(
                success=False,
                message="股票代码不能为空",
                code=code,
                name=name,
                quote=None,
                fundamentals=None,
                technical=None,
                sentiment=None,
                news=None,
                score=None,
                recommendation=None
            )
        
        if not HAS_REQUESTS:
            return StockAnalysisResult(
                success=False,
                message="requests 库未安装",
                code=code,
                name=name,
                quote=None,
                fundamentals=None,
                technical=None,
                sentiment=None,
                news=None,
                score=None,
                recommendation=None
            )
        
        # 获取数据
        data = fetch_stock_data(code, name)
        
        if not data.get('quote'):
            return StockAnalysisResult(
                success=False,
                message="获取股票数据失败",
                code=code,
                name=name,
                quote=None,
                fundamentals=None,
                technical=None,
                sentiment=None,
                news=None,
                score=None,
                recommendation=None
            )
        
        # 分析
        quote_data = parse_quote(data.get('quote', {}))
        fundamentals = analyze_fundamentals(data)
        technical = analyze_technical(data)
        sentiment = analyze_sentiment(data)
        news = analyze_news(data)
        score, recommendation = calculate_score(fundamentals, technical, sentiment, news)
        
        return StockAnalysisResult(
            success=True,
            message="分析完成",
            code=code,
            name=name,
            quote=quote_data,
            fundamentals=fundamentals,
            technical=technical,
            sentiment=sentiment,
            news=news,
            score=score,
            recommendation=recommendation
        )
        
    except Exception as e:
        print(f"股票分析错误: {e}")
        import traceback
        traceback.print_exc()
        return StockAnalysisResult(
            success=False,
            message=f"分析失败: {str(e)}",
            code=request.code,
            name=request.name,
            quote=None,
            fundamentals=None,
            technical=None,
            sentiment=None,
            news=None,
            score=None,
            recommendation=None
        )


# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
