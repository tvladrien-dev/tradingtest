import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import ta  # Bibliothèque d'analyse technique

class DataLoader:
    """
    Moteur d'acquisition et de traitement de données haute performance.
    Gère le flux entrant multi-marchés (PEA, Crypto, Commodities) et le calcul des indicateurs.
    """
    def __init__(self):
        self.cache = {}
        self.last_sync = None
        logging.info("DataLoader initialisé - Prêt pour synchronisation multi-flux.")

    def download_market_data(self, tickers, period="2y", interval="1d"):
        """
        Télécharge les données historiques et temps réel depuis Yahoo Finance.
        Supporte le téléchargement groupé et le nettoyage de données.
        """
        data_store = {}
        if not tickers:
            logging.warning("Aucun ticker fourni au DataLoader.")
            return {}

        logging.info(f"Téléchargement de {len(tickers)} actifs sur une période de {period} (intervalle: {interval})...")
        
        try:
            # Téléchargement groupé pour optimiser les appels réseau
            # auto_adjust=True permet d'avoir les prix ajustés (dividendes/splits) directement
            raw_data = yf.download(
                tickers=tickers,
                period=period,
                interval=interval,
                group_by='ticker',
                auto_adjust=True,
                threads=True,
                proxy=None
            )

            for ticker in tickers:
                try:
                    # Gestion du cas particulier yfinance : si un seul ticker, le DataFrame n'a pas de MultiIndex
                    if len(tickers) == 1:
                        df = raw_data.copy()
                    else:
                        if ticker not in raw_data.columns.levels[0]:
                            continue
                        df = raw_data[ticker].copy()
                    
                    # Nettoyage des données (suppression des NaNs sur la colonne Close)
                    df = df.dropna(subset=['Close'])
                    
                    # Vérification du seuil minimal pour les indicateurs (ex: EMA200 nécessite 200 points)
                    if len(df) < 20:
                        logging.warning(f"Données insuffisantes pour {ticker} ({len(df)} points). Ignoré.")
                        continue

                    # Enrichissement technique (Vecteurs Alpha)
                    df = self._enrich_with_indicators(df)
                    data_store[ticker] = df

                except Exception as inner_e:
                    logging.error(f"Erreur lors du traitement du ticker {ticker} : {inner_e}")
                    continue
            
            self.last_sync = datetime.now()
            return data_store

        except Exception as e:
            logging.error(f"Erreur critique lors du téléchargement global : {e}")
            return {}

    def _enrich_with_indicators(self, df):
        """
        Calcule la matrice d'indicateurs propriétaires (Technique + Volatilité).
        """
        # Utilisation d'un bloc try-except pour éviter qu'un calcul d'indicateur ne bloque tout
        try:
            # 1. RSI (Relative Strength Index) pour le momentum
            df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()

            # 2. Matrice de Moyennes Mobiles (Convergence de tendance)
            df['EMA20'] = ta.trend.EMAIndicator(close=df['Close'], window=20).ema_indicator()
            df['EMA50'] = ta.trend.EMAIndicator(close=df['Close'], window=50).ema_indicator()
            df['EMA200'] = ta.trend.EMAIndicator(close=df['Close'], window=200).ema_indicator()

            # 3. ATR (Average True Range) pour la volatilité et le calcul des Stop Loss
            # L'ATR est crucial pour le position sizing dynamique
            df['ATR'] = ta.volatility.AverageTrueRange(
                high=df['High'], low=df['Low'], close=df['Close'], window=14
            ).average_true_range()

            # 4. Bandes de Bollinger (Détection des extrêmes et squeeze)
            indicator_bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
            df['BB_High'] = indicator_bb.bollinger_hband()
            df['BB_Low'] = indicator_bb.bollinger_lband()
            df['BB_Mid'] = indicator_bb.bollinger_mavg()

            # 5. Indicateur de Tendance Additionnel (ADX)
            adx_ind = ta.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14)
            df['ADX'] = adx_ind.adx()
            df['ADX_Pos'] = adx_ind.adx_pos()
            df['ADX_Neg'] = adx_ind.adx_neg()

            # 6. Calcul de la tendance (Distance à la EMA200 en %)
            # Une valeur positive indique un marché haussier à long terme
            df['Dist_EMA200'] = ((df['Close'] / df['EMA200']) - 1) * 100

            # 7. Volume SMA pour détecter les cassures avec volume
            df['Volume_SMA20'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Rel'] = df['Volume'] / df['Volume_SMA20']

            # Nettoyage final pour enlever les lignes de calcul (NaNs créés par les périodes de fenêtres)
            # On garde l'historique mais on s'assure que les dernières lignes sont propres
            return df
            
        except Exception as e:
            logging.error(f"Erreur lors du calcul des indicateurs : {e}")
            return df

    def get_latest_price(self, ticker):
        """Récupère le dernier prix connu pour un ticker donné avec fallback."""
        try:
            ticker_obj = yf.Ticker(ticker)
            # Utilisation de fast_info pour la performance, fallback sur history
            price = ticker_obj.fast_info.get('lastPrice')
            if price is None:
                hist = ticker_obj.history(period="1d")
                price = hist['Close'].iloc[-1]
            return price
        except Exception as e:
            logging.warning(f"Impossible de récupérer le prix pour {ticker}: {e}")
            return None

    def check_market_hours(self):
        """
        Vérifie si la bourse est ouverte. 
        Note : Cette version est générique. Pour les cryptos, cela devrait toujours être True.
        """
        now = datetime.now()
        
        # 0 = Lundi, 6 = Dimanche
        if now.weekday() >= 5:
            return False
        
        current_time = now.time()
        start_time = datetime.strptime("09:00", "%H:%M").time()
        end_time = datetime.strptime("17:35", "%H:%M").time() # +5min pour le fixing de clôture
        
        return start_time <= current_time <= end_time
