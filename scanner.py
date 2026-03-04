import requests
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# הגדרות סביבה
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימת ה-300 המלאה
STOCKS = [
    "DIA", "XLK", "XLF", "XLV", "XLE",
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", "PHOE.TA", "MGDL.TA", "HRL.TA", "CLIS.TA", "ALTR.TA", "MENO.TA",
    "AZRG.TA", "MELI.TA", "AMOT.TA", "ALHE.TA", "DANE.TA", "DIMO.TA", "REIT.TA", "SELA.TA", "MVNE.TA", "GSPT.TA", "ENGL.TA", 
    "ARPT.TA", "BSRE.TA", "PROP.TA", "AURA.TA", "AFRE.TA", "IBPR.TA", "ISRS.TA", "GLDS.TA", "ZMH.TA",
    "STRS.TA", "TNVH.TA", "WILH.TA", "SACH.TA", "VICT.TA", "RAMI.TA", "YCHL.TA", "NETO.TA", "DIPL.TA", "FOX.TA", "GOLF.TA",
    "NICE.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", "ICL.TA", "ORL.TA", "SPNS.TA", "AUDC.TA", "GILAT.TA", "MTRX.TA", "ONIT.TA", "ENOG.TA", "ENER.TA",
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ADBE", "ASML", "AMD", "QCOM", "TXN", "INTC", "MU", "AMAT", "LRCX", "ADI", "KLAC", "SNPS",
    "CDNS", "PANW", "FTNT", "CSCO", "ORCL", "CRM", "ACN", "IBM", "INTU", "NOW", "UBER", "ABNB", "SHOP", "NFLX", "TMUS", "VZ", "T", "CMCSA", "DIS", "EA",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "PYPL", "BLK", "BX", "AMP", "SCHW", "CB", "MMC", "PGR", "MET", "PRU", "AIG",
    "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "AMGN", "TMO", "DHR", "ISRG", "GILD", "VRTX", "REGN", "BMY", "BSX", "SYK", "ZTS", "BDX", "MCK", "CVS",
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "TJX", "EL", "CL", "PG", "KO", "PEP", "PM", "MO", "MDLZ", "CAT", "DE", "GE", "HON", "BA", "LMT", "RTX",
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "NEE", "DUK", "SO", "D", "AEP", "EXC", "PCG"
]

def get_news_headline(symbol):
    try:
        clean = symbol.replace(".TA", "")
        hebrew_names = {"POLI": "פועלים", "LUMI": "לאומי", "DISI": "דיסקונט", "BEZQ": "בזק", "AZRG": "עזריאלי"}
        search_term = hebrew_names.get(clean, clean)
        lang = "he" if ".TA" in symbol else "en"
        loc = "IL" if ".TA" in symbol else "US"
        query = urllib.parse.quote(search_term)
        url = f"https://news.google.com/rss/search?q={query}&hl={lang}&gl={loc}&ceid={loc}:{lang}"
        r = requests.get(url, timeout=5)
        if "<item>" in r.text:
            return r.text.split("<title>")[1].split("</title>")[0][:75] + "..."
    except: pass
    return "אין חדשות טריות"

def main():
    il_results = []
    us_results = []
    print(f"🚀 סריקה מאוחדת ל-10+10 מניות...")

    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            close = df["Close"].squeeze()
            ma150 = close.rolling(150).mean()
            curr_p, curr_ma = close.iloc[-1], ma150.iloc[-1]
            if pd.isna(curr_ma): continue
            dist = (curr_p - curr_ma) / curr_ma
            
            if 0 <= dist <= 0.04:
                news = get_news_headline(stock)
                data = {"ticker": stock.replace(".TA", ""), "dist": round(dist * 100, 2), "news": news}
                if ".TA" in stock:
                    il_results.append(data)
                else:
                    us_results.append(data)
        except: continue

    # בחירת ה-10 הכי קרובות מכל שוק
    il_top = sorted(il_results, key=lambda x: x['dist'])[:10]
    us_top = sorted(us_results, key=lambda x: x['dist'])[:10]

    today = datetime.today().strftime('%d/%m/%Y')
    msg = f"📊 דוח הזדמנויות MA150 - {today}\n\n"
    
    msg += "🇮🇱 מניות מישראל (Top 10):\n"
    if not il_top: msg += "לא נמצאו מניות בטווח.\n"
    for i, res in enumerate(il_top, 1):
        msg += f"{i}. {res['ticker']} | {res['dist']}%\n📰 {res['news']}\n"
    
    msg += "\n🇺🇸 מניות מארה\"ב (Top 10):\n"
    if not us_top: msg += "לא נמצאו מניות בטווח.\n"
    for i, res in enumerate(us_top, 1):
        msg += f"{i}. {res['ticker']} | {res['dist']}%\n📰 {res['news']}\n"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})

if __name__ == "__main__":
    main()











