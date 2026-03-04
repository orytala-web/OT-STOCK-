import requests
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import urllib.parse

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימת "מפלצת" - ישראל + ארה"ב (מעל 350 מניות)
STOCKS = [
    # --- מדדים ---
    "SPY", "QQQ", "IWM", "DIA",
    # --- ישראל: בנקים, נדל"ן, טכנולוגיה ומזון (ת"א 125+) ---
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", "PHOE.TA", "MGDL.TA", "HRL.TA", 
    "AZRG.TA", "MELI.TA", "AMOT.TA", "ALHE.TA", "DANE.TA", "DIMO.TA", "REIT.TA", "AURA.TA",
    "NICE.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", "ICL.TA", "ORL.TA", "STRS.TA", "TEVA.TA",
    "VICT.TA", "RAMI.TA", "ELAL.TA", "ENOG.TA", "ENER.TA", "OPC.TA", "MTRX.TA", "ONE.TA",
    # --- ארה"ב: ה-200 הגדולות (S&P 200) ---
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ADBE", "ASML",
    "AMD", "QCOM", "TXN", "INTC", "MU", "AMAT", "LRCX", "ADI", "KLAC", "SNPS",
    "CDNS", "PANW", "FTNT", "CSCO", "ORCL", "CRM", "ACN", "IBM", "INTU", "NOW",
    "UBER", "ABNB", "SHOP", "NFLX", "TMUS", "VZ", "T", "CMCSA", "DIS", "EA",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "PYPL", "BLK",
    "BX", "AMP", "SCHW", "CB", "MMC", "PGR", "MET", "PRU", "AIG", "TRV",
    "SPGI", "MCO", "ICE", "CME", "COF", "DFS", "SYF", "USB", "TFC", "PNC",
    "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "AMGN", "TMO", "DHR", "ISRG",
    "GILD", "VRTX", "REGN", "BMY", "BSX", "SYK", "ZTS", "BDX", "MCK", "ABC",
    "CI", "CVS", "HCA", "GEHC", "IDXX", "IQV", "EW", "HUM", "MDT", "BAX",
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "TJX", "EL", "CL",
    "PG", "KO", "PEP", "PM", "MO", "MDLZ", "ADM", "CAT", "DE", "GE",
    "HON", "BA", "LMT", "RTX", "NOC", "GD", "MMM", "UPS", "FDX", "UNP",
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "PXD", "DVN"
]

def get_news(symbol):
    """מחפש חדשות רלוונטיות בגוגל חדשות"""
    clean_name = symbol.replace(".TA", "")
    # תרגום בסיסי למניות ישראליות בולטות לשיפור חיפוש
    hebrew_map = {"POLI": "פועלים", "LUMI": "לאומי", "BEZQ": "בזק", "AZRG": "עזריאלי"}
    search_query = hebrew_map.get(clean_name, clean_name)
    
    encoded = urllib.parse.quote(search_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he" if ".TA" in symbol else f"https://news.google.com/rss/search?q={encoded}&hl=en&gl=US&ceid=US:en"
    
    try:
        r = requests.get(url, timeout=5)
        title = r.text.split("<title>")[1].split("</title>")[0]
        return title[:65] + "..."
    except:
        return "אין חדשות רלוונטיות כרגע"

def main():
    final_picks = []
    print(f"🚀 סריקה מאסיבית מתחילה: {len(STOCKS)} מניות...")
    
    for stock in STOCKS:
        try:
            data = yf.download(stock, period="1y", progress=False)
            if data.empty: continue
            
            close = data["Close"].squeeze()
            ma150 = close.rolling(150).mean()
            
            curr_p = close.iloc[-1]
            curr_ma = ma150.iloc[-1]
            
            if pd.isna(curr_ma): continue
            
            diff = (curr_p - curr_ma) / curr_ma
            
            # פילטר: 0 עד 4% מעל הממוצע
            if 0 <= diff <= 0.04:
                news_headline = get_news(stock)
                final_picks.append({
                    "ticker": stock.replace(".TA", ""),
                    "dist": round(diff * 100, 2),
                    "news": news_headline
                })
        except:
            continue

    # בחירת ה-15 הכי קרובות
    final_picks = sorted(final_picks, key=lambda x: x['dist'])[:15]
    
    date_str = datetime.today().strftime('%d/%m/%Y')
    if not final_picks:
        msg = f"🔍 סריקה גלובלית {date_str}: השוק מתוח, לא נמצאו מניות קרובות לממוצע."
    else:
        msg = f"📊 הזדמנויות קרובות לממוצע 150 - {date_str}\n\n"
        for i, item in enumerate(final_picks, 1):
            msg += f"{i}. {item['ticker']} | מרחק: {item['dist']}%\n"
            msg += f"📰 {item['news']}\n\n"

    send_telegram(msg)

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": message})

if __name__ == "__main__":
    main()

            diff_pct = (curr_price - curr_ma) / curr_ma
            
            # הרחבנו את הטווח ל-5% כדי לוודא שתקבל תוצאות
            if 0 <= diff_pct <= 0.05:
                news = get_israeli_news_simple(stock)
                results.append({
                    "name": stock.replace(".TA", ""),
                    "dist": round(diff_pct * 100, 2),
                    "news": news
                })
        except Exception as e:
            print(f"Error scanning {stock}: {e}")

    # מיון לפי הקרבה לממוצע
    results = sorted(results, key=lambda x: x['dist'])[:10]
    
    today = datetime.today().strftime('%d/%m/%Y')
    if not results:
        msg = f"🔍 סורק {today}: לא נמצאו מניות בטווח של 5% מהממוצע."
    else:
        msg = f"📍 מניות קרובות לתמיכה (MA150) - {today}\n\n"
        for i, res in enumerate(results, 1):
            msg += f"{i}. {res['name']} | מרחק: {res['dist']}%\n"
            msg += f"📰 {res['news']}\n\n"
            
    send_telegram(msg)

def send_telegram(message):
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

if __name__ == "__main__":
    main()









