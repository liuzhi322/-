import pandas as pd
import yfinance as yf
from datetime import datetime

# 台股競賽專用：高頻選股策略
def get_contest_stocks():
    # 競賽熱門股票觀察清單（可隨時自行擴充）
    stock_list = [
        "2330.TW", "2317.TW", "2454.TW", "2382.TW", "3231.TW", 
        "2376.TW", "2301.TW", "3037.TW", "2603.TW", "2609.TW",
        "1519.TW", "1504.TW", "1513.TW", "1514.TW", "3661.TW",
        "3443.TW", "6669.TW", "3324.TWO", "3583.TWO", "8054.TWO"
    ]
    
    selected_stocks = []
    
    for ticker in stock_list:
        try:
            df = yf.download(ticker, period="3m", progress=False)
            if len(df) < 20:
                continue
            
            # 處理 yfinance 的欄位結構
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            close = df['Close']
            volume = df['Volume']
            
            # 計算指標
            ma5 = close.rolling(5).mean()
            ma20 = close.rolling(20).mean()
            vol_ma5 = volume.rolling(5).mean()
            
            # 計算 RSI 14
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 取得最新交易日數據
            latest_close = float(close.iloc[-1])
            latest_vol = float(volume.iloc[-1])
            latest_ma5 = float(ma5.iloc[-1])
            latest_ma20 = float(ma20.iloc[-1])
            latest_vol_ma5 = float(vol_ma5.iloc[-1])
            latest_rsi = float(rsi.iloc[-1])
            
            # 競賽策略門檻：
            # 1. 成交量 > 1,000 張
            # 2. 股價站上 5 日線與 20 日線 (轉強)
            # 3. 今日成交量 > 5日均量 1.2 倍 (放量)
            # 4. RSI > 55 (強勢區)
            cond1 = latest_vol > 1000 * 1000
            cond2 = (latest_close > latest_ma5) and (latest_close > latest_ma20)
            cond3 = latest_vol > (latest_vol_ma5 * 1.2)
            cond4 = latest_rsi > 55
            
            if cond1 and cond2 and cond3 and cond4:
                selected_stocks.append({
                    'ticker': ticker,
                    'price': round(latest_close, 2),
                    'rsi': round(latest_rsi, 1),
                    'entry': round(latest_close, 2),
                    'stop_loss': round(latest_close * 0.95, 2), # 5% 強制停損
                    'take_profit': round(latest_close * 1.10, 2) # 10% 快速停利
                })
        except Exception:
            continue
            
    return selected_stocks

if __name__ == "__main__":
    results = get_contest_stocks()
    print("==========================================")
    print(f"🔥 【競賽高頻爆發股選股結果】 ({datetime.now().strftime('%Y-%m-%d')})")
    print("==========================================")
    if not results:
        print("今日無符合條件個股。")
    else:
        for s in results:
            print(f"📌 股票: {s['ticker']}")
            print(f"   現價: {s['price']} | RSI: {s['rsi']}")
            print(f"   建議買進: {s['entry']} | 停損: {s['stop_loss']} | 停利: {s['take_profit']}")
            print("------------------------------------------")
