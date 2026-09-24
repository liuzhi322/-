import requests
import pandas as pd
from datetime import datetime

def get_all_tw_stocks_contest():
    selected_stocks = []
    
    # 1. 抓取上市股票每日成交資訊 (證交所 API)
    url_twse = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data"
    # 2. 抓取上櫃股票每日成交資訊 (櫃買中心 API)
    url_tpex = "https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&o=json"

    headers = {'User-Agent': 'Mozilla/5.0'}
    
    print("📡 正在抓取全台股 (上市+上櫃) 今日最新資料...")

    try:
        # 處理上市股票
        df_twse = pd.read_csv(url_twse)
        # 欄位: 證券代號, 證券名稱, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數, 特殊標記
        df_twse.columns = [c.strip() for c in df_twse.columns]
        
        for _, row in df_twse.iterrows():
            try:
                code = str(row['證券代號']).strip()
                name = str(row['證券名稱']).strip()
                
                # 過濾掉權證、ETF (只留4碼純股票)
                if len(code) != 4 or not code.isdigit():
                    continue
                
                close_price = float(str(row['收盤價']).replace(',', ''))
                open_price = float(str(row['開盤價']).replace(',', ''))
                high_price = float(str(row['最高價']).replace(',', ''))
                volume_shares = float(str(row['成交股數']).replace(',', ''))
                volume_lots = volume_shares / 1000 # 轉為張數
                
                # 計算今日漲幅
                change = float(str(row['漲跌價差']).replace(',', ''))
                prev_close = close_price - change
                pct_change = ((close_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
                
                # 競賽型全台股篩選條件：
                # 1. 成交量 > 1500 張 (確保流動性足夠，競賽好進好出)
                # 2. 今日大漲 > 3.5% (動能強勁)
                # 3. 收在近乎最高點 (留上影線不超過 1.5%，代表買盤鎖死)
                # 4. 股價 > 10 元 (避開低價水餃股)
                cond1 = volume_lots >= 1500
                cond2 = pct_change >= 3.5
                cond3 = (high_price - close_price) / close_price <= 0.015
                cond4 = close_price >= 10.0
                
                if cond1 and cond2 and cond3 and cond4:
                    selected_stocks.append({
                        'code': code,
                        'name': name,
                        'market': '上市',
                        'price': round(close_price, 2),
                        'pct_change': round(pct_change, 2),
                        'volume': int(volume_lots),
                        'entry': round(close_price, 2),
                        'stop_loss': round(close_price * 0.95, 2), # 5% 停損
                        'take_profit': round(close_price * 1.10, 2) # 10% 停利
                    })
            except Exception:
                continue

    except Exception as e:
        print(f"上市資料抓取失敗: {e}")

    return selected_stocks

if __name__ == "__main__":
    results = get_all_tw_stocks_contest()
    print("==========================================")
    print(f"🔥 【競賽級 - 全台股動能爆發股】 ({datetime.now().strftime('%Y-%m-%d')})")
    print("==========================================")
    if not results:
        print("今日全台股市場中，暫無符合競賽高動能條件的個股。")
    else:
        # 依漲幅排序
        results = sorted(results, key=lambda x: x['pct_change'], reverse=True)
        for s in results:
            print(f"📌 [{s['market']}] {s['code']} {s['name']}")
            print(f"   現價: {s['price']} (漲幅: +{s['pct_change']}%) | 今日成交量: {s['volume']} 張")
            print(f"   建議買進: {s['entry']} | 5%停損: {s['stop_loss']} | 10%停利: {s['take_profit']}")
            print("------------------------------------------")
