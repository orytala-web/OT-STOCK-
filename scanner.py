import requests
import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# הגדרות טלגרם
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימה מורחבת (300+ מניות) - ללא מדדים (SPY/QQQ/IWM)
STOCKS = [
    # --- ישראל: ת"א 125 (חלקי) ובנקים ---
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", "PHOE.TA", "MGDL.TA", "HRL.TA", "CLIS.TA", "ALTR.TA",
    "AZRG.TA", "MELI.TA", "AMOT.TA", "ALHE.TA", "DANE.TA", "DIMO.TA", "REIT.TA", "SELA.TA", "MVNE.TA", "AURA.TA",
    "STRS.TA", "TNVH.TA", "WILH.TA", "VICT.TA", "RAMI.TA", "YCHL.TA", "NETO.TA", "DIPL.TA", "FOX.TA", "GOLF.TA",
    "NICE.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", "ICL.TA", "ORL.TA", "SPNS.TA", "AUDC.TA", "GILAT.TA", "MTRX.TA", "ENOG.TA", "TEVA.TA",
    
    # --- ארה"ב: Top 200 S&P ---
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ADBE", "ASML", "AMD", "QCOM", "TXN", "INTC", "MU", "AMAT", 
    "LRCX", "ADI", "KLAC", "SNPS", "CDNS", "PANW", "FTNT", "CSCO", "ORCL", "CRM", "ACN", "IBM", "INTU", "NOW", "UBER", "ABNB", 
    "SHOP", "NFLX", "TMUS", "VZ", "T", "CMCSA", "DIS", "EA", "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "PYPL", 
    "BLK", "BX", "AMP", "SCHW", "CB", "MMC", "PGR", "MET", "PRU", "AIG", "TRV", "SPGI", "MCO", "ICE", "CME", "COF", "DFS", 
    "SYF", "USB", "TFC", "PNC", "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "AMGN", "TMO", "DHR", "ISRG", "GILD", "VRTX", 
    "REGN", "BMY", "BSX", "SYK", "ZTS", "BDX", "MCK", "CI", "CVS", "HCA", "GEHC", "IDXX", "IQV", "EW", "HUM", "MDT", "BAX", 
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "TJX", "EL", "CL", "PG", "KO", "PEP", "PM", "MO", "MDLZ", "ADM", "CAT", 
    "DE", "GE", "HON", "BA", "LMT", "RTX", "NOC", "GD", "MMM", "UPS", "FDX", "UNP", "XOM", "CVX", "COP", "SLB", "EOG", "MPC", 
    "PSX", "VLO", "PXD", "DVN", "NEE", "DUK", "SO", "D", "AEP", "EXC", "PCG", "ED", "PEG", "SRE", "WEC", "AWK", "ECL", "APD"
]

def analyze_stock(df):
    try:
        if len(df) < 151: return None
        
        close = df["Close"].squeeze()
        volume = df["Volume"].squeeze()
        
        # 1. ממוצע 150 ומרחק (הגדלנו מעט את הטווח לזיהוי "זנבות")
        ma150 = close.rolling(150).mean().iloc[-1]
        curr_p = close.iloc[-1]
        dist = (curr_p - ma150) / ma150
        
        # תנאי: 3%- עד 5%+ מהממוצע
        if not (-0.03 <= dist <= 0.05): return None
        
        # 2. ווליום חזק (גבוה מהממוצע של 20 יום)
        avg_vol = volume.rolling(20).mean().iloc[-1]
        curr_vol = volume.iloc[-1]
        vol_ratio = curr_vol / avg_vol
        
        # 3. זיהוי תבנית - פריצת שיא מקומי (20 יום)
        recent_high = close.rolling(20).max().iloc[-1]
        is_breakout = curr_p >= (recent_high * 0.98)
        
        pattern = "🚀 פריצה/דגל" if is_breakout else "🧱 תמיכה MA"
        
        return {
            "dist": round(dist * 100, 2),
            "price": round(curr_p, 2),
            "vol_ratio": round(vol_ratio, 2),
            "pattern": pattern
        }
    except: return None

def main():
    il_results, us_results = [], []
    print(f"Starting Scan for {len(STOCKS)} stocks...")

    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            res = analyze_stock(df)
            if res:
                res["ticker"] = stock.replace(".TA", "")
                if ".TA" in stock: il_results.append(res)
                else: us_results.append(res)
        except: continue

    # מיון לפי עוצמת הווליום (הכי חזקות בראש)
    il_top = sorted(il_results, key=lambda x: x['vol_ratio'], reverse=True)[:10]
    us_top = sorted(us_results, key=lambda x: x['vol_ratio'], reverse=True)[:10]

    today = datetime.today().strftime('%d/%m/%Y')
    msg = f"📊 **דוח תבניות וווליום (300+)** - {today}\n"
    msg += "תנאים: MA150 + מחזור גבוה + תבנית שורית\n\n"
    
    for label, results, emoji in [("מניות ישראל", il_top, "🇮🇱"), ("מניות ארה\"ב", us_top, "🇺🇸")]:
        msg += f"{emoji} **{label}:**\n"
        if not results: msg += "אין מניות שעמדו בכל התנאים היום.\n"
        for res in results:
            msg += f"• **{res['ticker']}** | {res['price']}\n  מרחק MA: {res['dist']}% | ווליום: {res['vol_ratio']}x\n  סוג: {res['pattern']}\n\n"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    main()



 












