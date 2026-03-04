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
    df["MA150"] = df["Close"].rolling(150).mean()
    df["VolumeAvg"] = df["Volume"].rolling(30).mean()

    if len(df) < 160:
        return None

    price = df["Close"].iloc[-1]
    ma150 = df["MA150"].iloc[-1]

    if pd.isna(ma150):
        return None

    distance = abs(price - ma150) / ma150
    slope = df["MA150"].iloc[-1] - df["MA150"].iloc[-10]
    volume_ratio = df["Volume"].iloc[-1] / df["VolumeAvg"].iloc[-1]

    rs = (df["Close"].pct_change(60).iloc[-1] -
          index_df["Close"].pct_change(60).iloc[-1])

    score = 0
    if (distance < 0.02).any():

        score += (1 - distance) * 30

    if slope > 0:
        score += 25

    if (volume_ratio > 1.2).any():
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
        if score:
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
