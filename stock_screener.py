import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from FinMind.data import DataLoader

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram_msg(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(" Console 輸出：\n", message)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"發送失敗: {e}")

def get_all_taiwan_stock_ids():
    stock_list = []
    try:
        df_twse = pd.read_html("https://isin.twse.com.tw/isin/C_public.jsp?strMode=2")[0]
        df_twse.columns = df_twse.iloc[0]
        df_twse = df_twse.iloc[1:]
        df_tpex = pd.read_html("https://isin.twse.com.tw/isin/C_public.jsp?strMode=4")[0]
        df_tpex.columns = df_tpex.iloc[0]
        df_tpex = df_tpex.iloc[1:]
        df_all = pd.concat([df_twse, df_tpex], ignore_index=True)
        for item in df_all['有價證券代號及名稱'].dropna():
            parts = str(item).split('\u3000')
            if len(parts) >= 2 and len(parts[0].strip()) == 4 and parts[0].strip().isdigit():
                stock_list.append(parts[0].strip())
        return sorted(list(set(stock_list)))
    except:
        return ['2330', '2317', '2454', '2382', '3231', '2603', '2303', '2345', '6669']

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    return 100 - (100 / (1 + (gain / loss)))

def get_chip_data(stock_id, start_date):
    try:
        dl = DataLoader()
        df = dl.taiwan_stock_institutional_investors_recap(stock_id=stock_id, start_date=start_date)
        if df.empty: return 0
        df_latest = df[df['date'] == df['date'].max()]
        return (df_latest['buy'] - df_latest['sell']).sum()
    except:
        return 0

def run_screener():
    all_stocks = get_all_taiwan_stock_ids()
    results = []
    end_date = datetime.today()
    start_date = end_date - timedelta(days=120)
    chip_start = (end_date - timedelta(days=10)).strftime('%Y-%m-%d')
    
    for stock_id in all_stocks:
        ticker = f"{stock_id}.TW"
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) < 60:
                ticker = f"{stock_id}.TWO"
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if len(df) < 60: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df = df.xs(df.columns.levels[1][0], level=1, axis=1)

            latest = df.iloc[-1]
            if float(latest['Volume']) < 1000000: continue

            df['MA5'] = df['Close'].rolling(5).mean()
            df['MA20'] = df['Close'].rolling(20).mean()
            df['MA60'] = df['Close'].rolling(60).mean()
            df['Vol_MA20'] = df['Volume'].rolling(20).mean()
            df['RSI14'] = calculate_rsi(df)

            latest = df.iloc[-1]
            prev_20 = df.iloc[-21:-1]
            
            c1 = (latest['Close'] > latest['MA5']) and (latest['Close'] > latest['MA20']) and (latest['Close'] > latest['MA60'])
            c2 = latest['Volume'] > (latest['Vol_MA20'] * 1.8)
            c3 = latest['Close'] > prev_20['High'].max()
            c4 = 50 < latest['RSI14'] < 75

            if c1 and c2 and c3 and c4:
                inst_buy = get_chip_data(stock_id, chip_start)
                if inst_buy > 0:
                    close_p = float(latest['Close'])
                    low_p = float(latest['Low'])
                    results.append({
                        'stock_id': stock_id,
                        'close': close_p,
                        'vol_ratio': round(float(latest['Volume']/latest['Vol_MA20']), 1),
                        'vol_shares': int(latest['Volume']/1000),
                        'inst_shares': int(inst_buy/1000),
                        'buy_range_low': round(close_p * 0.99, 2),
                        'buy_range_high': round(close_p * 1.01, 2),
                        'stop_loss': round(max(low_p, close_p * 0.95), 2),
                        'take_profit': round(close_p * 1.12, 2)
                    })
        except:
            continue

    today_str = datetime.now().strftime('%Y-%m-%d')
    report = f"🔥 *【台股每日爆發股與買賣策略】* ({today_str})\n"
    report += "="*28 + "\n\n"

    if results:
        for r in results:
            report += f"📌 *股票代號：{r['stock_id']}*\n"
            report += f" ├ 今日收盤價：`${r['close']}`\n"
            report += f" ├ 量能倍數：`{r['vol_ratio']}x` (成交量 {r['vol_shares']} 張)\n"
            report += f" ├ 三大法人買超：`{r['inst_shares']} 張`\n"
            report += " ├ -------------------------\n"
            report += f" ├ 💡 *建議買進時機*：明日開盤小幅拉回接近 `${r['buy_range_low']} ~ ${r['buy_range_high']}` 時分批佈局。\n"
            report += f" ├ 🛑 *建議停損時機*：跌破突破紅K低點 `${r['stop_loss']}` 即刻執行停損。\n"
            report += f" └ 🎯 *建議停利時機*：達目標價 `${r['take_profit']}`（+12% 獲利）分批獲利入袋。\n\n"
    else:
        report += "今日全台股市場中，暫無符合條件的爆發股。\n"

    send_telegram_msg(report)

if __name__ == "__main__":
    run_screener()
