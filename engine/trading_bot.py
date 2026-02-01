import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
import time
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    Moteur de Trading Institutionnel Intégré.
    Fusion de DataLoader (Acquisition/Indicateurs) et TradingBot (Analyse/Signaux).
    Version : 12.5.1 (2026) - Full Performance
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        self.ntfy_url = "https://ntfy.sh/votre_topic_unique_2026" # À mettre en variable d'env
        self.last_sync = None
        self.data_store = {}
        logger.info("Bot Elite Initialisé avec moteur DataLoader intégré.")

    # --- SECTION : MOTEUR DE DONNÉES (ANCIENNEMENT DATA_LOADER) ---

    def sync_market_data(self, period="2y", interval="1d"):
        """
        Téléchargement groupé haute performance et enrichissement technique.
        Remplace l'ancien DataLoader.download_market_data.
        """
        if not self.tickers:
            logger.warning("Aucun ticker à synchroniser.")
            return {}

        logger.info(f"Synchronisation de {len(self.tickers)} actifs...")
        
        try:
            # Téléchargement groupé (Threads=True pour la vitesse)
            raw_data = yf.download(
                tickers=self.tickers,
                period=period,
                interval=interval,
                group_by='ticker',
                auto_adjust=True,
                threads=True
            )

            for ticker in self.tickers:
                try:
                    # Gestion de la structure de retour yfinance
                    if len(self.tickers) == 1:
                        df = raw_data.copy()
                    else:
                        if ticker not in raw_data.columns.levels[0]: continue
                        df = raw_data[ticker].copy()
                    
                    df = df.dropna(subset=['Close'])
                    
                    if len(df) >= 200: # Minimum pour EMA200
                        # Calcul de TOUS les indicateurs (Vecteurs Alpha)
                        df = self._enrich_indicators(df)
                        self.data_store[ticker] = df
                    else:
                        logger.warning(f"Historique insuffisant pour {ticker}")

                except Exception as e:
                    logger.error(f"Erreur sur le ticker {ticker}: {e}")
            
            self.last_sync = datetime.now()
            return self.data_store

        except Exception as e:
            logger.error(f"Échec critique de synchronisation : {e}")
            return {}

    def _enrich_indicators(self, df):
        """Calcule la matrice d'indicateurs propriétaires pour l'analyse technique."""
        # Tendance
        df['EMA20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
        df['EMA50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Momentum & Volatilité
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        
        # ADX (Force de tendance)
        adx_ind = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
        df['ADX'] = adx_ind.adx()
        
        # MACD (Accélération)
        macd_obj = ta.trend.MACD(df['Close'])
        df['MACD_Hist'] = macd_obj.macd_diff()

        # Bollinger (Extrêmes)
        bb = ta.volatility.BollingerBands(df['Close'], window=20)
        df['BB_High'] = bb.bollinger_hband()
        df['BB_Low'] = bb.bollinger_lband()
        
        # Distance EMA200
        df['Dist_EMA200'] = ((df['Close'] / df['EMA200']) - 1) * 100
        
        return df

    # --- SECTION : ANALYSE & DÉCISION (TRADING_BOT) ---

    def get_news_sentiment(self, ticker):
        """Scoring de sentiment basé sur Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news: return "Neutre ⚪", 0
            
            pos_words = ['hausse', 'croissance', 'achat', 'profit', 'contrat', 'succès', 'dividende', 'rebond']
            neg_words = ['chute', 'baisse', 'perte', 'alerte', 'déficit', 'litige', 'inflation', 'règlement']
            
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
        """Analyse les données synchronisées pour générer des signaux."""
        results = []
        
        # On télécharge le VIX une fois pour tout le groupe (économie de ressources)
        vix_df = yf.download("^VIX", period="1d", progress=False)
        vix_val = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 20.0

        for ticker, df in self.data_store.items():
            try:
                # Récupération des dernières valeurs calculées par le moteur interne
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                prob = 0
                # Règle 1 : Tendance de fond
                if last['Close'] > last['EMA200']: prob += 30
                # Règle 2 : Golden Cross
                if last['EMA50'] > last['EMA200']: prob += 20
                # Règle 3 : Puissance ADX
                if last['ADX'] > 25: prob += 20
                # Règle 4 : Momentum MACD
                if last['MACD_Hist'] > prev['MACD_Hist']: prob += 15
                # Règle 5 : RSI équilibré
                if 40 <= last['RSI'] <= 65: prob += 10
                # Règle 6 : Risque Marché
                if vix_val < 22: prob += 5

                # Gestion du risque ATR
                sl_dist = last['ATR'] * 2
                sl_pct = (sl_dist / last['Close']) * 100
                tp_price = last['Close'] + (last['ATR'] * 4)
                gain_pct = ((tp_price / last['Close']) - 1) * 100

                action = "VEILLE"
                if prob >= 75: action = "ACHAT"
                elif last['RSI'] > 80: action = "VENTE"

                sentiment_label, _ = self.get_news_sentiment(ticker)
                
                results.append({
                    'ticker': ticker,
                    'prix': last['Close'],
                    'rsi': last['RSI'],
                    'probabilite': prob,
                    'action': action,
                    'sentiment': sentiment_label,
                    'sl_pct': sl_pct,
                    'tp': tp_price,
                    'gain_pct': gain_pct,
                    'last_update': datetime.now().strftime("%Y-%m-%d %H:%M")
                })

            except Exception as e:
                logger.error(f"Erreur d'analyse sur {ticker}: {e}")
        
        return results

    def send_notification(self, d):
        """Alerte via NTFY."""
        if d['action'] == "VEILLE": return
        
        title = f"SIGNAL {d['action']} : {d['ticker']} ({d['probabilite']}%)"
        msg = (
            f"📈 Action : {d['action']}\n"
            f"📊 Confiance : {d['probabilite']}%\n"
            f"💵 Prix : {d['prix']:.2f}€\n"
            f"🛡️ Stop Loss : -{d['sl_pct']:.2f}%\n"
            f"🚀 Objectif : +{d['gain_pct']:.2f}%\n"
            f"📰 Sentiment : {d['sentiment']}"
        )
        requests.post(self.ntfy_url, data=msg.encode('utf-8'), headers={"Title": title})
