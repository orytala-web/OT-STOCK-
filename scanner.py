import requests
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# סימול מדד ת"א 125 כדי לשלוף את רכיביו (או רשימה רחבה אחרת)
# הערה: מכיוון שאין רשימה אוטומטית תמיד ב-yfinance למדד, 
# הכנסתי כאן רשימה מורחבת של המניות המובילות בישראל (ניתן להוסיף עוד)
STOCKS = [
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "MZR.TA", "BEZQ.TA", "TEVA.TA", 
    "NICE.TA", "AZRG.TA", "ICL.TA", "ORL.TA", "DSCT.TA", "AVNV.TA", "DEOL.TA", 
    "OPK.TA", "MVNE.TA", "DANE.TA", "SACH.TA", "CLIS.TA", "GSPT.TA", "ALHE.TA",
    "ENGL.TA", "IES.TA", "PSTR.TA", "HRL.TA", "MGDL.TA", "PHOE.TA", "ELTR.TA"
]

INDEX_SYMBOL = "^TA125.TA"

def calculate_score(df, index_df):
    close_series = df["Close"].squeeze()
    volume_series = df["Volume"].squeeze()
    index_close_series = index_df["Close"].squeeze()

    if len(close_series) < 160:
        return None

    # חישובי אינדיקטורים
    ma150 = close_series.rolling(150).mean()
    ma30_vol = volume_series.rolling(30).mean()
    
    curr_price = close_series.iloc[-1]
    curr_ma = ma150.iloc[-1]
    
    if pd.isna(curr_ma) or curr_ma == 0:
        return None

    # 1. בדיקת קירבה לממוצע 150 (מקסימום 40 נקודות)
    # ככל שהמרחק קטן מ-2%, הניקוד עולה
    distance = abs(curr_price - curr_ma) / curr_ma
    dist_score = 0
    if distance <= 0.03: # עד 3% מרחק
        dist_score = (1 - (distance / 0.03)) * 40

    # 2. בדיקת מגמה חיובית - שיפוע הממוצע (מקסימום 30 נקודות)
    # בודקים אם הממוצע היום גבוה מהממוצע לפני 10 ו-20 ימים
    slope_short = curr_ma - ma150.iloc[-10]
    slope_long = curr_ma - ma150.iloc[-30]
    trend_score = 0
    if slope_short > 0 and slope_long > 0:
        trend_score = 30
    elif slope_short > 0:
        trend_score = 15

    # 3. חוזק יחסי מול המדד (מקסימום 20 נקודות)
    stock_ret = close_series.pct_change(60).iloc[-1]
    index_ret = index_close_series.pct_change(60).iloc[-1]
    rs_score = 0
    if stock_ret > index_ret:
        rs_score = 20 + (min(stock_ret - index_ret, 0.1) * 100) # בונוס על ביצועי עודף

    # 4. אנרגיה - נפח מסחר (מקסימום 10 נקודות)
    vol_ratio = volume_series.iloc[-1] / ma30_vol.iloc[-1]
    vol_score = min(vol_ratio, 2) * 5 

    total_score = dist_score + trend_score + rs_score + vol_score
    return round(total_score, 2)

def main():
    results = []
    print("מתחיל הורדת נתוני מדד...")
    index_df = yf.download(INDEX_SYMBOL, period="1y", progress=False)

    print(f"סורק {len(STOCKS)} מניות...")
    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            
            score = calculate_score(df, index_df)
            if score is not None:
                results.append((stock, score))
        except Exception as e:
            print(f"שגיאה בסריקת {stock}: {e}")

    # מיון ושליפת 10 הטובות ביותר
    top_10 = sorted(results, key=lambda x: x[1], reverse=True)[:10]

    if not top_10:
        message = "לא נמצאו מניות מעניינות בסריקה הנוכחית."
    else:
        message = f"🇮🇱 סורק מניות ישראל - 10 המובילות\n"
        message += f"תאריך: {datetime.today().strftime('%d/%m/%Y')}\n"
        message += f"סינון: קירבה לממוצע 150 ומגמה חיובית\n\n"
        for i, (stock, score) in enumerate(top_10, 1):
            message += f"{i}. {stock.replace('.TA', '')} ➔ ציון: {score}\n"

    print("שולח עדכון לטלגרם...")
    send_telegram(message)

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("חסר TOKEN או CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

if __name__ == "__main__":
    main()

