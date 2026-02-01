import yfinance as yf
import pandas as pd
import ta
import requests
import matplotlib.pyplot as plt
import logging
import time
from datetime import datetime

# Configuration rigoureuse du logging pour Streamlit
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    Moteur de Trading Haute Précision
    Analyse Long Terme (2 ans) + Exécution Intra-day (5 min)
    """
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        # Remplace par ton propre lien NTFY ou secret
        self.ntfy_url = "https://ntfy.sh/trading_bot_pea_2026" 

    def get_news_sentiment(self, ticker):
        """Analyse le sentiment basé sur les derniers titres de presse."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news:
                return "Neutre ⚪", 0
            
            positive_keywords = ['hausse', 'croissance', 'succès', 'achat', 'profit', 'contrat', 'excédent']
            negative_keywords = ['chute', 'baisse', 'perte', 'déficit', 'alerte', 'litige', 'inflation']
            
            score = 0
            recent_titles = [n['title'].lower() for n in news[:5]]
            for title in recent_titles:
                for pw in positive_keywords:
                    if pw in title: score += 1
                for nw in negative_keywords:
                    if nw in title: score -= 1
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except Exception as e:
            logger.warning(f"Sentiment indisponible pour {ticker}: {e}")
            return "Indisponible ❓", 0

    def process_ticker(self, ticker):
        """Analyse complète multi-timeframe pour un ticker donné."""
        try:
            # --- PHASE 1 : ANALYSE TENDANCE 2 ANS (Daily) ---
            # Yahoo permet 2y en intervalle '1d' sans problème
            df_long = yf.download(ticker, period="2y", interval="1d", progress=False, threads=False)
            
            if df_long.empty or len(df_long) < 200:
                logger.error(f"{ticker} : Données historiques (2 ans) insuffisantes.")
                return None

            # Moyenne Mobile Exponentielle 200 (Le juge de paix du trader)
            df_long['EMA200'] = ta.trend.ema_indicator(df_long['Close'], window=200)
            ema200_long = float(df_long['EMA200'].iloc[-1])

            # --- PHASE 2 : ANALYSE TIMING (5 Minutes) ---
            # On récupère le max autorisé par Yahoo pour du 5min (60 jours)
            df_now = yf.download(ticker, period="60d", interval="5m", progress=False, threads=False)

            if df_now.empty:
                logger.error(f"{ticker} : Données 5min introuvables.")
                return None

            # Calcul des indicateurs techniques sur le flux 5 min
            df_now['RSI'] = ta.momentum.rsi(df_now['Close'], window=14)
            macd_obj = ta.trend.MACD(df_now['Close'])
            df_now['MACD_Hist'] = macd_obj.macd_diff()
            df_now['ATR'] = ta.volatility.average_true_range(df_now['High'], df_now['Low'], df_now['Close'])
            
            # Extraction des dernières valeurs scalaires
            last_close = float(df_now['Close'].iloc[-1])
            last_rsi = float(df_now['RSI'].iloc[-1])
            last_macd_h = float(df_now['MACD_Hist'].iloc[-1])
            prev_macd_h = float(df_now['MACD_Hist'].iloc[-2])
            last_atr = float(df_now['ATR'].iloc[-1])

            # --- PHASE 3 : MACRO & SENTIMENT ---
            vix_data = yf.download("^VIX", period="1d", progress=False)
            vix_price = float(vix_data['Close'].iloc[-1]) if not vix_data.empty else 20.0
            sentiment_label, sentiment_score = self.get_news_sentiment(ticker)

            # --- PHASE 4 : LOGIQUE DE SCORE (PROBABILITÉ) ---
            prob = 0
            # 1. Tendance de fond (Daily vs 2 ans) : Crucial
            if last_close > ema200_long: 
                prob += 40 
            
            # 2. Timing RSI (5 min) : Zone de rebond
            if last_rsi < 40: prob += 25
            elif last_rsi < 55: prob += 15
            
            # 3. Momentum MACD (5 min) : Accélération
            if last_macd_h > prev_macd_h: prob += 20
            
            # 4. Contexte Marché (VIX)
            if vix_price < 22: prob += 15
            elif vix_price > 30: prob -= 20 # Pénalité forte si panique marché

            # --- PHASE 5 : GESTION DU RISQUE (ATR DYNAMIQUE) ---
            # Stop Loss à 2x l'ATR (adapté à la volatilité 5 min)
            sl_value = last_atr * 2
            sl_percent = (sl_value / last_close) * 100
            
            # Take Profit à 3.5x l'ATR (Ratio Risk/Reward > 1.5)
            tp_price = last_close + (last_atr * 3.5)
            potential_gain = ((tp_price / last_close) - 1) * 100

            # --- PHASE 6 : DÉCISION FINALE ---
            action = "VEILLE"
            if prob >= 75 and last_rsi < 50:
                action = "ACHAT"
            elif last_rsi > 80:
                action = "VENTE"

            # Récupération secteur pour le graphique
            info = yf.Ticker(ticker).info
            sector = info.get('sector', 'Divers')

            return {
                'ticker': ticker,
                'nom': info.get('shortName', ticker),
                'secteur': sector,
                'prix': last_close,
                'rsi': last_rsi,
                'vix': vix_price,
                'ema200': ema200_long,
                'macd_evol': "Hausse" if last_macd_h > prev_macd_h else "Baisse",
                'sl_pct': sl_percent,
                'tp': tp_price,
                'gains_potentiels': potential_gain,
                'probabilite': prob,
                'sentiment': sentiment_label,
                'action': action,
                'last_update': datetime.now().strftime("%H:%M:%S")
            }

        except Exception as e:
            logger.error(f"Erreur fatale sur {ticker}: {str(e)}")
            return None

    def plot_sectors(self, results):
        """Génère une visualisation des opportunités par secteur."""
        buys = [r['secteur'] for r in results if r['action'] == "ACHAT"]
        if not buys:
            logger.info("Aucun achat détecté, graphique sectoriel sauté.")
            return None
        
        plt.figure(figsize=(12, 7), facecolor='#0E1117')
        data = pd.Series(buys).value_counts()
        
        colors = ['#22C55E', '#16A34A', '#15803D', '#166534', '#14532D']
        plt.pie(data, labels=data.index, autopct='%1.1f%%', startangle=140,
                textprops={'color': "white", 'weight': 'bold'}, colors=colors)
        
        plt.title("Répartition Sectorielle des Signaux d'Achat", color="white", fontsize=14)
        path = "secteurs_conseilles.png"
        plt.savefig(path, dpi=100)
        plt.close()
        return path

    def send_notification(self, data):
        """Envoie une alerte formatée vers NTFY."""
        if data['action'] == "VEILLE":
            return
        
        emoji = "🟢" if data['action'] == "ACHAT" else "🔴"
        title = f"{emoji} {data['action']} {data['ticker']} - Score: {data['probabilite']}%"
        
        message = (
            f"🎯 Actif : {data['nom']} ({data['ticker']})\n"
            f"💰 Prix : {data['prix']:.2f}€\n"
            f"📈 Probabilité : {data['probabilite']}%\n"
            f"--------------------------------\n"
            f"📊 RSI : {data['rsi']:.1f} | VIX : {data['vix']:.1f}\n"
            f"📉 EMA 200 (2 ans) : {data['ema200']:.2f}€\n"
            f"📰 Sentiment : {data['sentiment']}\n"
            f"--------------------------------\n"
            f"🛡️ Stop Loss : -{data['sl_pct']:.2f}%\n"
            f"🚀 Objectif TP : {data['tp']:.2f}€ (+{data['gains_potentiels']:.2f}%)\n"
            f"⏰ Signal généré à : {data['last_update']}"
        )

        try:
            requests.post(
                self.ntfy_url,
                data=message.encode('utf-8'),
                headers={
                    "Title": title,
                    "Priority": "urgent" if data['probabilite'] > 85 else "default",
                    "Tags": "money_with_wings,chart_with_upwards_trend"
                }
            )
        except Exception as e:
            logger.error(f"Erreur notification : {e}")
