import pandas as pd
import numpy as np
import logging

class TradingBotPEA:
    """
    Moteur de décision Alpha pour le PEA (Alpha Convergence 2026).
    Analyse les indicateurs techniques calculés par le DataLoader et 
    génère des signaux d'achat basés sur la convergence Tendance/Momentum.
    """
    def __init__(self):
        self.strategy_name = "Alpha Convergence"
        self.version = "12.5.0"
        # Seuils internes pour la validation du signal
        self.rsi_oversold = 35
        self.rsi_neutral = 50

    def analyze(self, ticker, df):
        """
        Analyse les séries temporelles pour détecter une anomalie statistique positive.
        Retourne un dictionnaire contenant le signal et les métriques de décision.
        """
        try:
            # Sécurité : On vérifie que le DataFrame contient assez de données
            # Il faut au moins 200 jours pour que la EMA200 soit valide
            if df is None or len(df) < 200:
                logging.warning(f"Données insuffisantes pour {ticker} ({len(df) if df is not None else 0}/200 jours)")
                return None

            # On récupère les deux dernières lignes pour détecter les croisements
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            # --- LOGIQUE DE DÉTECTION ALPHA ---
            
            # 1. Filtre de Tendance Long Terme (Structure de Marché)
            # Le prix doit être au-dessus de la moyenne mobile 200 (Biais haussier institutionnel)
            is_bullish_trend = last_row['Close'] > last_row['EMA200']
            
            # 2. Signal de Momentum (Croisement de Moyennes Mobiles)
            # La moyenne rapide (20) passe au-dessus de la moyenne lente (50)
            is_momentum_positive = last_row['EMA20'] > last_row['EMA50']
            
            # 3. Signal de Retournement RSI (Mean Reversion)
            # On cherche une sortie de zone de survente (le RSI repasse au-dessus de 35)
            # OU un RSI qui reste sain (< 60) pendant une poussée de prix
            rsi_rebound = prev_row['RSI'] < self.rsi_oversold and last_row['RSI'] > self.rsi_oversold
            
            # 4. Filtre de Volatilité (ATR)
            # On évite d'entrer si la bougie actuelle est anormalement explosive (risque de mèche)
            is_volatility_stable = last_row['Close'] < (last_row['BB_High'] * 1.01)

            # --- GÉNÉRATION DU SIGNAL FINAL ---
            # Un signal d'achat (1) est généré si :
            # (Tendance Haussière ET Rebond RSI) OU (Tendance Haussière ET Momentum Confirmé)
            signal = 0
            if is_bullish_trend and is_volatility_stable:
                if rsi_rebound:
                    signal = 1
                elif is_momentum_positive and last_row['RSI'] < self.rsi_neutral:
                    signal = 1

            # --- PRÉPARATION DU RÉSUMÉ ---
            return {
                "Ticker": ticker,
                "Close": float(last_row['Close']),
                "Change": round(((last_row['Close'] / prev_row['Close']) - 1) * 100, 2),
                "RSI": round(float(last_row['RSI']), 2),
                "EMA200": round(float(last_row['EMA200']), 2),
                "Dist_EMA200": round(((last_row['Close'] / last_row['EMA200']) - 1) * 100, 2),
                "ATR": round(float(last_row['ATR']), 2),
                "Signal": signal,
                "Status": "ACHAT" if signal == 1 else "OBSERVATION"
            }

        except Exception as e:
            logging.error(f"Erreur lors de l'analyse Alpha de {ticker} : {str(e)}")
            return None

    def get_strategy_info(self):
        """Retourne les métadonnées de la stratégie."""
        return {
            "Name": self.strategy_name,
            "Version": self.version,
            "Indicators": ["EMA200", "EMA50", "EMA20", "RSI", "ATR", "Bollinger"]
        }
