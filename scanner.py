import requests
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# הגדרות סביבה
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימת ה-300 המאוחדת
STOCKS = [
    "SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ADBE", "AMD", "QCOM", 
    "NFLX", "TMUS", "VZ", "T", "DIS", "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "WMT", "COST", "HD", "LOW", "NKE", "SBUX", 
    "PG", "KO", "PEP", "CAT", "GE", "XOM", "CVX", "COP", "NEE", "DUK", "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "AMGN", 
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", "PHOE.TA", "MGDL.TA", "HRL.TA", "AZRG.TA", "MELI.TA", "AMOT.TA", 
    "ALHE.TA", "DANE.TA", "AURA.TA", "ISRS.TA", "STRS.TA", "TNVH.TA", "WILH.TA", "VICT.TA", "RAMI.TA", "NETO.TA", "TEVA.TA", 
    "NICE.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", "ICL.TA", "ORL.TA", "ENOG.TA", "ENER.TA", "OPC.TA", "MTRX.TA", "ONE.TA"
]

def main():
    il_results, us_results = [], []
    print("🚀 סריקה טכנית 10+10 רצה...")

    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            if df.empty or len(df) < 151: continue
            
            close = df["Close"].squeeze()
            ma150 = close.rolling(150).mean()
            curr_p = close.iloc[-1]
            curr_ma = ma150.iloc[-1]
            
            if pd.isna(curr_ma): continue
            dist = (curr_p - curr_ma) / curr_ma
            
            # מחיר מעל הממוצע (תמיכה)
            if dist >= 0:
                # יצירת קישורי חיפוש מהירים במקום סריקה כושלת
                clean = stock.replace(".TA", "")
                if ".TA" in stock:
                    news_link = f"https://www.bizportal.co.il/searchresult?q={clean}"
                    il_results.append({"ticker": clean, "dist": round(dist * 100, 2), "price": round(curr_p, 2), "link": news_link})
                else:
                    news_link = f"https://finance.yahoo.com/quote/{stock}"
                    us_results.append({"ticker": stock, "dist": round(dist * 100, 2), "price": round(curr_p, 2), "link": news_link})
        except: continue

    # מיון ובחירת 10 הכי קרובות
    il_top = sorted(il_results, key=lambda x: x['dist'])[:10]
    us_top = sorted(us_results, key=lambda x: x['dist'])[:10]

    today = datetime.today().strftime('%d/%m/%Y')
    msg = f"🎯 **סורק תמיכה MA150** - {today}\n\n"
    
    msg += "🇮🇱 **בורסת תל אביב (הכי קרובות):**\n"
    for i, res in enumerate(il_top, 1):
        msg += f"{i}. **{res['ticker']}** | {res['dist']}% | {res['price']} ₪\n🔍 [חדשות ונתונים]({res['link']})\n\n"
    
    msg += "🇺🇸 **בורסת ארה\"ב (הכי קרובות):**\n"
    for i, res in enumerate(us_top, 1):
        msg += f"{i}. **{res['ticker']}** | {res['dist']}% | {res['price']}$ \n🔍 [News & Chart]({res['link']})\n\n"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True})

if __name__ == "__main__":
    main()


 












