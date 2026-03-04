import requests
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימה מורחבת (ת"א 125 + מניות בולטות נוספות)
STOCKS = [
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "MZR.TA", "BEZQ.TA", "TEVA.TA", 
    "NICE.TA", "AZRG.TA", "ICL.TA", "ORL.TA", "DSCT.TA", "AVNV.TA", "DEOL.TA", 
    "OPK.TA", "MVNE.TA", "DANE.TA", "SACH.TA", "CLIS.TA", "GSPT.TA", "ALHE.TA",
    "ENGL.TA", "IES.TA", "PSTR.TA", "HRL.TA", "MGDL.TA", "PHOE.TA", "ELTR.TA",
    "ARAD.TA", "DELT.TA", "AMOT.TA", "REIT.TA", "DIMO.TA", "MMHD.TA", "SELA.TA"
]

def detect_patterns(df):
    """מזהה תבניות פריצה ודגל"""
    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    
    patterns = []
    
    # 1. זיהוי פריצה (Breakout) - מחיר סגירה גבוה מהשיא של 20 הימים האחרונים
    recent_high = high.iloc[-21:-1].max()
    if close.iloc[-1] > recent_high:
        patterns.append("פריצה (Breakout)")

    # 2. זיהוי תבנית דגל (Flag) - עלייה חדה ואז דשדוש
    # עלייה של לפחות 5% ב-4 ימים, ואז 3 ימי דשדוש בטווח צר
    move = (close.iloc[-4] - close.iloc[-10]) / close.iloc[-10]
    std_dev = close.iloc[-3:].std() / close.iloc[-3:].mean()
    if move > 0.05 and std_dev < 0.01:
        patterns.append("דגל (Flag)")
        
    return patterns

def calculate_score(df, index_df):
    close_series = df["Close"].squeeze()
    index_close = index_df["Close"].squeeze()

    if len(close_series) < 160: return None

    ma150 = close_series.rolling(150).mean()
    curr_price = close_series.iloc[-1]
    curr_ma = ma150.iloc[-1]

    if pd.isna(curr_ma) or curr_ma == 0: return None

    # ציון בסיסי (קירבה לממוצע ומגמה)
    distance = abs(curr_price - curr_ma) / curr_ma
    score = 0
    
    # קירבה לממוצע 150 (עד 40 נק')
    if distance <= 0.03:
        score += (1 - (distance / 0.03)) * 40
    
    # מגמה חיובית (30 נק')
    if curr_ma > ma150.iloc[-20]:
        score += 30

    # תבניות גרפיות (בונוס של 30 נק')
    patterns = detect_patterns(df)
    if patterns:
        score += 30

    return round(score, 2), patterns

def main():
    results = []
    index_df = yf.download("^TA125.TA", period="1y", progress=False)

    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            
            res = calculate_score(df, index_df)
            if res:
                score, patterns = res
                results.append((stock, score, patterns))
        except: continue

    top_results = sorted(results, key=lambda x: x[1], reverse=True)[:10]

    if not top_results:
        msg = "לא נמצאו הזדמנויות."
    else:
        msg = f"🔍 סריקת בורסת ת"א - {datetime.today().strftime('%d/%m')}\n\n"
        for i, (stock, score, patterns) in enumerate(top_results, 1):
            name = stock.replace(".TA", "")
            pattern_str = f" [{', '.join(patterns)}]" if patterns else ""
            msg += f"{i}. {name}: {score}{pattern_str}\n"

    send_telegram(msg)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

if __name__ == "__main__":
    main()


