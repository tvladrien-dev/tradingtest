import yfinance as yf
import pandas as pd
import ta
import requests
import matplotlib.pyplot as plt
import logging
import time
from datetime import datetime

# Configuration avancée du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    Moteur de Trading Institutionnel - Version Swing Daily Intégrale.
    Utilise l'ADX, les EMA 50/200 et l'analyse de sentiment pour prédire les cycles.
    """
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        self.ntfy_url = "https://ntfy.sh/votre_topic_unique_2026"

    def get_news_sentiment(self, ticker):
        """
        Analyse de sentiment textuelle basée sur les flux Yahoo Finance.
        Aide à valider si la tendance haussière est soutenue par les fondamentaux.
        """
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news:
                return "Neutre ⚪", 0
            
            # Dictionnaire de mots-clés pour le scoring
            pos_words = ['hausse', 'croissance', 'achat', 'profit', 'contrat', 'succès', 'dividende', 'rebond']
            neg_words = ['chute', 'baisse', 'perte', 'alerte', 'déficit', 'litige', 'inflation', 'règlement']
            
            score = 0
            titles = [n['title'].lower() for n in news[:5]]
            for title in titles:
                score += sum(1 for w in pos_words if w in title)
                score -= sum(1 for w in neg_words if w in title)
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except Exception as e:
            logger.warning(f"Sentiment non disponible pour {ticker}: {e}")
            return "Indisponible ❓", 0

    def process_ticker(self, ticker):
        """
        Analyse technique profonde sur 2 ans d'historique.
        L'intervalle journalier (1d) garantit la stabilité des données.
        """
        try:
            # --- 1. ACQUISITION DES DONNÉES ---
            # Utilisation stricte de l'intervalle '1d' pour éviter les erreurs 404/60j
            df = yf.download(ticker, period="2y", interval="1d", progress=False, threads=False)

            if df.empty or len(df) < 200:
                logger.error(f"Données insuffisantes pour {ticker} (Min 200 jours requis)")
                return None

            # --- 2. INDICATEURS DE TENDANCE & PRÉDICTION ---
            # EMA 200 : Tendance de fond (Support/Résistance psychologique)
            df['EMA200'] = ta.trend.ema_indicator(df['Close'], window=200)
            # EMA 50 : Tendance intermédiaire
            df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50)
            
            # ADX (Average Directional Index) : Prédit la puissance de la tendance
            # Un ADX > 25 indique que la tendance est solide et susceptible de durer
            adx_indicator = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
            df['ADX'] = adx_indicator.adx()
            
            # RSI : Détecte les zones de sur-achat ou de sur-vente
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # MACD : Mesure l'accélération du prix
            macd_obj = ta.trend.MACD(df['Close'])
            df['MACD_Hist'] = macd_obj.macd_diff()

            # --- 3. EXTRACTION DES DONNÉES ACTUELLES ---
            last_close = float(df['Close'].iloc[-1])
            ema200 = float(df['EMA200'].iloc[-1])
            ema50 = float(df['EMA50'].iloc[-1])
            last_adx = float(df['ADX'].iloc[-1])
            last_rsi = float(df['RSI'].iloc[-1])
            last_macd_h = float(df['MACD_Hist'].iloc[-1])
            prev_macd_h = float(df['MACD_Hist'].iloc[-2])

            # Analyse du VIX (Indice de la peur) pour le risque global
            vix_df = yf.download("^VIX", period="1d", progress=False)
            vix_val = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 20.0
            sentiment_label, sentiment_score = self.get_news_sentiment(ticker)

            # --- 4. LOGIQUE DE PRÉDICTION (SCORE DE CONFIANCE) ---
            prob = 0
            
            # Règle 1 : Prix au-dessus de la tendance long terme (EMA 200)
            if last_close > ema200: prob += 30
            
            # Règle 2 : Croisement haussier (EMA 50 > EMA 200) - Golden Cross
            if ema50 > ema200: prob += 20
            
            # Règle 3 : Force du mouvement (ADX > 25)
            if last_adx > 25: prob += 20
            
            # Règle 4 : Accélération du momentum (MACD)
            if last_macd_h > prev_macd_h: prob += 15
            
            # Règle 5 : RSI équilibré (pas encore en sur-achat)
            if 40 <= last_rsi <= 65: prob += 10
            
            # Règle 6 : Marché serein (VIX)
            if vix_val < 22: prob += 5

            # --- 5. GESTION DU RISQUE (STOP LOSS DYNAMIQUE) ---
            # Utilisation de l'ATR (Average True Range) pour s'adapter à la volatilité
            df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
            last_atr = float(df['ATR'].iloc[-1])
            
            # Stop Loss à 2x l'ATR sous le prix actuel
            sl_dist = last_atr * 2
            sl_pct = (sl_dist / last_close) * 100
            
            # Objectif de gain (Take Profit) à 4x l'ATR (Ratio 1:2)
            tp_price = last_close + (last_atr * 4)
            potential_gain = ((tp_price / last_close) - 1) * 100

            # --- 6. DÉCISION FINALE ---
            action = "VEILLE"
            if prob >= 75:
                action = "ACHAT"
            elif last_rsi > 80:
                action = "VENTE"

            info = yf.Ticker(ticker).info
            
            return {
                'ticker': ticker,
                'nom': info.get('shortName', ticker),
                'secteur': info.get('sector', 'Inconnu'),
                'prix': last_close,
                'rsi': last_rsi,
                'adx': last_adx,
                'ema50': ema50,
                'ema200': ema200,
                'probabilite': prob,
                'action': action,
                'sentiment': sentiment_label,
                'sl_pct': sl_pct,
                'tp': tp_price,
                'gain_pct': potential_gain,
                'last_update': datetime.now().strftime("%Y-%m-%d %H:%M")
            }

        except Exception as e:
            logger.error(f"Erreur d'analyse sur {ticker}: {e}")
            return None

    def plot_sectors(self, results):
        """Visualise la répartition sectorielle des signaux d'achat."""
        buys = [r['secteur'] for r in results if r['action'] == "ACHAT"]
        if not buys: return None
        
        plt.figure(figsize=(10, 6), facecolor='#0E1117')
        counts = pd.Series(buys).value_counts()
        plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140, textprops={'color':"w"})
        plt.title("Secteurs Dominants en Tendance Haussière", color="w")
        
        path = "secteurs_opportunites.png"
        plt.savefig(path)
        plt.close()
        return path

    def send_notification(self, d):
        """Envoie l'alerte de trading via NTFY."""
        if d['action'] == "VEILLE": return
        
        title = f"SIGNAL {d['action']} : {d['ticker']} ({d['probabilite']}%)"
        msg = (
            f"📈 Action : {d['action']}\n"
            f"📊 Confiance : {d['probabilite']}%\n"
            f"💵 Prix : {d['prix']:.2f}€\n"
            f"💪 Force ADX : {d['adx']:.1f}\n"
            f"🛡️ Stop Loss : -{d['sl_pct']:.2f}%\n"
            f"🚀 Objectif : +{d['gain_pct']:.2f}%\n"
            f"📰 Sentiment : {d['sentiment']}"
        )
        requests.post(self.ntfy_url, data=msg.encode('utf-8'), headers={"Title": title})
