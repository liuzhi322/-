import pandas as pd
import yfinance as yf
from datetime import datetime

def get_contest_stocks():
    # 競賽熱門股票觀察清單 (擴充至 50 檔標的)
    stock_list = [
        # 半導體/AI
        "2330.TW", "2317.TW", "2454.TW", "2382.TW", "3231.TW", 
        "2376.TW", "2301.TW", "3037.TW", "6669.TW", "3661.TW",
        "3443.TW", "3017.TW", "2356.TW", "3711.TW", "2357.TW",
        # 重電/綠能
        "1519.TW", "1504.TW", "1513.TW", "1514.TW", "1503.TW",
        # 航運/軍工
        "2603.TW", "2609.TW", "2615.TW", "2634.TW", "8222.TW",
        # 上櫃熱門/中小型飆股 (.TWO)
        "3324.TWO", "3583.TWO", "8054.TWO", "3293.TWO", "3529.TWO",
        "6274.TWO", "3081.TWO", "6223.TWO", "5483.TWO", "8299.TWO",
        # PCB/面板/電子零組件
        "3035.TW", "2303.TW", "2409.TW", "3481.TW", "2324.TW",
        "2337.TW", "2344.TW", "2449.TW", "3008.TW", "2327.TW",
        "2368.TW", "6213.TW", "2360.TW", "2353.TW", "2498.TW"
    ]
    
    selected_stocks = []
    
    for ticker in stock_list:
        try:
            # 修正參數：period 改為 '3mo'
            df = yf.download(ticker, period="3mo", progress=False)
            if len(df) < 20:
                continue
            
            # 處理 MultiIndex 欄位
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
            
            # 取得最新一筆數據
            latest_close = float(close.iloc[-1])
            latest_vol = float(volume.iloc[-1])
            latest_ma5 = float(ma5.iloc[-1])
            latest_ma20 = float(ma20.iloc[-1])
            latest_vol_ma5 = float(vol_ma5.iloc[-1])
            latest_rsi = float(rsi.iloc[-1])
            
            # 競賽高頻門檻：
            # 1. 成交量 > 800 張
            # 2. 站上 5 日線與 20 日線
            # 3. 今日成交量 > 5日均量 1.15 倍
            # 4. RSI > 52 (偏強)
            cond1 = latest_vol > 800 * 1000
            cond2 = (latest_close > latest_ma5) and (latest_close > latest_ma20)
            cond3 = latest_vol > (latest_vol_ma5 * 1.15)
            cond4 = latest_rsi > 52
            
            if cond1 and cond2 and cond3 and cond4:
                selected_stocks.append({
                    'ticker': ticker,
                    'price': round(latest_close, 2),
                    'rsi': round(latest_rsi, 1),
                    'entry': round(latest_close, 2),
                    'stop_loss': round(latest_close * 0.95, 2), # 5% 停損
                    'take_profit': round(latest_close * 1.10, 2) # 10% 停利
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
