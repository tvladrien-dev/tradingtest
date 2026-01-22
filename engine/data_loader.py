import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import ta  # Bibliothèque d'analyse technique

class DataLoader:
    """
    Moteur d'acquisition et de traitement de données haute performance.
    Gère le flux entrant d'Euronext Paris et le calcul des indicateurs.
    """
    def __init__(self):
        self.cache = {}
        self.last_sync = None
        logging.info("DataLoader initialisé - Prêt pour synchronisation Euronext.")

    def download_market_data(self, tickers, period="2y", interval="1d"):
        """
        Télécharge les données historiques et temps réel depuis Yahoo Finance.
        """
        data_store = {}
        logging.info(f"Téléchargement de {len(tickers)} actifs sur une période de {period}...")
        
        try:
            # Téléchargement groupé pour optimiser les appels réseau
            raw_data = yf.download(
                tickers=tickers,
                period=period,
                interval=interval,
                group_by='ticker',
                auto_adjust=True,
                threads=True
            )

            for ticker in tickers:
                if ticker in raw_data:
                    df = raw_data[ticker].copy()
                    # Nettoyage des données (suppression des NaNs critiques)
                    df = df.dropna(subset=['Close'])
                    
                    if not df.empty:
                        # Enrichissement technique (Vecteurs Alpha)
                        df = self._enrich_with_indicators(df)
                        data_store[ticker] = df
            
            self.last_sync = datetime.now()
            return data_store

        except Exception as e:
            logging.error(f"Erreur critique lors du téléchargement : {e}")
            return {}

    def _enrich_with_indicators(self, df):
        """
        Calcule la matrice d'indicateurs propriétaires pour le trading PEA.
        """
        # 1. RSI (Relative Strength Index) pour le momentum
        df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()

        # 2. Matrice de Moyennes Mobiles (Convergence de tendance)
        df['EMA20'] = ta.trend.EMAIndicator(close=df['Close'], window=20).ema_indicator()
        df['EMA50'] = ta.trend.EMAIndicator(close=df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(close=df['Close'], window=200).ema_indicator()

        # 3. ATR (Average True Range) pour la volatilité et le calcul des Stop Loss
        df['ATR'] = ta.volatility.AverageTrueRange(
            high=df['High'], low=df['Low'], close=df['Close'], window=14
        ).average_true_range()

        # 4. Bandes de Bollinger (Détection des extrêmes)
        indicator_bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_High'] = indicator_bb.bollinger_hband()
        df['BB_Low'] = indicator_bb.bollinger_lband()

        # 5. Calcul de la tendance (Distance à la EMA200 en %)
        df['Dist_EMA200'] = ((df['Close'] / df['EMA200']) - 1) * 100

        return df

    def get_latest_price(self, ticker):
        """Récupère le dernier prix connu pour un ticker donné."""
        try:
            ticker_obj = yf.Ticker(ticker)
            return ticker_obj.fast_info['lastPrice']
        except:
            return None

    def check_market_hours(self):
        """
        Vérifie si la bourse de Paris est ouverte (Euronext: 09:00 - 17:30).
        """
        now = datetime.now()
        # 0 = Lundi, 6 = Dimanche
        if now.weekday() >= 5:
            return False
        
        current_time = now.time()
        start_time = datetime.strptime("09:00", "%H:%M").time()
        end_time = datetime.strptime("17:35", "%H:%M").time() # +5min pour le fixing
        
        return start_time <= current_time <= end_time
