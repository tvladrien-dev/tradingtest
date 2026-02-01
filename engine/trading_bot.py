import yfinance as yf
import pandas as pd
import ta
import requests
import time
import matplotlib.pyplot as plt
from datetime import datetime
import logging

# === CONFIGURATION ===
NTFY_URL = "https://ntfy.sh/votre_topic_unique" # À CHANGER
TICKERS = ["SU.PA", "AIR.PA", "MC.PA", "BNP.PA", "OR.PA", "BTC-USD", "ETH-USD"]
RISK_FREE_VIX = 25  # Seuil de peur (VIX)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EliteBot")

class EliteTradingBot:
    def __init__(self, tickers):
        self.tickers = tickers
        self.history = []

    def get_news_sentiment(self, ticker):
        """Analyse de l'actualité via Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news: return 0
            titles = [n['title'].lower() for n in news[:5]]
            pos = sum(1 for t in titles if any(w in t for w in ['record', 'gain', 'contrat', 'hausse', 'succès']))
            neg = sum(1 for t in titles if any(w in t for w in ['chute', 'baisse', 'dette', 'perte', 'alerte']))
            return (pos - neg)
        except: return 0

    def compute_indicators(self, ticker):
        """Calcul de la stratégie V1 + Probabilités"""
        # Intervalle 5m pour le temps réel
        df = yf.download(ticker, period="5d", interval="5m", progress=False)
        if len(df) < 50: return None

        # Indicateurs V1
        df['EMA200'] = ta.trend.ema_indicator(df['Close'], window=200)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        macd = ta.trend.MACD(df['Close'])
        df['MACD_Hist'] = macd.macd_diff()
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        vix = yf.download("^VIX", period="1d", interval="5m", progress=False)['Close'].iloc[-1]

        # --- CALCUL PROBABILITÉ (SCORE 0-100) ---
        score = 0
        if last['Close'] > last['EMA200']: score += 30
        if last['RSI'] < 40: score += 25
        if last['MACD_Hist'] > prev['MACD_Hist']: score += 20
        if vix < RISK_FREE_VIX: score += 15
        sentiment = self.get_news_sentiment(ticker)
        if sentiment > 0: score += 10

        # --- LOGIQUE STOP LOSS & GAINS ---
        atr_value = last['ATR'] * 2
        sl_pct = (atr_value / last['Close']) * 100
        tp_price = last['Close'] + (atr_value * 2) # Ratio 1:2
        gains_prevus = ((tp_price / last['Close']) - 1) * 100

        return {
            'ticker': ticker,
            'prix': last['Close'],
            'rsi': last['RSI'],
            'macd': "HAUSSIER" if last['MACD_Hist'] > 0 else "BAISSIER",
            'vix': vix,
            'ema200': last['EMA200'],
            'sl_pct': sl_pct,
            'tp': tp_price,
            'gains_pct': gains_prevus,
            'probabilite': score,
            'sentiment': sentiment,
            'action': "ACHAT" if (score > 60 and last['RSI'] < 45) else ("VENTE" if last['RSI'] > 75 else "VEILLE")
        }

    def generate_sector_chart(self, signals):
        """Génère un graphique des secteurs conseillés"""
        sectors = []
        for s in signals:
            if s['action'] == "ACHAT":
                info = yf.Ticker(s['ticker']).info
                sectors.append(info.get('sector', 'Crypto/Autres'))
        
        if sectors:
            pd.Series(sectors).value_counts().plot(kind='pie', autopct='%1.1f%%', colormap='viridis')
            plt.title("Répartition Sectorielle des Opportunités")
            plt.savefig("secteurs_conseilles.png")
            plt.close()

    def run(self):
        while True:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"--- ACTUALISATION : {now} ---")
            
            results = []
            for t in self.tickers:
                data = self.compute_indicators(t)
                if data: results.append(data)

            # TRI : ACHAT en premier, puis par Probabilité décroissante
            results.sort(key=lambda x: (x['action'] != "ACHAT", -x['probabilite']))

            for res in results:
                print(f"[{res['action']}] {res['ticker']} - Probabilité: {res['probabilite']}%")
                
                # Notification NTFY pour les signaux forts
                if res['action'] in ["ACHAT", "VENTE"]:
                    msg = (
                        f"📢 SIGNAL {res['action']} - Probabilité: {res['probabilite']}%\n"
                        f"Ticker: {res['ticker']}\n"
                        f"Prix: {res['prix']:.2f}€ | VIX: {res['vix']:.1f}\n"
                        f"RSI: {res['rsi']:.1f} | EMA200: {res['ema200']:.2f}\n"
                        f"--------------------------\n"
                        f"🎯 Achat conseillé: {res['prix']:.2f}€\n"
                        f"🏁 Vente conseillée: {res['tp']:.2f}€\n"
                        f"🛡️ Stop Loss Suiveur: {res['sl_pct']:.2f}%\n"
                        f"📈 Gains prévus: +{res['gains_pct']:.2f}%\n"
                        f"🌍 Sentiment News: {res['sentiment']}"
                    )
                    requests.post(NTFY_URL, data=msg.encode('utf-8'))

            self.generate_sector_chart(results)
            print("Graphique sectoriel mis à jour. Prochain scan dans 5 min...")
            time.sleep(300)

if __name__ == "__main__":
    bot = EliteTradingBot(TICKERS)
    bot.run()
