import yfinance as yf
import pandas as pd
import ta
import requests
import matplotlib.pyplot as plt
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingEngine")

class TradingBotV1Elite:
    """
    Moteur de Trading Hybride V1 "Elite"
    Analyse 2 ans (Tendance) + 60 jours (Timing 5min)
    """
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        self.ntfy_url = "https://ntfy.sh/votre_topic_unique_2026" # À personnaliser

    def get_news_sentiment(self, ticker):
        """Analyse textuelle du sentiment des news via Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news:
                return "Neutre ⚪", 0
            
            # Analyse des 5 derniers titres
            titles = [n['title'].lower() for n in news[:5]]
            pos_words = ['hausse', 'gain', 'contrat', 'croissance', 'succès', 'achat', 'record']
            neg_words = ['baisse', 'chute', 'perte', 'dette', 'inflation', 'vente', 'litige']
            
            score = 0
            for title in titles:
                score += sum(1 for w in pos_words if w in title)
                score -= sum(1 for w in neg_words if w in title)
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except Exception as e:
            logger.warning(f"Sentiment indisponible pour {ticker}: {e}")
            return "Indisponible ❓", 0

    def process_ticker(self, ticker):
        """Analyse complète d'un actif avec stratégie multi-timeframe."""
        try:
            # --- 1. ACQUISITION DES DONNÉES ---
            # Données Journalières (2 ans) pour l'EMA 200
            df_daily = yf.download(ticker, period="2y", interval="1d", progress=False)
            # Données Intra-day (60j max pour intervalle 5m) pour le timing
            df_now = yf.download(ticker, period="60d", interval="5m", progress=False)

            if df_daily.empty or df_now.empty or len(df_now) < 50:
                logger.error(f"Données insuffisantes pour {ticker}")
                return None

            # --- 2. INDICATEURS LONG TERME (SUR 2 ANS) ---
            df_daily['EMA200'] = ta.trend.ema_indicator(df_daily['Close'], window=200)
            ema200_long = float(df_daily['EMA200'].iloc[-1])

            # --- 3. INDICATEURS TEMPS RÉEL (SUR 5 MIN) ---
            # RSI
            df_now['RSI'] = ta.momentum.rsi(df_now['Close'], window=14)
            # MACD
            macd = ta.trend.MACD(df_now['Close'])
            df_now['MACD_Hist'] = macd.macd_diff()
            # ATR (Volatilité pour Stop Loss)
            df_now['ATR'] = ta.volatility.average_true_range(df_now['High'], df_now['Low'], df_now['Close'])
            
            # Valeurs actuelles
            last_close = float(df_now['Close'].iloc[-1])
            last_rsi = float(df_now['RSI'].iloc[-1])
            last_macd_hist = float(df_now['MACD_Hist'].iloc[-1])
            prev_macd_hist = float(df_now['MACD_Hist'].iloc[-2])
            last_atr = float(df_now['ATR'].iloc[-1])

            # --- 4. ANALYSE MACRO & SENTIMENT ---
            vix_data = yf.download("^VIX", period="1d", progress=False)
            vix_price = float(vix_data['Close'].iloc[-1]) if not vix_data.empty else 20.0
            sentiment_label, sentiment_score = self.get_news_sentiment(ticker)

            # --- 5. CALCUL DE LA PROBABILITÉ (SCORE 0-100) ---
            prob = 0
            if last_close > ema200_long: prob += 35      # Tendance de fond (2 ans)
            if last_rsi < 45: prob += 25                # Zone de survente/opportunité
            if last_macd_hist > prev_macd_hist: prob += 20 # Accélération haussière
            if vix_price < 25: prob += 15               # Calme macro-économique
            if sentiment_score > 0: prob += 5           # News positives

            # --- 6. GESTION DU RISQUE (STOP LOSS & TAKE PROFIT) ---
            # Stop Loss Suiveur basé sur 2x l'ATR
            sl_suiveur_val = last_atr * 2
            sl_pct = (sl_suiveur_val / last_close) * 100
            # Take Profit à 3x l'ATR pour un ratio risque/récompense de 1:1.5
            tp_price = last_close + (last_atr * 3)
            potential_gain = ((tp_price / last_close) - 1) * 100

            # --- 7. DÉCISION ---
            action = "VEILLE"
            if prob >= 70 and last_rsi < 50:
                action = "ACHAT"
            elif last_rsi > 75:
                action = "VENTE"

            # Récupération infos société
            info = yf.Ticker(ticker).info
            
            return {
                'ticker': ticker,
                'nom': info.get('shortName', ticker),
                'secteur': info.get('sector', 'Inconnu'),
                'prix': last_close,
                'rsi': last_rsi,
                'vix': vix_price,
                'ema200': ema200_long,
                'macd_status': "HAUSSIER" if last_macd_hist > prev_macd_hist else "STAGNANT",
                'sl_pct': sl_pct,
                'tp': tp_price,
                'gains_pct': potential_gain,
                'probabilite': prob,
                'sentiment': sentiment_label,
                'action': action,
                'horodatage': datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de {ticker}: {e}")
            return None

    def plot_sectors(self, results):
        """Génère un diagramme circulaire des secteurs où des signaux d'achat sont détectés."""
        buys = [r['secteur'] for r in results if r['action'] == "ACHAT"]
        if not buys:
            return None
        
        plt.figure(figsize=(10, 6), facecolor='#0E1117')
        s_counts = pd.Series(buys).value_counts()
        colors = ['#00FF41', '#008F11', '#003B00', '#005C00']
        
        plt.pie(s_counts, labels=s_counts.index, autopct='%1.1f%%', 
                startangle=140, textprops={'color':"w"}, colors=colors)
        plt.title("Répartition des Opportunités d'Achat par Secteur", color="w")
        plt.savefig("secteurs_conseilles.png")
        plt.close()
        return "secteurs_conseilles.png"

    def send_notification(self, d):
        """Envoie une alerte complète et formatée via NTFY."""
        emoji = "🚀" if d['action'] == "ACHAT" else "💰"
        title = f"ALERTE {d['action']} : {d['ticker']} ({d['probabilite']}%)"
        
        msg = (
            f"{emoji} SIGNAL : {d['action']}\n"
            f"📈 Probabilité : {d['probabilite']}%\n"
            f"--------------------------------\n"
            f"💵 Prix Actuel : {d['prix']:.2f}€\n"
            f"📊 RSI : {d['rsi']:.1f} | VIX : {d['vix']:.1f}\n"
            f"📉 EMA200 (2 ans) : {d['ema200']:.2f}€\n"
            f"🌍 News : {d['sentiment']}\n"
            f"--------------------------------\n"
            f"🛡️ STOP LOSS SUIVEUR : -{d['sl_pct']:.2f}%\n"
            f"🎯 OBJECTIF (TP) : {d['tp']:.2f}€\n"
            f"💰 GAIN POTENTIEL : +{d['gains_pct']:.2f}%\n"
            f"⏰ Heure : {d['horodatage']}"
        )
        
        try:
            response = requests.post(
                self.ntfy_url,
                data=msg.encode('utf-8'),
                headers={
                    "Title": title,
                    "Priority": "high",
                    "Tags": "chart_with_upwards_trend,moneybag"
                }
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur d'envoi NTFY : {e}")
            return False

# Fin du fichier trading_bot.py
