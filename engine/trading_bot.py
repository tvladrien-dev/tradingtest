import yfinance as yf
import pandas as pd
import ta
import requests
import matplotlib.pyplot as plt
import logging
from datetime import datetime

# Configuration rigoureuse du logging pour Streamlit
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    Moteur de Trading Haute Précision - Version Daily Intégrale
    Analyse historique (2 ans) pour détection de tendances lourdes.
    """
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        # Lien NTFY pour les alertes (à personnaliser)
        self.ntfy_url = "https://ntfy.sh/trading_bot_pea_2026" 

    def get_news_sentiment(self, ticker):
        """Analyse le sentiment basé sur les derniers titres de presse (Sentiment Analysis)."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news:
                return "Neutre ⚪", 0
            
            positive_keywords = ['hausse', 'croissance', 'succès', 'achat', 'profit', 'contrat', 'excédent', 'rebond']
            negative_keywords = ['chute', 'baisse', 'perte', 'déficit', 'alerte', 'litige', 'inflation', 'profit warning']
            
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
        """Analyse complète sur intervalle 1 Jour avec mémoire historique de 2 ans."""
        try:
            # --- PHASE 1 : ACQUISITION (2 ans en Daily) ---
            # Intervalle '1d' est extrêmement stable sur Yahoo Finance
            df = yf.download(ticker, period="2y", interval="1d", progress=False, threads=False)
            
            if df.empty or len(df) < 200:
                logger.error(f"{ticker} : Historique insuffisant (minimum 200 jours requis).")
                return None

            # --- PHASE 2 : INDICATEURS DE TENDANCE (MÉMOIRE LONG TERME) ---
            # Moyennes Mobiles Exponentielles (EMA)
            df['EMA200'] = ta.trend.ema_indicator(df['Close'], window=200)
            df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50)
            
            # Force de la tendance (ADX) - Prédit si la tendance va durer
            adx_indicator = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
            df['ADX'] = adx_indicator.adx()
            
            # Momentum (RSI) et MACD
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            macd_obj = ta.trend.MACD(df['Close'])
            df['MACD_Hist'] = macd_obj.macd_diff()
            
            # Volatilité (ATR) pour le calcul du risque
            df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
            
            # Extraction des dernières valeurs scalaires (cast en float pour éviter les warnings)
            last_close = float(df['Close'].iloc[-1])
            ema200 = float(df['EMA200'].iloc[-1])
            ema50 = float(df['EMA50'].iloc[-1])
            last_rsi = float(df['RSI'].iloc[-1])
            last_adx = float(df['ADX'].iloc[-1])
            last_macd_h = float(df['MACD_Hist'].iloc[-1])
            prev_macd_h = float(df['MACD_Hist'].iloc[-2])
            last_atr = float(df['ATR'].iloc[-1])

            # --- PHASE 3 : CONTEXTE MACRO (VIX) ---
            vix_data = yf.download("^VIX", period="1d", progress=False)
            vix_price = float(vix_data['Close'].iloc[-1]) if not vix_data.empty else 20.0
            sentiment_label, sentiment_score = self.get_news_sentiment(ticker)

            # --- PHASE 4 : LOGIQUE DE SCORE (PROBABILITÉ DE RÉUSSITE) ---
            prob = 0
            
            # 1. Filtre de Tendance Majeure (Prix > EMA 200)
            if last_close > ema200: prob += 30
            
            # 2. Golden Cross (EMA 50 > EMA 200) - Signal haussier puissant
            if ema50 > ema200: prob += 20
            
            # 3. Force du mouvement (ADX > 25 signifie tendance solide)
            if last_adx > 25: prob += 15
            
            # 4. Momentum MACD (Accélération haussière)
            if last_macd_h > prev_macd_h: prob += 15
            
            # 5. RSI sain (Entre 45 et 65, évite le sur-achat)
            if 45 <= last_rsi <= 65: prob += 10
            
            # 6. Risque Marché (VIX bas)
            if vix_price < 22: prob += 10

            # --- PHASE 5 : CALCUL DU STOP LOSS ET TAKE PROFIT (ATR DYNAMIQUE) ---
            # Stop Loss à 2x l'ATR (adapté à la respiration quotidienne de l'action)
            sl_value = last_atr * 2
            sl_percent = (sl_value / last_close) * 100
            
            # Take Profit avec ratio 1:2.5 (Risk/Reward institutionnel)
            tp_price = last_close + (last_atr * 5)
            potential_gain = ((tp_price / last_close) - 1) * 100

            # --- PHASE 6 : DÉCISION FINALE ---
            action = "VEILLE"
            if prob >= 75:
                action = "ACHAT"
            elif last_rsi > 75:
                action = "VENTE"

            # Récupération des informations entreprise
            info = yf.Ticker(ticker).info
            sector = info.get('sector', 'Divers')

            return {
                'ticker': ticker,
                'nom': info.get('shortName', ticker),
                'secteur': sector,
                'prix': last_close,
                'rsi': last_rsi,
                'adx': last_adx,
                'vix': vix_price,
                'ema200': ema200,
                'ema50': ema50,
                'macd_evol': "Hausse" if last_macd_h > prev_macd_h else "Baisse",
                'sl_pct': sl_percent,
                'tp': tp_price,
                'gains_potentiels': potential_gain,
                'probabilite': prob,
                'sentiment': sentiment_label,
                'action': action,
                'last_update': datetime.now().strftime("%Y-%m-%d %H:%M")
            }

        except Exception as e:
            logger.error(f"Erreur fatale sur {ticker}: {str(e)}")
            return None

    def plot_sectors(self, results):
        """Génère une visualisation des opportunités par secteur (Daily)."""
        buys = [r['secteur'] for r in results if r['action'] == "ACHAT"]
        if not buys:
            return None
        
        plt.figure(figsize=(10, 6), facecolor='#0E1117')
        data = pd.Series(buys).value_counts()
        
        colors = ['#22C55E', '#16A34A', '#15803D', '#166534', '#14532D']
        plt.pie(data, labels=data.index, autopct='%1.1f%%', startangle=140,
                textprops={'color': "white", 'weight': 'bold'}, colors=colors)
        
        plt.title("Répartition des Tendances Haussières par Secteur", color="white", fontsize=14)
        path = "secteurs_conseilles.png"
        plt.savefig(path, dpi=100)
        plt.close()
        return path

    def send_notification(self, data):
        """Envoie une alerte Swing Trading vers NTFY."""
        if data['action'] == "VEILLE":
            return
        
        emoji = "🟢" if data['action'] == "ACHAT" else "🔴"
        title = f"{emoji} {data['action']} {data['ticker']} - Force: {data['probabilite']}%"
        
        message = (
            f"🎯 SIGNAL DAILY : {data['action']}\n"
            f"💰 Prix : {data['prix']:.2f}€\n"
            f"📈 Score de Confiance : {data['probabilite']}%\n"
            f"--------------------------------\n"
            f"💪 Force Tendance (ADX) : {data['adx']:.1f}\n"
            f"📊 RSI : {data['rsi']:.1f} | VIX : {data['vix']:.1f}\n"
            f"📈 EMA 50/200 : {'Golden Cross ✅' if data['ema50'] > data['ema200'] else 'Sous EMA200 ⚠️'}\n"
            f"📰 Sentiment : {data['sentiment']}\n"
            f"--------------------------------\n"
            f"🛡️ Stop Loss : -{data['sl_pct']:.2f}%\n"
            f"🚀 Objectif : {data['tp']:.2f}€ (+{data['gains_potentiels']:.2f}%)\n"
            f"⏰ Analyse du : {data['last_update']}"
        )

        try:
            requests.post(
                self.ntfy_url,
                data=message.encode('utf-8'),
                headers={
                    "Title": title,
                    "Priority": "urgent" if data['probabilite'] > 85 else "default",
                    "Tags": "chart_with_upwards_trend,moneybag"
                }
            )
        except Exception as e:
            logger.error(f"Erreur notification : {e}")
