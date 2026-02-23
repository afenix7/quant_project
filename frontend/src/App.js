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
  const [initialCash, setInitialCash] = useState(100000);
  const [forceRefresh, setForceRefresh] = useState(false);
  const [stockLimit, setStockLimit] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);

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

  return (
    <div className="container">
      <header className="header">
        <div className="header-content">
          <div>
            <h1>尾盘选股策略 - 回测系统</h1>
            <p>基于均线多头排列的尾盘选股策略回测分析</p>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            退出登录
          </button>
        </div>
      </header>

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
