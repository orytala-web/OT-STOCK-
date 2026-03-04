import requests
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import urllib.parse

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימה מורחבת (דוגמה)
STOCKS = ["POLI.TA", "LUMI.TA", "NICE.TA", "TEVA.TA", "BEZQ.TA", "AZRG.TA", "ICL.TA"]

def get_israeli_news(stock_name):
    """
    מחפש כותרות אחרונות בגוגל חדשות ממוקד לאתרים כלכליים בישראל
    """
    clean_name = stock_name.replace(".TA", "")
    # חיפוש ממוקד באתרים כלכליים מובילים
    query = f"{clean_name} (site:calcalist.co.il OR site:globes.co.il OR site:themarker.com)"
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=he&gl=IL&ceid=IL:he"
    
    try:
        response = requests.get(rss_url, timeout=10)
        # חילוץ כותרות פשוט (בלי ספריות כבדות)
        titles = []
        items = response.text.split("<item>")[1:4] # 3 כותרות ראשונות
        for item in items:
            title = item.split("<title>")[1].split("</title>")[0]
            titles.append(title)
        return titles
    except:
        return []

def calculate_combined_score(stock, df):
    try:
        close = df["Close"].squeeze()
        if len(close) < 160: return None
        
        # ניתוח טכני: קרבה לממוצע 150 (עד 3%)
        ma150 = close.rolling(150).mean()
        curr_price = close.iloc[-1]
        curr_ma = ma150.iloc[-1]
        diff_pct = (curr_price - curr_ma) / curr_ma
        
        if diff_pct < 0 or diff_pct > 0.03: return None
        
        tech_score = (1 - (diff_pct / 0.03)) * 100
        
        # ניתוח חדשות מישראל
        news_headlines = get_israeli_news(stock)
        
        # חיפוש מילות מפתח חיוביות בעברית
        pos_words = ['רווח', 'צמיחה', 'הסכם', 'רכישה', 'חיובי', 'דיבידנד', 'זינוק']
        neg_words = ['הפסד', 'ירידה', 'חקירה', 'קריסה', 'אזהרה', 'תביעה']
        
        sentiment_bonus = 0
        for title in news_headlines:
            for word in pos_words:
                if word in title: sentiment_bonus += 10
            for word in neg_words:
                if word in title: sentiment_bonus -= 15

        return round(tech_score + sentiment_bonus, 2), round(diff_pct * 100, 2), news_headlines
    except:
        return None

def main():
    results = []
    print("סורק מניות ומחפש חדשות באתרים כלכליים...")
    
    for stock in STOCKS:
        try:
            df = yf.download(stock, period="1y", progress=False)
            if df.empty: continue
            
            res = calculate_combined_score(stock, df)
            if res:
                score, dist, headlines = res
                results.append((stock, score, dist, headlines))
        except: continue

    top_results = sorted(results, key=lambda x: x[1], reverse=True)[:10]
    
    today = datetime.today().strftime('%d/%m/%Y')
    msg = f"🇮🇱 סורק משולב: טכני + חדשות ישראל - {today}\n\n"
    
    for i, (stock, score, dist, headlines) in enumerate(top_results, 1):
        name = stock.replace(".TA", "")
        msg += f"{i}. {name} | מרחק: {dist}%\n"
        if headlines:
            msg += f"📰 כותרת: {headlines[0][:60]}...\n"
        msg += f"⭐ ציון משולב: {score}\n\n"
        
    send_telegram(msg)

def send_telegram(message):
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

if __name__ == "__main__":
    main()








