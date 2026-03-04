import requests
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימה מורחבת משמעותית - מעל 100 מניות מובילות בישראל
STOCKS = [
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "MZR.TA", "BEZQ.TA", "TEVA.TA", 
    "NICE.TA", "AZRG.TA", "ICL.TA", "ORL.TA", "DSCT.TA", "AVNV.TA", "DEOL.TA", 
    "OPK.TA", "MVNE.TA", "DANE.TA", "SACH.TA", "CLIS.TA", "GSPT.TA", "ALHE.TA",
    "ENGL.TA", "IES.TA", "PSTR.TA", "HRL.TA", "MGDL.TA", "PHOE.TA", "ELTR.TA",
    "ARAD.TA", "DELT.TA", "AMOT.TA", "REIT.TA", "DIMO.TA", "MMHD.TA", "SELA.TA",
    "SPNS.TA", "AUDC.TA", "GILAT.TA", "FTAL.TA", "MELI.TA", "ESLT.TA", "ALTR.TA",
    "ALON.TA", "AMAL.TA", "ARPT.TA", "ASRT.TA", "BOLI.TA", "BYNR.TA", "CAAS.TA",
    "CEL.TA", "DLTI.TA", "DRCO.TA", "ELCO.TA", "ELWS.TA", "ENOG.TA", "ENER.TA",
    "GCT.TA", "GGR.TA", "GLAT.TA", "GRE.TA", "ILDC.TA", "INRM.TA", "ISTR.TA",
    "MTRX.TA", "MREIT.TA", "NETO.TA", "NVMI.TA", "PSTG.TA", "PTNR.TA", "SKBN.TA",
    "TSEM.TA", "VTRK.TA", "WIX.TA", "YCDA.TA", "ZIM.TA", # רשימת מניות משולבת: ישראל + ארה"ב (כדי להבטיח תוצאות)
    # --- מדדים מובילים (ETFs) ---
    "SPY", "QQQ", "IWM", "DIA", # S&P 500, Nasdaq, Russell 2000, Dow Jones

    # --- ישראל: בנקים ופיננסים ---
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", "PHOE.TA", "MGDL.TA", "HRL.TA", "CLIS.TA",

    # --- ישראל: נדל"ן ובנייה ---
    "AZRG.TA", "MELI.TA", "AMOT.TA", "ALHE.TA", "DANE.TA", "DIMO.TA", "REIT.TA", "SELA.TA", 
    "MVNE.TA", "GSPT.TA", "ENGL.TA", "ARPT.TA", "BSRE.TA", "PROP.TA",

    # --- ישראל: מזון וצריכה ---
    "STRS.TA", "TNVH.TA", "WILH.TA", "SACH.TA", "VICT.TA", "RAMI.TA", "YCHL.TA", "NETO.TA",

    # --- ישראל: טכנולוגיה ותעשייה ---
    "NICE.TA", "TEVA.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", "ICL.TA", "ORL.TA", "SPNS.TA", 
    "AUDC.TA", "GILAT.TA", "OPK.TA", "MTRX.TA", "ONIT.TA", "ALTR.TA",

    # --- ארה"ב: מניות צמיחה וטכנולוגיה (מלא) ---
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD", "NFLX", "AVGO", 
    "QCOM", "INTC", "CSCO", "PYPL", "ADBE", "CRM", "ABNB", "Airbnb", "UBER", "PANW",

    # --- ארה"ב: פיננסים וצריכה ---
    "JPM", "BAC", "WFC", "V", "MA", "DIS", "KO", "PEP", "COST", "WMT", "NKE", "SBUX"
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





