import requests
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימה מורחבת של מניות ישראל (ת"א 125 + מניות יתר בולטות)
STOCKS = [
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "MZR.TA", "BEZQ.TA", "TEVA.TA", 
    "NICE.TA", "AZRG.TA", "ICL.TA", "ORL.TA", "DSCT.TA", "AVNV.TA", "DEOL.TA", 
    "OPK.TA", "MVNE.TA", "DANE.TA", "SACH.TA", "CLIS.TA", "GSPT.TA", "ALHE.TA",
    "ENGL.TA", "IES.TA", "PSTR.TA", "HRL.TA", "MGDL.TA", "PHOE.TA", "ELTR.TA",
    "ARAD.TA", "DELT.TA", "AMOT.TA", "REIT.TA", "DIMO.TA", "MMHD.TA", "SELA.TA",
    "SPNS.TA", "AUDC.TA", "GILAT.TA", "FTAL.TA", "MELI.TA", "ESLT.TA"
]

def detect_patterns(df):
    """מזהה תבניות פריצה ודגל"""
    # מוודא שמשתמשים בנתונים כסדרה פשוטה (Squeeze)
    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    
    if len(close) < 30: return []
    
    patterns = []
    
    # 1. זיהוי פריצה (Breakout)
    recent_high = high.iloc[-21:-1].max()
    if close.iloc[-1] > recent_high:
        patterns.append("Breakout")

    # 2. זיהוי תבנית דגל (Flag)
    move = (close.iloc[-4] - close.iloc[-10]) / close.iloc[-10]
    std_dev = close.iloc[-3:].std() / close.iloc[-3:].mean()
    if move > 0.05 and std_dev < 0.01:
        patterns.append("Flag")
        
    return patterns

def calculate_score(df, index_df):
    try:
        close_series = df["Close"].squeeze()
        index_close = index_df["Close"].squeeze()

        if len(close_series) < 160: return None

        ma150 = close_series.rolling(150).mean()
        curr_price = close_series.iloc[-1]
        curr_ma = ma150.iloc[-1]

        if pd.isna(curr_ma) or curr_ma == 0: return None

        distance = abs(curr_price - curr_ma) / curr_ma
        score = 0
        
        # ניקוד קירבה לממוצע 150
        if distance <= 0.03:
            score += (1 - (distance / 0.03)) * 40
        
        # ניקוד מגמה
        if curr_ma > ma150.iloc[-20]:
            score += 30

        # ניקוד תבניות
        patterns = detect_patterns(df)
        if patterns:
            score += 30

        return round(score, 2), patterns
    except:
        return None

def main():
    results = []
    # הורדת נתוני מדד
    index_df = yf.download("^TA125.TA", period="1y", progress=False)

    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            
            res = calculate_score(df, index_df)
            if res:
                score, patterns = res
                results.append((stock, score, patterns))
        except:
            continue

    # בחירת 10 המניות עם הציון הכי גבוה
    top_results = sorted(results, key=lambda x: x[1], reverse=True)[:10]

    if not top_results:
        msg = "No suitable stocks found today."
    else:
        # בניית ההודעה בצורה בטוחה ללא תווים בעייתיים
        today_str = datetime.today().strftime('%d/%m')
        msg = f"Stock Scanner Israel - {today_str}\n\n"
        for i, (stock, score, patterns) in enumerate(top_results, 1):
            name = stock.replace(".TA", "")
            p_text = f" ({', '.join(patterns)})" if patterns else ""
            msg += f"{i}. {name}: {score}{p_text}\n"

    send_telegram(msg)

def send_telegram(message):
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

if __name__ == "__main__":
    main()



