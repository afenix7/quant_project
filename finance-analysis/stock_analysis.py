#!/usr/bin/env python3
import sys
import os
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def fetch_stock_data(code, name=""):
    print(f"Fetching {code} {name}...")
    results = {'quote': {}, 'news': []}
    market = '1' if code.startswith('6') else '0'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f43,f44,f45,f46,f47,f50,f51,f55,f57,f58,f59,f169,f170,f171"
        if HAS_REQUESTS:
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            if data.get('data'):
                results['quote'] = data['data']
                print("  Quote OK")
    except Exception as e:
        print(f"  Quote failed: {e}")
    try:
        url = f"https://np-anotice-stock.eastmoney.com/api/security/ann?page=true&pageSize=10&stock={code}"
        if HAS_REQUESTS:
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            if data.get('data') and data['data'].get('data'):
                results['news'] = data['data']['data'][:5]
                print("  News OK")
    except Exception as e:
        print(f"  News failed: {e}")
    return results


def safe_div(a, b):
    try:
        return float(a) / float(b) if a and b else 0
    except:
        return 0


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
        headlines.append(f"  {date} {title}")
    pos_words = ['增长', '突破', '获批', '合作', '利好', '涨停']
    neg_words = ['亏损', '减持', '风险', '调查', '处罚', '跌停']
    pos = sum(1 for h in headlines for w in pos_words if w in h)
    neg = sum(1 for h in headlines for w in neg_words if w in h)
    sentiment = 'positive' if pos > neg else 'negative' if neg > pos else 'neutral'
    return {'headlines': headlines, 'sentiment': sentiment}


def generate_report(code, name, data, fundamentals, technical, sentiment, news):
    quote = parse_quote(data.get('quote', {}))
    price = quote.get('price', 0)
    change_pct = quote.get('change_pct', 0)
    pe = quote.get('pe', 0)
    volume = quote.get('volume', 0)
    turnover = quote.get('turnover', 0)
    amount = quote.get('amount', 0)
    high = quote.get('high', 0)
    low = quote.get('low', 0)
    open_p = quote.get('open', 0)
    pre_close = quote.get('pre_close', 0)
    
    print("\n" + "=" * 60)
    print(f"  {code} {name} ANALYSIS REPORT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\n[1] QUOTE DATA")
    print(f"  Price: {price:.2f}")
    print(f"  Change: {change_pct:+.2f}%")
    print(f"  Open: {open_p:.2f}")
    print(f"  High: {high:.2f}")
    print(f"  Low: {low:.2f}")
    print(f"  Pre_close: {pre_close:.2f}")
    print(f"  Turnover: {turnover:.2f}%")
    print(f"  Volume: {volume:.2f}M")
    print(f"  Amount: {amount:.2f}B")
    print(f"  PE(TTM): {pe:.2f}" if pe > 0 else "  PE(TTM): loss")
    
    print("\n[2] FUNDAMENTALS")
    print(f"  Valuation: {fundamentals.get('valuation', 'N/A')}")
    print(f"  Liquidity: {fundamentals.get('liquidity', 'N/A')}")
    
    print("\n[3] TECHNICAL")
    print(f"  Trend: {technical.get('trend', 'N/A')}")
    print(f"  Signal: {technical.get('signal', 'N/A')}")
    print(f"  Volume: {technical.get('volume_status', 'N/A')}")
    
    print("\n[4] SENTIMENT")
    print(f"  Market: {sentiment.get('market_sentiment', 'N/A')}")
    print(f"  Capital: {sentiment.get('capital_flow', 'N/A')}")
    
    print("\n[5] NEWS")
    print(f"  Sentiment: {news.get('sentiment', 'N/A')}")
    for h in news.get('headlines', [])[:3]:
        print(h)
    
    print("\n[6] SCORING")
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
        rec = "STRONG BUY"
    elif score >= 60:
        rec = "BUY"
    elif score >= 40:
        rec = "HOLD"
    else:
        rec = "SELL"
    
    print(f"  Score: {score}/100")
    print(f"  Recommendation: {rec}")
    
    print("\n[7] RISK")
    print("  For reference only, not investment advice")
    print("  Stock market has risks")
    
    print("\n" + "=" * 60)
    return {'score': score, 'recommendation': rec}


def save_md(code, name, data, result):
    import os
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    os.makedirs(report_dir, exist_ok=True)
    quote = parse_quote(data.get('quote', {}))
    filename = os.path.join(report_dir, f"{code}_{datetime.now().strftime('%Y%m%d')}.md")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# {code} {name} Report\n\n")
        f.write(f"**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write("## Quote\n\n")
        f.write(f"- Price: {quote.get('price', 0):.2f}\n")
        f.write(f"- Change: {quote.get('change_pct', 0):+.2f}%\n")
        f.write(f"- Turnover: {quote.get('turnover', 0):.2f}%\n\n")
        f.write("## Result\n\n")
        f.write(f"- **Score**: {result['score']}/100\n")
        f.write(f"- **Recommendation**: {result['recommendation']}\n\n")
        f.write("---\n*Reference only*\n")
    print(f"\nSaved: {filename}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python stock_analysis.py <code> [name]")
        print("Ex: python stock_analysis.py 603893 瑞芯微")
        sys.exit(1)
    
    code = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else ""
    
    print("=" * 50)
    print("  TradingAgents Stock Analyzer")
    print("=" * 50)
    print(f"Stock: {code} {name}")
    
    if not HAS_REQUESTS:
        print("Please install requests: pip install requests")
        sys.exit(1)
    
    data = fetch_stock_data(code, name)
    
    if not data.get('quote'):
        print("Failed to fetch data")
        sys.exit(1)
    
    fundamentals = analyze_fundamentals(data)
    technical = analyze_technical(data)
    sentiment = analyze_sentiment(data)
    news = analyze_news(data)
    
    result = generate_report(code, name, data, fundamentals, technical, sentiment, news)
    save_md(code, name, data, result)


if __name__ == "__main__":
    main()
