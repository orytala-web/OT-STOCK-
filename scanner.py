import requests
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# הגדרות סביבה
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימה מאוחדת רחבה: ישראל (ת"א 125) + ארה"ב (S&P 200)
STOCKS = [
    "SPY", "QQQ", "IWM", "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", 
    "AZRG.TA", "MELI.TA", "AMOT.TA", "NICE.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", 
    "ICL.TA", "ORL.TA", "STRS.TA", "TEVA.TA", "AAPL", "MSFT", "GOOGL", "AMZN", 
    "META", "NVDA", "TSLA", "AVGO", "ADBE", "AMD", "QCOM", "NFLX", "JPM", "V", 
    "MA", "COST", "WMT", "DIS", "KO", "PEP", "XOM", "CVX"
]

def get_news_headline(symbol):
    """מושך כותרת חדשות אחרונה"""
    try:
        clean = symbol.replace(".TA", "")
        lang = "he" if ".TA" in symbol else "en"
        loc = "IL" if ".TA" in symbol else "US"
        query = urllib.parse.quote(clean)
        url = f"https://news.google.com/rss/search?q={query}&hl={lang}&gl={loc}&ceid={loc}:{lang}"
        r = requests.get(url, timeout=5)
        if "<item>" in r.text:
            return r.text.split("<title>")[1].split("</title>")[0][:70] + "..."
    except:
        pass
    return "אין דיווחים טריים"

def main():
    final_results = []
    print(f"Starting scan for {len(STOCKS)} stocks...")
    
    for stock in STOCKS:
        try:
            # הורדת נתונים
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            
            # חישוב טכני
            close = df["Close"].squeeze()
            ma150 = close.rolling(150).mean()
            curr_p = close.iloc[-1]
            curr_ma = ma150.iloc[-1]
            
            if pd.isna(curr_ma): continue
            
            dist_pct = (curr_p - curr_ma) / curr_ma
            
            # סינון: רק מניות בטווח של 0% עד 4% מעל הממוצע
            if 0 <= dist_pct <= 0.04:
                news = get_news_headline(stock)
                final_results.append({
                    "ticker": stock.replace(".TA", ""),
                    "dist": round(dist_pct * 100, 2),
                    "news": news
                })
        except:
            continue

    # מיון לפי הקרבה הכי גדולה לממוצע
    final_results = sorted(final_results, key=lambda x: x['dist'])[:15]
    
    # הכנת הודעה
    today = datetime.today().strftime('%d/%m/%Y')
    if not final_results:
        msg = f"🔍 סורק {today}: לא נמצאו מניות קרובות לממוצע 150."
    else:
        msg = f"📍 הזדמנויות MA150 - {today}\n\n"
        for i, res in enumerate(final_results, 1):
            msg += f"{i}. {res['ticker']} | מרחק: {res['dist']}%\n"
            msg += f"📰 {res['news']}\n\n"

    # שליחה לטלגרם
    if TELEGRAM_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("Done. Message sent!")

if __name__ == "__main__":
    main()










