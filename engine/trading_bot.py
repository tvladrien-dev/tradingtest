import pandas as pd
import numpy as np
import ta
import logging

class TradingBotPEA:
    """
    Moteur de trading Alpha Quant v2.5.
    Logique : Tendance EMA200 + RSI Accumulation + Confirmation MACD + Volatilité ATR.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("TradingBot")

    def analyze(self, ticker, df):
        """
        Analyse un actif selon la stratégie combinée pour PEA :
        1. Tendance : Prix > EMA 200 (Condition Sine Qua Non)
        2. Momentum : RSI entre 30 et 55 (Pas de surachat, potentiel de hausse)
        3. Cycle : MACD > Ligne de Signal (Confirmation de l'impulsion)
        4. Risque : Mesure de l'ATR pour le dimensionnement
        """
        try:
            # Vérification de la profondeur historique pour l'EMA 200
            if df is None or len(df) < 200:
                self.logger.warning(f"Historique insuffisant pour {ticker} ({len(df) if df is not None else 0} jours)")
                return None

            # --- 1. CALCUL DES INDICATEURS (BIBLIOTHÈQUE TA) ---
            
            # TENDANCE : Moyenne Mobile Exponentielle 200 jours
            df['EMA200'] = ta.trend.ema_indicator(df['Close'], window=200)
            
            # MOMENTUM : Relative Strength Index 14 jours
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # CYCLE : MACD (Moving Average Convergence Divergence)
            macd_obj = ta.trend.MACD(
                df['Close'], 
                window_slow=26, 
                window_fast=12, 
                window_sign=9
            )
            df['MACD'] = macd_obj.macd()
            df['MACD_Signal'] = macd_obj.macd_signal()
            df['MACD_Diff'] = macd_obj.macd_diff() # Histogramme
            
            # VOLATILITÉ : Average True Range (Pour les futures limites de Stop/Profit)
            df['ATR'] = ta.volatility.average_true_range(
                df['High'], 
                df['Low'], 
                df['Close'], 
                window=14
            )

            # --- 2. EXTRACTION DES DONNÉES DE DÉCISION ---
            
            last_close = df['Close'].iloc[-1]
            last_ema200 = df['EMA200'].iloc[-1]
            last_rsi = df['RSI'].iloc[-1]
            last_macd = df['MACD'].iloc[-1]
            last_macd_sig = df['MACD_Signal'].iloc[-1]
            last_atr = df['ATR'].iloc[-1]
            
            # Calcul de la distance à l'EMA 200
            dist_ema = ((last_close / last_ema200) - 1) * 100

            # --- 3. LOGIQUE DE FILTRAGE ET SIGNAL ---
            
            # RÈGLE 1 : Tendance de fond (On n'achète que ce qui monte à long terme)
            is_bullish_trend = last_close > last_ema200
            
            # RÈGLE 2 : Zone de prix saine (RSI entre 30 et 55)
            # On évite le surachat (> 70) et on cherche la reprise
            is_rsi_ok = 30 <= last_rsi <= 55
            
            # RÈGLE 3 : Confirmation du mouvement (Croisement MACD)
            is_macd_bullish = last_macd > last_macd_sig
            
            # --- 4. DÉTERMINATION DU SIGNAL ET STATUT ---
            
            signal = 0
            status = "NEUTRE"
            
            # Le signal d'achat nécessite la validation des 3 conditions
            if is_bullish_trend and is_rsi_ok and is_macd_bullish:
                signal = 1
                status = "ACHAT"
            
            # Diagnostics pour l'UI (Dashboard)
            elif not is_bullish_trend:
                status = "SOUS MM200"
            elif last_rsi > 55:
                status = "SURACHAT"
            elif not is_macd_bullish:
                status = "ATTENTE MACD"

            # --- 5. ENCAPSULATION DES RÉSULTATS ---
            
            return {
                'Ticker': ticker,
                'Close': round(last_close, 2),
                'EMA200': round(last_ema200, 2),
                'Dist_EMA200': round(dist_ema, 2),
                'RSI': round(last_rsi, 2),
                'MACD': round(last_macd, 4),
                'MACD_Sig': round(last_macd_sig, 4),
                'MACD_Hist': round(df['MACD_Diff'].iloc[-1], 4),
                'ATR': round(last_atr, 2),
                'Change': round(df['Close'].pct_change().iloc[-1] * 100, 2),
                'Signal': signal,
                'Status': status,
                'Timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Erreur d'analyse critique pour {ticker}: {e}")
            return None
