import yfinance as yf
import pandas as pd
import ta
import requests
import time
import matplotlib.pyplot as plt
from datetime import datetime
import logging
import sys

# =====================================================================
# CONFIGURATION ÉLITE
# =====================================================================
NTFY_URL = "https://ntfy.sh/votre_topic_secret_2026" # <--- À modifier
TICKERS = [
    "SU.PA", "AIR.PA", "MC.PA", "BNP.PA", "OR.PA", "DG.PA", 
    "BTC-USD", "ETH-USD", "NVDA", "AAPL", "MSFT"
]
UPDATE_INTERVAL = 300  # 5 minutes
VIX_LIMIT = 28         # Seuil de panique macro

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("InstitutionalBot")

class TradingBotV1Elite:
    def __init__(self, tickers):
        self.tickers = tickers
        self.market_data = []

    def get_sentiment(self, ticker):
        """Analyse l'actualité mondiale pour le ticker."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news: return "Neutre ⚪", 0
            titles = [n['title'].lower() for n in news[:5]]
            pos = sum(1 for t in titles if any(w in t for w in ['hausse', 'gain', 'succès', 'contrat', 'croissance', 'achat']))
            neg = sum(1 for t in titles if any(w in t for w in ['chute', 'baisse', 'perte', 'dette', 'inflation', 'vente']))
            score = pos - neg
            return ("Positif ✅" if score > 0 else "Négatif ⚠️" if score < 0 else "Neutre ⚪"), score
        except: return "Inconnu ❓", 0

    def get_vix(self):
        """Récupère l'indice de peur VIX."""
        try:
            vix = yf.download("^VIX", period="1d", interval="5m", progress=False)
            return vix['Close'].iloc[-1]
        except: return 20.0

    def compute_signals(self, ticker):
        """Calcul de la stratégie V1 originale + Analyse graphique."""
        try:
            # Récupération 5 jours en 5min pour le temps réel
            df = yf.download(ticker, period="5d", interval="5m", progress=False)
            if df.empty or len(df) < 50: return None

            # Indicateurs Stratégie V1
            df['EMA200'] = ta.trend.ema_indicator(df['Close'], window=200)
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            macd = ta.trend.MACD(df['Close'])
            df['MACD_Hist'] = macd.macd_diff()
            df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            vix = self.get_vix()
            sentiment_lbl, sentiment_score = self.get_sentiment(ticker)

            # --- ANALYSE GRAPHIQUE (Tendance confirmée via creux ascendants) ---
            lows = df['Low'].rolling(window=10).min()
            is_uptrend = lows.iloc[-1] >= lows.iloc[-10]

            # --- CALCUL DU SCORE DE PROBABILITÉ (0-100) ---
            prob = 0
            if last['Close'] > last['EMA200']: prob += 30
            if last['RSI'] < 45: prob += 20
            if last['MACD_Hist'] > prev['MACD_Hist']: prob += 20
            if is_uptrend: prob += 15
            if vix < VIX_LIMIT: prob += 10
            if sentiment_score > 0: prob += 5

            # --- CALCULS FINANCIERS ---
            atr_2x = last['ATR'] * 2
            sl_suiveur_pct = (atr_2x / last['Close']) * 100
            tp_price = last['Close'] + (atr_2x * 3) # Target Price
            gains_pct = ((tp_price / last['Close']) - 1) * 100

            # --- LOGIQUE DÉCISIONNELLE ---
            action = "VEILLE"
            if prob > 60 and last['RSI'] < 50: action = "ACHAT"
            elif last['RSI'] > 75: action = "VENTE"

            info = yf.Ticker(ticker).info
            return {
                'ticker': ticker, 'nom': info.get('shortName', ticker),
                'secteur': info.get('sector', 'Inconnu'), 'prix': last['Close'],
                'rsi': last['RSI'], 'macd': last['MACD_Hist'], 'vix': vix,
                'ema200': last['EMA200'], 'sl_pct': sl_suiveur_pct,
                'tp': tp_price, 'gains': gains_pct, 'prob': prob,
                'sentiment': sentiment_lbl, 'action': action
            }
        except Exception as e:
            logger.error(f"Erreur sur {ticker}: {e}")
            return None

    def notify(self, d):
        """Envoi vers NTFY."""
        msg = (
            f"🔔 SIGNAL {d['action']} | {d['nom']} ({d['ticker']})\n"
            f"🎯 Probabilité : {d['prob']}%\n"
            f"----------------------------------\n"
            f"💰 Prix : {d['prix']:.2f}€ | VIX : {d['vix']:.1f}\n"
            f"📈 RSI : {d['rsi']:.1f} | EMA200 : {d['ema200']:.2f}\n"
            f"📊 MACD : {'Hausse' if d['macd'] > 0 else 'Baisse'}\n"
            f"🌍 News : {d['sentiment']}\n"
            f"----------------------------------\n"
            f"✅ Achat conseillé : {d['prix']:.2f}€\n"
            f"🏁 Vente conseillée : {d['tp']:.2f}€\n"
            f"🛡️ Stop Loss Suiveur : {d['sl_pct']:.2f}%\n"
            f"🚀 Gain potentiel : +{d['gains']:.2f}%"
        )
        try:
            requests.post(NTFY_URL, data=msg.encode('utf-8'), headers={"Title": f"ALERTE {d['ticker']}"})
        except: pass

    def plot_sectors(self, results):
        """Crée le graphique sectoriel des opportunités d'achat."""
        buys = [r['secteur'] for r in results if r['action'] == "ACHAT"]
        if buys:
            plt.figure(figsize=(8, 6))
            pd.Series(buys).value_counts().plot(kind='pie', autopct='%1.1f%%', colormap='Set3')
            plt.title("Répartition Sectorielle des Signaux d'Achat")
            plt.ylabel('')
            plt.savefig("secteurs.png")
            plt.close()

    def run(self):
        while True:
            logger.info("Début du cycle d'analyse...")
            results = []
            for t in self.tickers:
                data = self.compute_signals(t)
                if data: results.append(data)
            
            # --- TRIAGE DES DONNÉES ---
            # Priorité 1 : ACHAT, Priorité 2 : VENTE, Priorité 3 : Probabilité
            results.sort(key=lambda x: (x['action'] != "ACHAT", x['action'] != "VENTE", -x['prob']))

            print(f"\n--- DASHBOARD {datetime.now().strftime('%H:%M:%S')} ---")
            for res in results:
                print(f"[{res['action']}] {res['ticker'].ljust(8)} | Prob: {res['prob']}% | RSI: {res['rsi']:.1f} | Prix: {res['prix']:.2f}")
                if res['action'] in ["ACHAT", "VENTE"]:
                    self.notify(res)

            self.plot_sectors(results)
            logger.info(f"Cycle terminé. Prochaine mise à jour dans 5 min.")
            time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    bot = TradingBotV1Elite(TICKERS)
    bot.run()
