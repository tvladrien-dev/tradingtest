import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
import time
from datetime import datetime

# Configuration du logging professionnel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    Moteur de Trading Institutionnel Intégré.
    Fusion de DataLoader (Acquisition/Indicateurs) et TradingBot (Analyse/Signaux).
    Version : 12.5.1 (2026) - Full Performance
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        self.ntfy_url = "https://ntfy.sh/votre_topic_unique_2026"  # À configurer
        self.last_sync = None
        self.data_store = {}
        self.last_results = []
        logger.info("Bot Elite Initialisé avec moteur DataLoader intégré.")

    # --- SECTION : MOTEUR DE DONNÉES ---

    def sync_market_data(self, period="2y", interval="1d"):
        """
        Téléchargement groupé haute performance et enrichissement technique.
        """
        if not self.tickers:
            logger.warning("Aucun ticker à synchroniser.")
            return {}

        logger.info(f"Synchronisation de {len(self.tickers)} actifs...")
        
        try:
            # Téléchargement groupé (Threads=True pour maximiser la vitesse sur Streamlit Cloud)
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
                    # Gestion de la structure de retour yfinance (Single vs Multi-index)
                    if len(self.tickers) == 1:
                        df = raw_data.copy()
                    else:
                        if ticker not in raw_data.columns.levels[0]: 
                            continue
                        df = raw_data[ticker].copy()
                    
                    # Nettoyage des données vides
                    df = df.dropna(subset=['Close'])
                    
                    # Minimum 200 points requis pour l'EMA200
                    if len(df) >= 200:
                        # Calcul de la matrice d'indicateurs
                        df = self._enrich_indicators(df)
                        self.data_store[ticker] = df
                    else:
                        logger.warning(f"Historique insuffisant pour {ticker} ({len(df)} points)")

                except Exception as e:
                    logger.error(f"Erreur sur le ticker {ticker}: {e}")
            
            self.last_sync = datetime.now()
            return self.data_store

        except Exception as e:
            logger.error(f"Échec critique de synchronisation : {e}")
            return {}

    def _enrich_indicators(self, df):
        """Calcule la matrice d'indicateurs propriétaires."""
        # Tendance
        df['EMA20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
        df['EMA50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Momentum & Volatilité
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        
        # Force de tendance (ADX)
        adx_ind = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
        df['ADX'] = adx_ind.adx()
        
        # MACD
        macd_obj = ta.trend.MACD(df['Close'])
        df['MACD_Hist'] = macd_obj.macd_diff()

        # Bollinger
        bb = ta.volatility.BollingerBands(df['Close'], window=20)
        df['BB_High'] = bb.bollinger_hband()
        df['BB_Low'] = bb.bollinger_lband()
        
        # Distance relative à l'EMA200
        df['Dist_EMA200'] = ((df['Close'] / df['EMA200']) - 1) * 100
        
        return df

    # --- SECTION : ANALYSE & DÉCISION ---

    def get_news_sentiment(self, ticker):
        """Scoring de sentiment textuel via Yahoo News."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news: return "Neutre ⚪", 0
            
            pos_words = ['hausse', 'croissance', 'achat', 'profit', 'contrat', 'succès', 'dividende', 'rebond', 'positive', 'upgrade']
            neg_words = ['chute', 'baisse', 'perte', 'alerte', 'déficit', 'litige', 'inflation', 'règlement', 'downgrade', 'negative']
            
            score = 0
            titles = [n['title'].lower() for n in news[:5]]
            for title in titles:
                score += sum(1 for w in pos_words if w in title)
                score -= sum(1 for w in neg_words if w in title)
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except Exception:
            return "Indisponible ❓", 0

    def process_signals(self):
        """Analyse les données synchronisées pour générer des signaux probabilistes."""
        results = []
        
        # Téléchargement du VIX (Indice de peur)
        try:
            vix_df = yf.download("^VIX", period="1d", progress=False)
            # Correction FutureWarning en utilisant iloc[0] si Series
            vix_val = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 20.0
        except:
            vix_val = 20.0

        for ticker, df in self.data_store.items():
            try:
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                prob = 0
                # --- LOGIQUE DE SCORING ALPHA ---
                # 1. Tendance Long Terme (30 pts)
                if last['Close'] > last['EMA200']: prob += 30
                
                # 2. Golden Cross ou Alignement (20 pts)
                if last['EMA50'] > last['EMA200']: prob += 20
                
                # 3. Force de la Tendance ADX (20 pts)
                if last['ADX'] > 25: prob += 20
                
                # 4. Momentum MACD (15 pts)
                if last['MACD_Hist'] > prev['MACD_Hist']: prob += 15
                
                # 5. Zone RSI Optimale (10 pts)
                if 35 <= last['RSI'] <= 65: prob += 10
                
                # 6. Bonus Volatilité Basse (5 pts)
                if vix_val < 22: prob += 5

                # --- GESTION DU RISQUE ATR ---
                sl_dist = last['ATR'] * 2
                sl_pct = (sl_dist / last['Close']) * 100
                tp_price = last['Close'] + (last['ATR'] * 4)
                gain_pct = ((tp_price / last['Close']) - 1) * 100

                # Détermination de l'Action
                action = "VEILLE"
                if prob >= 75: 
                    action = "ACHAT"
                elif last['RSI'] > 80: 
                    action = "VENTE"

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
                    'last_update': datetime.now().strftime("%H:%M")
                })

            except Exception as e:
                logger.error(f"Erreur d'analyse sur {ticker}: {e}")
        
        self.last_results = results
        return results

    def get_last_signals(self):
        """Retourne les derniers signaux générés (Méthode utilisée par le Dashboard)."""
        if not self.last_results:
            return self.process_signals()
        return self.last_results

    def get_data_for_ticker(self, ticker):
        """Récupère l'historique complet pour un actif spécifique."""
        return self.data_store.get(ticker)

    def send_notification(self, d):
        """Alerte via NTFY sur mobile."""
        if d['action'] == "VEILLE": 
            return False
        
        title = f"💎 SIGNAL {d['action']} : {d['ticker']} ({d['probabilite']}%)"
        msg = (
            f"📈 Action : {d['action']}\n"
            f"📊 Confiance : {d['probabilite']}%\n"
            f"💵 Prix : {d['prix']:.2f}€\n"
            f"🛡️ Stop Loss : -{d['sl_pct']:.2f}%\n"
            f"🚀 Objectif : +{d['gain_pct']:.2f}%\n"
            f"📰 Sentiment : {d['sentiment']}"
        )
        
        try:
            res = requests.post(
                self.ntfy_url, 
                data=msg.encode('utf-8'), 
                headers={
                    "Title": title,
                    "Priority": "high",
                    "Tags": "chart_with_upwards_trend,moneybag"
                },
                timeout=5
            )
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Erreur notification NTFY: {e}")
            return False
