import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime

class MarketRegimeFilter:
    """
    Moteur de filtrage macro-économique.
    Détermine l'état de santé du marché (Bull, Bear, Stress) pour ajuster le levier.
    Analyse basée sur l'historique journalier (Daily) uniquement.
    """
    def __init__(self, index_ticker="^FCHI"):
        self.index_ticker = index_ticker
        self.threshold_vol = 22.0  # Seuil de stress VIX/Volatilité
        self.ema_long_period = 200
        self.ema_short_period = 50
        self.logger = logging.getLogger("MarketRegime")

    def get_market_status(self):
        """
        Analyse le régime actuel du marché via l'indice de référence (CAC 40).
        Retourne un dictionnaire complet de metrics macro.
        """
        try:
            # --- PHASE 1 : ACQUISITION (Intervalle 1d forcé) ---
            # On demande 1 an de données journalières pour calculer les EMA 50/200
            df = yf.download(self.index_ticker, period="1y", interval="1d", progress=False)
            
            if df.empty or len(df) < self.ema_long_period:
                self.logger.warning(f"Données d'indice {self.index_ticker} insuffisantes ou Rate Limit.")
                return self._get_default_status()

            # --- PHASE 2 : CALCUL DES INDICATEURS ---
            # Moyennes Mobiles Exponentielles
            df['EMA200'] = df['Close'].ewm(span=self.ema_long_period, adjust=False).mean()
            df['EMA50'] = df['Close'].ewm(span=self.ema_short_period, adjust=False).mean()
            
            # Extraction propre des dernières valeurs (Conversion en float explicite)
            last_close = float(df['Close'].iloc[-1])
            last_ema200 = float(df['EMA200'].iloc[-1])
            last_ema50 = float(df['EMA50'].iloc[-1])

            # --- PHASE 3 : VOLATILITÉ RÉALISÉE (ANNUALISÉE) ---
            # Calcul des rendements logarithmiques pour mesurer le risque réel
            log_returns = np.log(df['Close'] / df['Close'].shift(1))
            # Fenêtre de 20 jours de trading (~1 mois)
            volatility_series = log_returns.rolling(window=20).std() * np.sqrt(252) * 100
            
            if volatility_series.empty or pd.isna(volatility_series.iloc[-1]):
                current_vol = 20.0
            else:
                current_vol = float(volatility_series.iloc[-1])

            # --- PHASE 4 : LOGIQUE DE DÉCISION MATRICIELLE ---
            dist_ema200 = ((last_close / last_ema200) - 1) * 100
            
            status = "NEUTRE"
            multiplier = 0.5 # Exposition par défaut 50%

            # Matrice de décision croisant Tendance (EMA) et Risque (Volatilité)
            if last_close > last_ema200:
                if current_vol < self.threshold_vol:
                    status = "BULLISH (Sain)"
                    multiplier = 1.0 # Pleine confiance : 100% de la position
                else:
                    status = "BULLISH (Volatile)"
                    multiplier = 0.7 # Marché haussier mais nerveux : 70%
            else:
                if current_vol > self.threshold_vol:
                    status = "BEARISH (Panique)"
                    multiplier = 0.0 # Marché dangereux : Cash uniquement
                else:
                    status = "BEARISH (Correction)"
                    multiplier = 0.3 # Sous l'EMA200 mais calme : 30%

            return {
                "status": status,
                "multiplier": multiplier,
                "volatility": round(current_vol, 2),
                "last_price": round(last_close, 2),
                "dist_ema_200": round(dist_ema200, 2),
                "trend_50_200": "UP" if last_ema50 > last_ema200 else "DOWN",
                "last_update": datetime.now().strftime("%H:%M:%S")
            }

        except Exception as e:
            logging.error(f"Erreur critique dans MarketRegimeFilter: {e}")
            return self._get_default_status()

    def _get_default_status(self):
        """Fallback sécurisé en cas d'erreur API ou Rate Limit."""
        return {
            "status": "INDÉTERMINÉ (Mode Prudence)",
            "multiplier": 0.5,
            "volatility": 20.0,
            "last_price": 0.0,
            "dist_ema_200": 0.0,
            "trend_50_200": "NEUTRAL",
            "last_update": datetime.now().strftime("%H:%M:%S")
        }

    def get_dynamic_allocation(self, base_size):
        """
        Ajuste dynamiquement la taille d'une ligne selon le régime de marché.
        Si base_size = 1000€ et multiplier = 0.7, le bot investira 700€.
        """
        mkt = self.get_market_status()
        return base_size * mkt["multiplier"]
