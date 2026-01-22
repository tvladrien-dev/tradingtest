import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime

class MarketRegimeFilter:
    """
    Moteur de filtrage macro-économique.
    Détermine l'état de santé du marché (Bull, Bear, Stress) pour ajuster le levier.
    """
    def __init__(self, index_ticker="^FCHI"):
        self.index_ticker = index_ticker
        self.threshold_vol = 22.0  # Seuil de stress VIX/Volatilité
        self.ema_long_period = 200
        self.ema_short_period = 50

    def get_market_status(self):
        """
        Analyse le régime actuel du marché via l'indice de référence (CAC 40).
        Retourne un dictionnaire complet de metrics macro.
        """
        try:
            # Récupération des données de l'indice sur 1 an
            df = yf.download(self.index_ticker, period="1y", interval="1d", progress=False)
            
            if df.empty:
                return self._get_default_status()

            # 1. Calcul des indicateurs de tendance
            df['EMA200'] = df['Close'].ewm(span=self.ema_long_period, adjust=False).mean()
            df['EMA50'] = df['Close'].ewm(span=self.ema_short_period, adjust=False).mean()
            
            last_close = float(df['Close'].iloc[-1])
            last_ema200 = float(df['EMA200'].iloc[-1])
            last_ema50 = float(df['EMA50'].iloc[-1])

            # 2. Calcul de la volatilité réalisée (Annualisée)
            # On mesure l'écart-type des rendements logarithmiques sur 20 jours
            log_returns = np.log(df['Close'] / df['Close'].shift(1))
            volatility = log_returns.rolling(window=20).std() * np.sqrt(252) * 100
            current_vol = float(volatility.iloc[-1])

            # 3. Détermination du Statut et du Multiplicateur de Risque
            dist_ema200 = ((last_close / last_ema200) - 1) * 100
            
            status = "NEUTRE"
            multiplier = 0.5 # Exposition par défaut 50%

            # Logique de décision matricielle
            if last_close > last_ema200:
                if current_vol < self.threshold_vol:
                    status = "BULLISH (Sain)"
                    multiplier = 1.0 # Pleine exposition
                else:
                    status = "BULLISH (Volatile)"
                    multiplier = 0.7 # Prudence malgré la hausse
            else:
                if current_vol > self.threshold_vol:
                    status = "BEARISH (Panique)"
                    multiplier = 0.0 # Sortie totale du marché
                else:
                    status = "BEARISH (Correction)"
                    multiplier = 0.3 # Exposition minimale

            return {
                "status": status,
                "multiplier": multiplier,
                "volatility": round(current_vol, 2),
                "last_price": round(last_close, 2),
                "dist_ema_200": round(dist_ema200, 2),
                "trend_50_200": "UP" if last_ema50 > last_ema200 else "DOWN"
            }

        except Exception as e:
            logging.error(f"Erreur Marché Regime: {e}")
            return self._get_default_status()

    def _get_default_status(self):
        """Fallback en cas d'erreur de téléchargement."""
        return {
            "status": "INDÉTERMINÉ",
            "multiplier": 0.5,
            "volatility": 20.0,
            "last_price": 0.0,
            "dist_ema_200": 0.0,
            "trend_50_200": "NEUTRAL"
        }

    def get_dynamic_allocation(self, base_size):
        """
        Ajuste la taille d'une position individuelle selon le régime.
        """
        mkt = self.get_market_status()
        return base_size * mkt["multiplier"]
