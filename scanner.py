import requests
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# הגדרות סביבה
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימה רחבה מאוד
STOCKS = [
    "SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ADBE", "AMD", "QCOM", 
    "NFLX", "TMUS", "VZ", "T", "DIS", "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "WMT", "COST", "HD", "LOW", "NKE", "SBUX", 
    "PG", "KO", "PEP", "CAT", "GE", "XOM", "CVX", "COP", "NEE", "DUK", "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "AMGN", 
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", "PHOE.TA", "MGDL.TA", "HRL.TA", "AZRG.TA", "MELI.TA", "AMOT.TA", 
    "ALHE.TA", "DANE.TA", "AURA.TA", "ISRS.TA", "STRS.TA", "TNVH.TA", "WILH.TA", "VICT.TA", "RAMI.TA", "NETO.TA", "TEVA.TA", 
    "NICE.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", "ICL.TA", "ORL.TA", "ENOG.TA", "ENER.TA", "OPC.TA", "MTRX.TA", "ONE.TA"
]

def get_twitter_backup(search_term):
    """מחפש אזכורים בטוויטר כגיבוי"""
    try:
        # יצירת קישור חיפוש לטוויטר כי API רשמי דורש תשלום יקר
        twitter_url = f"https://twitter.com/search?q={urllib.parse.quote(search_term)}&src=typed_query&f=live"
        return f"לא נמצאו חדשות, בדוק דיבור בטוויטר", twitter_url
    except:
        return None, None

def get_news_with_twitter_fallback(symbol):
    try:
        clean = symbol.replace(".TA", "")
        is_israeli = ".TA" in symbol
        hebrew_names = {"POLI": "בנק הפועלים", "LUMI": "בנק לאומי", "BEZQ": "בזק", "AZRG": "עזריאלי", "TEVA": "טבע"}
        search_term = hebrew_names.get(clean, clean)
        
        # 1. ניסיון בגוגל חדשות
        lang, loc = ("he", "IL") if is_israeli else ("en", "US")
        query = f"{search_term} מניה חדשות" if is_israeli else f"{clean} stock news"
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={loc}&ceid={loc}:{lang}"
        
        r = requests.get(url, timeout=7)
        if "<item>" in r.text:
            title = r.text.split("<title>")[1].split("</title>")[0][:80]
            link = r.text.split("<link>")[1].split("</link>")[0]
            return title + "...", link
        
        # 2. אם אין חדשות - חיפוש בטוויטר
        tw_text, tw_link = get_twitter_backup(search_term)
        return tw_text, tw_link
        
    except:
        return None, None

def main():
    il_results, us_results = [], []
    print("🚀 סריקה רצה: טכני + חדשות + גיבוי טוויטר...")

    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            close = df["Close"].squeeze()
            ma150 = close.rolling(150).mean()
            curr_p, curr_ma = close.iloc[-1], ma150.iloc[-1]
            if pd.isna(curr_ma): continue
            
            dist = (curr_p - curr_ma) / curr_ma
            
            if dist >= 0:
                news_title, news_url = get_news_with_twitter_fallback(stock)
                # אם אין חדשות ואין טוויטר, אנחנו עדיין שומרים את המניה אבל בלי טקסט חדשותי
                data = {"ticker": stock.replace(".TA", ""), "dist": round(dist * 100, 2), "news": news_title, "url": news_url}
                if ".TA" in stock: il_results.append(data)
                else: us_results.append(data)
        except: continue

    # בחירת ה-10 הכי קרובות
    il_top = sorted(il_results, key=lambda x: x['dist'])[:10]
    us_top = sorted(us_results, key=lambda x: x['dist'])[:10]

    today = datetime.today().strftime('%d/%m/%Y')
    msg = f"📊 **דוח הזדמנויות משולב (News & X)** - {today}\n\n"
    
    for section_name, results, emoji in [("ישראל", il_top, "🇮🇱"), ("ארה\"ב", us_top, "🇺🇸")]:
        msg += f"{emoji} **{section_name}:**\n"
        for i, res in enumerate(results, 1):
            news_line = f"📰 {res['news']}" if res['news'] else "בלי חדשות כרגע"
            link_line = f"\n🔗 [לקריאה/דיבור]({res['url']})" if res['url'] else ""
            msg += f"{i}. **{res['ticker']}** | {res['dist']}%\n{news_line}{link_line}\n\n"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True})

if __name__ == "__main__":
    main()

 












