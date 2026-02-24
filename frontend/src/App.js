import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar, Scatter } from 'recharts';
import './App.css';

const API_BASE = 'http://localhost:8000';

// 认证工具函数
const getToken = () => localStorage.getItem('auth_token');
const setToken = (token) => localStorage.setItem('auth_token', token);
const removeToken = () => localStorage.removeItem('auth_token');

const apiRequest = async (url, options = {}) => {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });
  return response;
};

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || '登录失败');
      }

      const data = await response.json();
      setToken(data.access_token);
      onLogin();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>尾盘选股策略回测系统</h1>
        <p className="login-subtitle">请登录以继续</p>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              required
            />
          </div>
          <div className="form-group">
            <label>密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              required
            />
          </div>
          {error && <div className="login-error">{error}</div>}
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? '登录中...' : '登录'}
          </button>
        </form>
        <div className="login-hint">
          <p>提示：用户名 admin</p>
        </div>
      </div>
    </div>
  );
}

function BacktestApp({ onLogout }) {
  const [activeTab, setActiveTab] = useState('backtest');
  const [initialCash, setInitialCash] = useState(100000);
  const [forceRefresh, setForceRefresh] = useState(false);
  const [stockLimit, setStockLimit] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);
  
  const [analyzeCode, setAnalyzeCode] = useState('');
  const [analyzeName, setAnalyzeName] = useState('');
  const [analyzeResult, setAnalyzeResult] = useState(null);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value) => {
    return `${value?.toFixed(2) || '0.00'}%`;
  };

  const handleLogout = async () => {
    try {
      await apiRequest('/api/logout', { method: 'POST' });
    } catch (e) {
      // 忽略登出错误
    }
    removeToken();
    onLogout();
  };

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiRequest('/api/backtest', {
        method: 'POST',
        body: JSON.stringify({
          initial_cash: initialCash,
          force_refresh: forceRefresh,
          stock_limit: stockLimit
        }),
      });

      if (response.status === 401) {
        removeToken();
        onLogout();
        throw new Error('登录已过期，请重新登录');
      }

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || '回测请求失败');
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.message);
      }

      setResult(data);
      if (data.stock_data && Object.keys(data.stock_data).length > 0) {
        setSelectedStock(Object.keys(data.stock_data)[0]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const prepareStockChartData = () => {
    if (!result || !selectedStock || !result.stock_data[selectedStock]) {
      return [];
    }

    const stockData = result.stock_data[selectedStock];
    const trades = result.trades.filter(t => t.symbol === selectedStock);

    return stockData.map(point => {
      const buyTrade = trades.find(t => t.date === point.date && t.action === 'buy');
      const sellTrade = trades.find(t => t.date === point.date && t.action === 'sell');

      return {
        date: point.date,
        close: point.close,
        buy: buyTrade ? point.close : null,
        sell: sellTrade ? point.close : null,
      };
    });
  };

  const prepareEquityChartData = () => {
    if (!result || !result.equity_curve) {
      return [];
    }
    return result.equity_curve;
  };

  const runAnalyze = async () => {
    if (!analyzeCode) {
      setError('请输入股票代码');
      return;
    }
    setAnalyzeLoading(true);
    setError(null);
    setAnalyzeResult(null);
    try {
      const response = await apiRequest('/api/analyze', {
        method: 'POST',
        body: JSON.stringify({
          code: analyzeCode,
          name: analyzeName
        }),
      });

      if (response.status === 401) {
        removeToken();
        onLogout();
        throw new Error('登录已过期，请重新登录');
      }

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || '分析请求失败');
      }

      const data = await response.json();
      setAnalyzeResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzeLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <div className="header-content">
          <div>
            <h1>量化投资系统</h1>
            <p>尾盘选股策略回测与股票分析</p>
          </div>
          <div className="header-actions">
            <div className="tabs">
              <button 
                className={`tab ${activeTab === 'backtest' ? 'active' : ''}`}
                onClick={() => setActiveTab('backtest')}
              >
                回测分析
              </button>
              <button 
                className={`tab ${activeTab === 'analyze' ? 'active' : ''}`}
                onClick={() => setActiveTab('analyze')}
              >
                股票分析
              </button>
            </div>
            <button className="logout-btn" onClick={handleLogout}>
              退出登录
            </button>
          </div>
        </div>
      </header>

      {activeTab === 'backtest' && (
        <div className="control-panel">
          <h2>回测参数</h2>
          <div className="input-group">
            <div className="input-item">
              <label>初始资金</label>
              <input
                type="number"
                value={initialCash}
                onChange={(e) => setInitialCash(Number(e.target.value))}
              />
            </div>
            <div className="input-item">
              <label>股票数量限制</label>
              <input
                type="number"
                value={stockLimit}
                onChange={(e) => setStockLimit(Number(e.target.value))}
              />
            </div>
            <div className="input-item">
              <label>强制刷新数据</label>
              <input
                type="checkbox"
                checked={forceRefresh}
                onChange={(e) => setForceRefresh(e.target.checked)}
              />
            </div>
            <button className="btn" onClick={runBacktest} disabled={loading}>
              {loading ? '回测中...' : '开始回测'}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="error">
          <p>错误: {error}</p>
        </div>
      )}

      {loading && (
        <div className="status-message">
          <div className="loading">
            <div className="spinner"></div>
            <p>正在运行回测，请稍候...</p>
          </div>
        </div>
      )}

      {result && (
        <>
          <div className="metrics">
            <div className="metric-card">
              <div className="label">初始资金</div>
              <div className="value">{formatCurrency(result.initial_cash)}</div>
            </div>
            <div className="metric-card">
              <div className="label">最终资金</div>
              <div className="value">{formatCurrency(result.final_value)}</div>
            </div>
            <div className="metric-card">
              <div className="label">总收益率</div>
              <div className={`value ${result.total_return >= 0 ? 'positive' : 'negative'}`}>
                {formatPercent(result.total_return)}
              </div>
            </div>
            <div className="metric-card">
              <div className="label">夏普比率</div>
              <div className="value">{result.sharpe_ratio?.toFixed(2) || '-'}</div>
            </div>
            <div className="metric-card">
              <div className="label">最大回撤</div>
              <div className="value negative">{formatPercent(result.max_drawdown)}</div>
            </div>
            <div className="metric-card">
              <div className="label">年化收益率</div>
              <div className={`value ${result.annual_return >= 0 ? 'positive' : 'negative'}`}>
                {formatPercent(result.annual_return)}
              </div>
            </div>
            <div className="metric-card">
              <div className="label">总交易次数</div>
              <div className="value">{result.total_trades}</div>
            </div>
            <div className="metric-card">
              <div className="label">盈利次数</div>
              <div className="value positive">{result.winning_trades}</div>
            </div>
            <div className="metric-card">
              <div className="label">亏损次数</div>
              <div className="value negative">{result.losing_trades}</div>
            </div>
          </div>

          <div className="charts">
            <div className="chart-card">
              <h3>策略 vs 基准 - 净值曲线</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={prepareEquityChartData()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                  <XAxis
                    dataKey="date"
                    stroke="#8b949e"
                    tick={{ fill: '#8b949e' }}
                  />
                  <YAxis
                    stroke="#8b949e"
                    tick={{ fill: '#8b949e' }}
                    tickFormatter={(value) => `${(value / 10000).toFixed(0)}万`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }}
                    labelStyle={{ color: '#c9d1d9' }}
                    formatter={(value) => [formatCurrency(value), '']}
                  />
                  <Legend wrapperStyle={{ color: '#c9d1d9' }} />
                  <Line
                    type="monotone"
                    dataKey="strategy"
                    stroke="#667eea"
                    strokeWidth={2}
                    dot={false}
                    name="策略净值"
                  />
                  <Line
                    type="monotone"
                    dataKey="benchmark"
                    stroke="#f85149"
                    strokeWidth={2}
                    dot={false}
                    name="基准净值"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {selectedStock && result.stock_data && result.stock_data[selectedStock] && (
              <div className="chart-card">
                <h3>股票走势图 - {selectedStock}</h3>
                <div className="stock-selector">
                  <select
                    value={selectedStock}
                    onChange={(e) => setSelectedStock(e.target.value)}
                  >
                    {Object.keys(result.stock_data).map(symbol => (
                      <option key={symbol} value={symbol}>{symbol}</option>
                    ))}
                  </select>
                </div>
                <ResponsiveContainer width="100%" height={400}>
                  <ComposedChart data={prepareStockChartData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                    <XAxis
                      dataKey="date"
                      stroke="#8b949e"
                      tick={{ fill: '#8b949e' }}
                    />
                    <YAxis
                      stroke="#8b949e"
                      tick={{ fill: '#8b949e' }}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }}
                      labelStyle={{ color: '#c9d1d9' }}
                    />
                    <Legend wrapperStyle={{ color: '#c9d1d9' }} />
                    <Line
                      type="monotone"
                      dataKey="close"
                      stroke="#58a6ff"
                      strokeWidth={2}
                      dot={false}
                      name="收盘价"
                    />
                    <Scatter
                      dataKey="buy"
                      fill="#3fb950"
                      shape="triangle"
                      strokeWidth={2}
                      name="买入"
                    />
                    <Scatter
                      dataKey="sell"
                      fill="#f85149"
                      shape="triangle"
                      strokeWidth={2}
                      name="卖出"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {result.trades && result.trades.length > 0 && (
            <div className="trades-table">
              <h3>交易记录</h3>
              <table>
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>股票代码</th>
                    <th>操作</th>
                    <th>价格</th>
                  </tr>
                </thead>
                <tbody>
                  {result.trades.map((trade, index) => (
                    <tr key={index}>
                      <td>{trade.date}</td>
                      <td>{trade.symbol}</td>
                      <td className={trade.action}>{trade.action === 'buy' ? '买入' : '卖出'}</td>
                      <td>{trade.price.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {!loading && !result && !error && (
        <div className="status-message">
          <p>点击"开始回测"按钮运行策略回测</p>
        </div>
      )}

      {activeTab === 'analyze' && (
        <div className="analyze-panel">
          <div className="control-panel">
            <h2>股票分析</h2>
            <div className="input-group">
              <div className="input-item">
                <label>股票代码</label>
                <input
                  type="text"
                  value={analyzeCode}
                  onChange={(e) => setAnalyzeCode(e.target.value)}
                  placeholder="例如: 600519"
                />
              </div>
              <div className="input-item">
                <label>股票名称(可选)</label>
                <input
                  type="text"
                  value={analyzeName}
                  onChange={(e) => setAnalyzeName(e.target.value)}
                  placeholder="例如: 贵州茅台"
                />
              </div>
              <button className="btn" onClick={runAnalyze} disabled={analyzeLoading}>
                {analyzeLoading ? '分析中...' : '开始分析'}
              </button>
            </div>
          </div>

          {error && activeTab === 'analyze' && (
            <div className="error">
              <p>错误: {error}</p>
            </div>
          )}

          {analyzeLoading && (
            <div className="status-message">
              <div className="loading">
                <div className="spinner"></div>
                <p>正在进行股票分析，请稍候...</p>
              </div>
            </div>
          )}

          {analyzeResult && analyzeResult.success && (
            <div className="analysis-result">
              <div className="analysis-header">
                <h3>{analyzeResult.code} {analyzeResult.name}</h3>
                <div className={`recommendation ${analyzeResult.recommendation.includes('卖出') ? 'sell' : analyzeResult.recommendation.includes('持有') ? 'hold' : 'buy'}`}>
                  {analyzeResult.recommendation}
                </div>
              </div>
              
              <div className="score-display">
                <div className="score-circle">
                  <span className="score-value">{analyzeResult.score}</span>
                  <span className="score-label">分</span>
                </div>
              </div>

              {analyzeResult.quote && (
                <div className="metrics">
                  <div className="metric-card">
                    <div className="label">当前价格</div>
                    <div className="value">{analyzeResult.quote.price?.toFixed(2) || '-'}</div>
                  </div>
                  <div className="metric-card">
                    <div className="label">涨跌幅</div>
                    <div className={`value ${analyzeResult.quote.change_pct >= 0 ? 'positive' : 'negative'}`}>
                      {analyzeResult.quote.change_pct?.toFixed(2) || '0.00'}%
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="label">换手率</div>
                    <div className="value">{analyzeResult.quote.turnover?.toFixed(2) || '-'}%</div>
                  </div>
                  <div className="metric-card">
                    <div className="label">成交量</div>
                    <div className="value">{analyzeResult.quote.volume?.toFixed(2) || '-'}万</div>
                  </div>
                  <div className="metric-card">
                    <div className="label">PE(TTM)</div>
                    <div className="value">{analyzeResult.quote.pe?.toFixed(2) || '-'}</div>
                  </div>
                </div>
              )}

              {analyzeResult.fundamentals && (
                <div className="analysis-section">
                  <h4>基本面分析</h4>
                  <div className="analysis-tags">
                    <span className={`tag ${analyzeResult.fundamentals.valuation === 'undervalued' ? 'positive' : analyzeResult.fundamentals.valuation === 'overvalued' ? 'negative' : ''}`}>
                      估值: {analyzeResult.fundamentals.valuation === 'undervalued' ? '低估' : analyzeResult.fundamentals.valuation === 'overvalued' ? '高估' : analyzeResult.fundamentals.valuation === 'fair' ? '合理' : '亏损'}
                    </span>
                    <span className="tag">
                      流动性: {analyzeResult.fundamentals.liquidity === 'very_active' ? '非常活跃' : analyzeResult.fundamentals.liquidity === 'active' ? '活跃' : analyzeResult.fundamentals.liquidity === 'normal' ? '一般' : '清淡'}
                    </span>
                  </div>
                </div>
              )}

              {analyzeResult.technical && (
                <div className="analysis-section">
                  <h4>技术面分析</h4>
                  <div className="analysis-tags">
                    <span className={`tag ${analyzeResult.technical.trend?.includes('up') ? 'positive' : analyzeResult.technical.trend?.includes('down') ? 'negative' : ''}`}>
                      趋势: {analyzeResult.technical.trend === 'strong_up' ? '强势上涨' : analyzeResult.technical.trend === 'slight_up' ? '小幅上涨' : analyzeResult.technical.trend === 'slight_down' ? '小幅下跌' : '强势下跌'}
                    </span>
                    <span className={`tag ${analyzeResult.technical.signal === 'overbought' ? 'negative' : analyzeResult.technical.signal === 'oversold' ? 'positive' : ''}`}>
                      信号: {analyzeResult.technical.signal === 'overbought' ? '超买' : analyzeResult.technical.signal === 'oversold' ? '超卖' : analyzeResult.technical.signal === 'strong' ? '强势' : analyzeResult.technical.signal === 'weak' ? '弱势' : '中性'}
                    </span>
                    <span className="tag">
                      量能: {analyzeResult.technical.volume_status === 'high_vol' ? '放量' : analyzeResult.technical.volume_status === 'vol_up' ? '量增' : analyzeResult.technical.volume_status === 'normal_vol' ? '正常' : '缩量'}
                    </span>
                  </div>
                </div>
              )}

              {analyzeResult.sentiment && (
                <div className="analysis-section">
                  <h4>情绪分析</h4>
                  <div className="analysis-tags">
                    <span className={`tag ${analyzeResult.sentiment.market_sentiment === 'optimistic' ? 'positive' : analyzeResult.sentiment.market_sentiment === 'panic' ? 'negative' : ''}`}>
                      市场情绪: {analyzeResult.sentiment.market_sentiment === 'euphoric' ? '狂热' : analyzeResult.sentiment.market_sentiment === 'optimistic' ? '乐观' : analyzeResult.sentiment.market_sentiment === 'cautious' ? '谨慎' : '恐慌'}
                    </span>
                    <span className={`tag ${analyzeResult.sentiment.capital_flow?.includes('inflow') ? 'positive' : analyzeResult.sentiment.capital_flow === 'outflow' ? 'negative' : ''}`}>
                      资金流向: {analyzeResult.sentiment.capital_flow === 'big_inflow' ? '大幅流入' : analyzeResult.sentiment.capital_flow === 'inflow' ? '流入' : analyzeResult.sentiment.capital_flow === 'balanced' ? '平衡' : '流出'}
                    </span>
                  </div>
                </div>
              )}

              {analyzeResult.news && analyzeResult.news.headlines && analyzeResult.news.headlines.length > 0 && (
                <div className="analysis-section">
                  <h4>新闻动态</h4>
                  <p className="news-sentiment">情绪: {analyzeResult.news.sentiment === 'positive' ? '正面' : analyzeResult.news.sentiment === 'negative' ? '负面' : '中性'}</p>
                  <ul className="news-list">
                    {analyzeResult.news.headlines.map((headline, idx) => (
                      <li key={idx}>{headline}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="analysis-disclaimer">
                <p>本分析仅供参考，不构成投资建议。股市有风险，投资需谨慎。</p>
              </div>
            </div>
          )}

          {!analyzeLoading && !analyzeResult && activeTab === 'analyze' && (
            <div className="status-message">
              <p>输入股票代码，点击"开始分析"进行股票分析</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const token = getToken();
    setIsAuthenticated(!!token);
    setIsChecking(false);
  }, []);

  if (isChecking) {
    return (
      <div className="login-container">
        <div className="login-box">
          <div className="loading">
            <div className="spinner"></div>
            <p>加载中...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />;
  }

  return <BacktestApp onLogout={() => setIsAuthenticated(false)} />;
}

export default App;
