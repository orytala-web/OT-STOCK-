import requests
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

# הגדרות התחברות
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימת מניות ישראלית רחבה (ת"א 125 + יתר נבחרות)
STOCKS = [
    "POLI.TA", "LUMI.TA", "DISI.TA", "FIBI.TA", "DSCT.TA", "PHOE.TA", "MGDL.TA", "HRL.TA", "CLIS.TA", "ALTR.TA", "MENO.TA",
    "AZRG.TA", "MELI.TA", "AMOT.TA", "ALHE.TA", "DANE.TA", "DIMO.TA", "REIT.TA", "SELA.TA", "MVNE.TA", "GSPT.TA", "ENGL.TA", 
    "ARPT.TA", "BSRE.TA", "PROP.TA", "AURA.TA", "AFRE.TA", "IBPR.TA", "ISRS.TA", "GLDS.TA", "ZMH.TA", "ALON.TA", "AMAL.TA",
    "NICE.TA", "BEZQ.TA", "TSEM.TA", "ESLT.TA", "SPNS.TA", "AUDC.TA", "GILAT.TA", "MTRX.TA", "ONIT.TA", "ONE.TA", "FATT.TA",
    "SKBN.TA", "PLTR.TA", "MAGS.TA", "ENOG.TA", "PSTG.TA", "OPK.TA", "ICL.TA", "ORL.TA", "DEOL.TA", "ENER.TA", "NVRG.TA", 
    "PZOL.TA", "DLTI.TA", "EVNR.TA", "OPC.TA", "KEN.TA", "GCT.TA", "STRS.TA", "TNVH.TA", "WILH.TA", "SACH.TA", "VICT.TA", 
    "RAMI.TA", "YCHL.TA", "NETO.TA", "TEVA.TA", "ELAL.TA", "DIPL.TA", "FOX.TA", "GOLF.TA", "ELCO.TA", "ELECT.TA", "YCDA.TA", 
    "LSTG.TA", "IES.TA", "PSTR.TA", "MSRD.TA", "SMRT.TA", "PLMA.TA", "TLRP.TA", "KBY.TA", "DKL.TA", "IDIN.TA", "AZR.TA"
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
        
        # פילטר קשיח: רק מניות שבין 0% ל-3% מעל הממוצע
        if diff_pct < 0 or diff_pct > 0.03: 
            return None
        
        # ככל שקרוב ל-0, הציון גבוה יותר
        score = (1 - (diff_pct / 0.03)) * 100
        return round(score, 2), round(diff_pct * 100, 2)
    except:
        return None

def main():
    results = []
    print(f"Scanning {len(STOCKS)} Israeli stocks...")
    
    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            
            res = calculate_score(df)
            if res:
                score, dist = res
                results.append((stock, score, dist))
        except:
            continue
            
    top_results = sorted(results, key=lambda x: x[1], reverse=True)[:15]
    today = datetime.today().strftime('%d/%m/%Y')
    
    if not top_results:
        msg = f"🔍 סורק ישראל {today}:\nאין כרגע מניות שנוגעות בממוצע 150. כולן רחוקות מדי או מתחתיו."
    else:
        msg = f"📍 הזדמנויות קרובות לממוצע 150 - {today}\n\n"
        for i, (stock, score, dist) in enumerate(top_results, 1):
            name = stock.replace(".TA", "")
            msg += f"{i}. {name}: מרחק {dist}% (ציון: {score})\n"
            
    send_telegram(msg)

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

if __name__ == "__main__":
    main()







