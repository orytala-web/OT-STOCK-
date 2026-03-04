import requests
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# הגדרות סביבה
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימת המניות (ישראל + ארה"ב)
STOCKS = [
    "SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLV", "XLE",
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", "PHOE.TA", "MGDL.TA", "HRL.TA",
    "AZRG.TA", "MELI.TA", "AMOT.TA", "ALHE.TA", "DANE.TA", "AURA.TA", "ISRS.TA",
    "STRS.TA", "TNVH.TA", "WILH.TA", "VICT.TA", "RAMI.TA", "NETO.TA", "TEVA.TA",
    "NICE.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", "ICL.TA", "ORL.TA", "ENOG.TA", "ENER.TA",
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ADBE", "ASML",
    "AMD", "QCOM", "TXN", "INTC", "MU", "AMAT", "LRCX", "ADI", "KLAC", "SNPS",
    "NFLX", "TMUS", "VZ", "T", "DIS", "JPM", "BAC", "WFC", "GS", "MS", "V", "MA",
    "WMT", "COST", "HD", "LOW", "NKE", "SBUX", "PG", "KO", "PEP", "CAT", "GE",
    "XOM", "CVX", "COP", "NEE", "DUK", "LLY", "UNH", "JNJ", "ABBV", "MRK"
]

def get_targeted_news(symbol):
    try:
        clean = symbol.replace(".TA", "")
        is_israeli = ".TA" in symbol
        
        if is_israeli:
            # חיפוש ממוקד באתרים ישראליים מובילים
            hebrew_names = {"POLI": "פועלים", "LUMI": "לאומי", "DISI": "דיסקונט", "BEZQ": "בזק", "AZRG": "עזריאלי", "STRS": "שטראוס"}
            search_term = hebrew_names.get(clean, clean)
            sites = "(site:calcalist.co.il OR site:globes.co.il OR site:themarker.com OR site:bizportal.co.il)"
            query = f"{search_term} {sites}"
            lang, loc = "he", "IL"
        else:
            # חיפוש ממוקד באתרים אמריקאיים מובילים
            sites = "(site:bloomberg.com OR site:reuters.com OR site:cnbc.com OR site:marketwatch.com OR site:finance.yahoo.com)"
            query = f"{clean} {sites}"
            lang, loc = "en", "US"
            
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={loc}&ceid={loc}:{lang}"
        
        r = requests.get(url, timeout=7)
        if "<item>" in r.text:
            title = r.text.split("<title>")[1].split("</title>")[0][:80]
            link = r.text.split("<link>")[1].split("</link>")[0]
            return title + "...", link
    except:
        pass
    return "אין חדשות ממוקדות כרגע", ""

def main():
    il_results, us_results = [], []
    print(f"🚀 סריקה ממוקדת אתרים ל-{len(STOCKS)} מניות...")

    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            
            close = df["Close"].squeeze()
            ma150 = close.rolling(150).mean()
            curr_p, curr_ma = close.iloc[-1], ma150.iloc[-1]
            
            if pd.isna(curr_ma): continue
            dist = (curr_p - curr_ma) / curr_ma
            
            # טווח של 0-4% מהממוצע
            if 0 <= dist <= 0.04:
                news_title, news_url = get_targeted_news(stock)
                data = {
                    "ticker": stock.replace(".TA", ""),
                    "dist": round(dist * 100, 2),
                    "news": news_title,
                    "url": news_url
                }
                if ".TA" in stock:
                    il_results.append(data)
                else:
                    us_results.append(data)
        except: continue

    # מיון ובחירת 10 מכל שוק
    il_top = sorted(il_results, key=lambda x: x['dist'])[:10]
    us_top = sorted(us_results, key=lambda x: x['dist'])[:10]

    today = datetime.today().strftime('%d/%m/%Y')
    msg = f"💎 **דוח הזדמנויות VIP** - {today}\n"
    msg += "ניתוח טכני (MA150) + חדשות ממקורות מובילים\n\n"
    
    msg += "🇮🇱 **ישראל (כלכליסט/גלובס/דה-מרקר):**\n"
    for i, res in enumerate(il_top, 1):
        msg += f"{i}. {res['ticker']} | {res['dist']}%\n📰 {res['news']}\n🔗 {res['url']}\n\n"
    
    msg += "🇺🇸 **ארה\"ב (Bloomberg/CNBC/Reuters):**\n"
    for i, res in enumerate(us_top, 1):
        msg += f"{i}. {res['ticker']} | {res['dist']}%\n📰 {res['news']}\n🔗 {res['url']}\n\n"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True})

if __name__ == "__main__":
    main()
 












