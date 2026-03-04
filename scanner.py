import requests
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

stocks = [
    "POLI.TA", "BEZQ.TA", "TEVA.TA",
    "LUMI.TA", "NICE.TA", "AZRG.TA"
]

INDEX_SYMBOL = "^TA125.TA"

def calculate_score(df, index_df):
    # הפתרון: הוספת squeeze() כדי לוודא שהנתונים הם רשימה פשוטה ולא טבלה
    close_series = df["Close"].squeeze()
    volume_series = df["Volume"].squeeze()
    index_close_series = index_df["Close"].squeeze()

    ma150_series = close_series.rolling(150).mean()
    volume_avg_series = volume_series.rolling(30).mean()

    if len(close_series) < 160:
        return None

    # עכשיו הנתונים האלו יישלפו כמספרים אמיתיים (Floats)
    price = close_series.iloc[-1]
    ma150 = ma150_series.iloc[-1]

    if pd.isna(ma150):
        return None

    distance = abs(price - ma150) / ma150
    slope = ma150_series.iloc[-1] - ma150_series.iloc[-10]
    volume_ratio = volume_series.iloc[-1] / volume_avg_series.iloc[-1]

    rs = close_series.pct_change(60).iloc[-1] - index_close_series.pct_change(60).iloc[-1]

    score = 0
    
    # מכיוון שהכל עכשיו מספרים, התנאים הפשוטים יעבדו מעולה
    if distance < 0.02:
        score += (1 - distance) * 30

    if slope > 0:
        score += 25

    if volume_ratio > 1.2:
        score += 25

    if rs > 0:
        score += 20

    return round(score, 2)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

def main():
    results = []
    index_df = yf.download(INDEX_SYMBOL, period="1y")

    for stock in stocks:
        df = yf.download(stock, period="1y")
        score = calculate_score(df, index_df)
        if score is not None:
            results.append((stock, score))

    results = sorted(results, key=lambda x: x[1], reverse=True)[:3]

    if not results:
        message = "לא נמצאו מניות מתאימות היום."
    else:
        message = f"📊 סריקה יומית {datetime.today().date()}\n\n"
        for i, (stock, score) in enumerate(results, 1):
            message += f"{i}. {stock} - ציון {score}\n"

    send_telegram(message)

if __name__ == "__main__":
    main()

