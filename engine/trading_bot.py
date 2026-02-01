import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
import time
from datetime import datetime

# Configuration du logging haute précision
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    Moteur de Trading Institutionnel Intégré.
    Fusion de DataLoader (Acquisition/Indicateurs) et TradingBot (Analyse/Signaux).
    Version : 12.5.2 (Février 2026) - Full Performance
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        self.ntfy_url = "https://ntfy.sh/votre_topic_unique_2026" # Configurable via secrets
        self.last_sync = None
        self.data_store = {}
        self.last_results = []
        logger.info("Bot Elite Initialisé avec moteur DataLoader intégré.")

    # --- SECTION : MOTEUR DE DONNÉES (DATA ACQUISITION) ---

    def sync_market_data(self, period="2y", interval="1d"):
        """
        Téléchargement groupé haute performance et enrichissement technique.
        """
        if not self.tickers:
            logger.warning("Aucun ticker à synchroniser.")
            return {}

        logger.info(f"Synchronisation de {len(self.tickers)} actifs...")
        
        try:
            # Téléchargement asynchrone via threads pour Streamlit Cloud
            raw_data = yf.download(
                tickers=self.tickers,
                period=period,
                interval=interval,
                group_by='ticker',
                auto_adjust=True,
                threads=True,
                progress=False
            )

            for ticker in self.tickers:
                try:
                    # Extraction sécurisée selon le format de retour yfinance
                    if len(self.tickers) == 1:
                        df = raw_data.copy()
                    else:
                        if ticker not in raw_data.columns.levels[0]: 
                            continue
                        df = raw_data[ticker].copy()
                    
                    df = df.dropna(subset=['Close'])
                    
                    # Seuil critique de 200 points pour la validité de l'EMA200
                    if len(df) >= 200:
                        df = self._enrich_indicators(df)
                        self.data_store[ticker] = df
                    else:
                        logger.warning(f"Historique insuffisant pour {ticker} ({len(df)} j)")

                except Exception as e:
                    logger.error(f"Erreur extraction sur {ticker}: {e}")
            
            self.last_sync = datetime.now()
            return self.data_store

        except Exception as e:
            logger.error(f"Échec critique du flux de données : {e}")
            return {}

    def _enrich_indicators(self, df):
        """Calcule la matrice d'indicateurs techniques (Alpha Matrix)."""
        # Moyennes Mobiles (Trend)
        df['EMA20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
        df['EMA50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Oscillateurs (Momentum)
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # Volatilité (Risk management)
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        
        # Force de Tendance (ADX)
        adx_ind = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
        df['ADX'] = adx_ind.adx()
        
        # Convergence/Divergence (MACD)
        macd_obj = ta.trend.MACD(df['Close'])
        df['MACD_Hist'] = macd_obj.macd_diff()

        # Bollinger Bands (Extrêmes)
        bb = ta.volatility.BollingerBands(df['Close'], window=20)
        df['BB_High'] = bb.bollinger_hband()
        df['BB_Low'] = bb.bollinger_lband()
        
        # Calcul de l'écart type relatif à l'EMA200
        df['Dist_EMA200'] = ((df['Close'] / df['EMA200']) - 1) * 100
        
        return df

    # --- SECTION : ANALYSE & SENTIMENT (BRAIN) ---

    def get_news_sentiment(self, ticker):
        """Scoring sémantique des news pour renforcer la probabilité du signal."""
        try:
            stock = yf.Ticker(ticker)
            news = getattr(stock, 'news', [])
            if not news: 
                return "Neutre ⚪", 0
            
            pos_words = {'hausse', 'croissance', 'achat', 'profit', 'contrat', 'succès', 'dividende', 'rebond', 'positive', 'upgrade'}
            neg_words = {'chute', 'baisse', 'perte', 'alerte', 'déficit', 'litige', 'inflation', 'negative', 'downgrade'}
            
            score = 0
            for n in news[:5]:
                title = n.get('title', '').lower()
                score += sum(1 for w in pos_words if w in title)
                score -= sum(1 for w in neg_words if w in title)
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except Exception:
            return "Indisponible ❓", 0

    def process_signals(self):
        """Exécute l'algorithme de scoring probabiliste sur tout le data_store."""
        results = []
        
        # Récupération du VIX pour le régime de marché global
        try:
            vix_df = yf.download("^VIX", period="1d", progress=False)
            vix_val = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 20.0
        except:
            vix_val = 20.0

        for ticker, df in self.data_store.items():
            try:
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Système de points (Total 100)
                prob = 0
                if last['Close'] > last['EMA200']: prob += 30      # Trend LT
                if last['EMA50'] > last['EMA200']: prob += 20      # Structure
                if last['ADX'] > 25: prob += 20                   # Force
                if last['MACD_Hist'] > prev['MACD_Hist']: prob += 15 # Accélération
                if 40 <= last['RSI'] <= 65: prob += 10            # Zone de confort
                if vix_val < 22: prob += 5                        # Marché stable

                # Paramètres de sortie (Risk/Reward)
                sl_dist = last['ATR'] * 2
                sl_pct = (sl_dist / last['Close']) * 100
                tp_price = last['Close'] + (last['ATR'] * 4)
                gain_pct = ((tp_price / last['Close']) - 1) * 100

                # Classification de l'action
                action = "VEILLE"
                if prob >= 75: action = "ACHAT"
                elif last['RSI'] > 80: action = "VENTE"

                sentiment_label, _ = self.get_news_sentiment(ticker)
                
                results.append({
                    'ticker': ticker,
                    'prix': float(last['Close']),
                    'rsi': round(float(last['RSI']), 2),
                    'probabilite': prob,
                    'action': action,
                    'sentiment': sentiment_label,
                    'sl_pct': round(float(sl_pct), 2),
                    'tp': round(float(tp_price), 2),
                    'gain_pct': round(float(gain_pct), 2),
                    'last_update': datetime.now().strftime("%Y-%m-%d %H:%M")
                })

            except Exception as e:
                logger.error(f"Erreur d'analyse sur {ticker}: {e}")
        
        self.last_results = results
        return results

    def get_last_signals(self):
        """Méthode pivot pour l'interface Dashboard."""
        if not self.last_results:
            return self.process_signals()
        return self.last_results

    def get_data_for_ticker(self, ticker):
        """Retourne le DataFrame complet pour les graphiques détaillés."""
        return self.data_store.get(ticker)

    def send_notification(self, d):
        """Expédie l'alerte Alpha vers NTFY (Mobile)."""
        if d['action'] == "VEILLE": return False
        
        title = f"🚨 {d['action']} : {d['ticker']} ({d['probabilite']}%)"
        msg = (
            f"💰 Prix : {d['prix']:.2f}€\n"
            f"📊 Confiance : {d['probabilite']}%\n"
            f"🛡️ Stop : -{d['sl_pct']:.2f}%\n"
            f"🎯 Target : +{d['gain_pct']:.2f}%\n"
            f"📰 News : {d['sentiment']}"
        )
        
        try:
            requests.post(
                self.ntfy_url, 
                data=msg.encode('utf-8'), 
                headers={"Title": title, "Priority": "high", "Tags": "rocket,chart_with_upwards_trend"}
            )
            return True
        except:
            return False
