import requests
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימה מורחבת משמעותית - מעל 100 מניות מובילות בישראלSTOCKS = [
    # --- מדדים (ETFs) ---
    "SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLV",

    # --- ישראל: בנקים ופיננסים ---
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", 
    "PHOE.TA", "MGDL.TA", "HRL.TA", "CLIS.TA", "ALTR.TA", "MENO.TA",

    # --- ישראל: נדל"ן ובנייה ---
    "AZRG.TA", "MELI.TA", "AMOT.TA", "ALHE.TA", "DANE.TA", "DIMO.TA", "REIT.TA", 
    "SELA.TA", "MVNE.TA", "GSPT.TA", "ENGL.TA", "ARPT.TA", "BSRE.TA", "PROP.TA",
    "AURA.TA", "AFRE.TA", "IBPR.TA", "ISRS.TA", "GLDS.TA", "ZMH.TA",

    # --- ישראל: מזון, צריכה ופארמה ---
    "STRS.TA", "TNVH.TA", "WILH.TA", "SACH.TA", "VICT.TA", "RAMI.TA", "YCHL.TA", 
    "NETO.TA", "TEVA.TA", "OPK.TA", "ELAL.TA", "DIPL.TA", "FOX.TA", "GOLF.TA",

    # --- ישראל: טכנולוגיה, אנרגיה ותעשייה ---
    "NICE.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", "ICL.TA", "ORL.TA", "SPNS.TA", 
    "AUDC.TA", "GILAT.TA", "MTRX.TA", "ONIT.TA", "ENOG.TA", "ENER.TA", "NVRG.TA", 
    "PZOL.TA", "DLTI.TA", "ELCO.TA", "EVNR.TA",

    # --- ארה"ב: S&P 500 - טכנולוגיה ותקשורת ---
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ADBE", "ASML",
    "AMD", "QCOM", "TXN", "INTC", "MU", "AMAT", "LRCX", "ADI", "KLAC", "SNPS",
    "CDNS", "PANW", "FTNT", "CSCO", "ORCL", "CRM", "ACN", "IBM", "INTU", "NOW",
    "UBER", "ABNB", "SHOP", "NFLX", "TMUS", "VZ", "T", "CMCSA", "DIS", "EA",

    # --- ארה"ב: S&P 500 - פיננסים ---
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "PYPL", "BLK",
    "BX", "AMP", "SCHW", "CB", "MMC", "PGR", "MET", "PRU", "AIG", "TRV",
    "SPGI", "MCO", "ICE", "CME", "COF", "DFS", "SYF", "USB", "TFC", "PNC",

    # --- ארה"ב: S&P 500 - בריאות ופארמה ---
    "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "AMGN", "TMO", "DHR", "ISRG",
    "GILD", "VRTX", "REGN", "BMY", "BSX", "SYK", "ZTS", "BDX", "MCK", "ABC",
    "CI", "CVS", "HCA", "GEHC", "IDXX", "IQV", "EW", "HUM", "MDT", "BAX",

    # --- ארה"ב: S&P 500 - צריכה ותעשייה ---
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "TJX", "EL", "CL",
    "PG", "KO", "PEP", "PM", "MO", "MDLZ", "ADM", "CAT", "DE", "GE",
    "HON", "BA", "LMT", "RTX", "NOC", "GD", "MMM", "UPS", "FDX", "UNP",
    "CSX", "NSC", "ETN", "EMR", "ITW", "PH", "AME", "ROK", "PCAR", "FAST",

    # --- ארה"ב: S&P 500 - אנרגיה ותשתיות ---
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "PXD", "DVN",
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "PCG", "SRE", "ED", "PEG"
]


def calculate_score(df):
    try:
        close = df["Close"].squeeze()
        if len(close) < 160: return None

        ma150 = close.rolling(150).mean()
        curr_price = close.iloc[-1]
        curr_ma = ma150.iloc[-1]

        if pd.isna(curr_ma) or curr_ma == 0: return None

        diff_pct = (curr_price - curr_ma) / curr_ma

        # פילטר: מעל הממוצע ועד 3% מרחק (הגדלנו מ-2%)
        if diff_pct < 0 or diff_pct > 0.03:
            return None

        # ציון: ככל שקרוב יותר ל-0 הציון גבוה יותר
        score = (1 - (diff_pct / 0.03)) * 100
        return round(score, 2), round(diff_pct * 100, 2)
    except:
        return None

def main():
    results = []
    print(f"Scanning {len(STOCKS)} stocks for MA150 support...")
    
    for stock in STOCKS:
        try:
            # מורידים רק את הנתונים הנחוצים כדי לזרז את הסריקה
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            
            res = calculate_score(df)
            if res:
                score, dist = res
                results.append((stock, score, dist))
        except:
            continue

    # מיון לפי הציון הכי גבוה
    top_results = sorted(results, key=lambda x: x[1], reverse=True)[:10]

    today = datetime.today().strftime('%d/%m')
    if not top_results:
        msg = f"Stock Scanner {today}: No stocks found near MA150 support."
    else:
        msg = f"📍 MA150 Entry Opportunities - {today}\n"
        msg += "Stocks near support line (0-3%):\n\n"
        for i, (stock, score, dist) in enumerate(top_results, 1):
            name = stock.replace(".TA", "")
            msg += f"{i}. {name}: Distance {dist}% (Score: {score})\n"

    send_telegram(msg)

def send_telegram(message):
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

if __name__ == "__main__":
    main()





