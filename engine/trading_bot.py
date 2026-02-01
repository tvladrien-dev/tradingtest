import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
import time
import os
from datetime import datetime

# --- CONFIGURATION DU CACHE RÉSILIENT ---
try:
    cache_dir = "/tmp/yf_cache_v1_final"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    yf.set_tz_cache_location(cache_dir)
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TradingBot_V1_Elite")

class TradingBotV1Elite:
    """
    QUANT MASTER v1 - STRATÉGIE TENDANCE SAINE & SENTIMENT GLOBAL
    Analyse graphique, Macro (VIX) et Actualités mondiales.
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        # Endpoint NTFY (à personnaliser)
        self.ntfy_url = "https://ntfy.sh/votre_topic_secret_2026" 
        self.data_store = {}
        self.last_results = []
        logger.info("Bot V1 Initialisé : En attente de confirmation de tendance.")

    # --- SECTION : ACQUISITION MASSIVE (BATCH PROCESSING) ---

    def sync_market_data(self, period="2y", interval="1d"):
        """Téléchargement par lots de 40 pour éviter les bannissements Yahoo."""
        if not self.tickers: return {}

        # Nettoyage des tickers problématiques vus dans les logs
        blacklist = ['POL-USD', 'TAO-USD', 'AXL-USD', 'RON-USD', 'BRETT-USD']
        active_tickers = [t for t in self.tickers if t not in blacklist]

        chunk_size = 40
        for i in range(0, len(active_tickers), chunk_size):
            chunk = active_tickers[i:i + chunk_size]
            try:
                raw_data = yf.download(
                    tickers=chunk, period=period, interval=interval,
                    group_by='ticker', auto_adjust=True, threads=True, progress=False
                )

                for ticker in chunk:
                    try:
                        df = raw_data[ticker].copy() if len(chunk) > 1 else raw_data.copy()
                        df = df.dropna(subset=['Close'])
                        # Minimum 200 jours pour l'EMA200
                        if len(df) >= 200:
                            self.data_store[ticker] = self._enrich_v1_indicators(df)
                    except: continue
                time.sleep(1.2)
            except Exception as e:
                logger.error(f"Erreur Sync Lot {i}: {e}")
        
        return self.data_store

    def _enrich_v1_indicators(self, df):
        """Calcul de la matrice technique complète V1."""
        # --- Tendance ---
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # --- Analyse Graphique (Higher Lows sur 10 jours) ---
        df['low_rolling'] = df['Low'].rolling(window=10).min()
        df['is_uptrend'] = df['low_rolling'] >= df['low_rolling'].shift(10)
        
        # --- Momentum ---
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Hist'] = macd.macd_diff()
        
        # --- Volatilité (ATR pour Stop Loss) ---
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        
        return df

    # --- SECTION : ANALYSE EXTERNE (ACTUALITÉS & SECTEUR) ---

    def get_contextual_data(self, ticker):
        """Récupère le sentiment des news et les infos fondamentales."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            news = getattr(stock, 'news', [])
            
            # Analyse de sentiment simple
            score = 0
            pos_words = {'profit', 'croissance', 'achat', 'hausse', 'positif', 'gain', 'upgrade'}
            neg_words = {'chute', 'baisse', 'perte', 'alerte', 'négatif', 'faillite', 'downgrade'}
            
            for item in news[:5]:
                title = item.get('title', '').lower()
                score += sum(1 for w in pos_words if w in title)
                score -= sum(1 for w in neg_words if w in title)
            
            sentiment = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return sentiment, info.get('sector', 'Divers'), info.get('longName', ticker)
        except:
            return "Neutre ⚪", "Inconnu", ticker

    # --- SECTION : MOTEUR DE DÉCISION ET SCORING ---

    def process_signals(self):
        """Moteur V1 : Analyse graphique + Macro VIX + Scoring."""
        results = []
        
        # Filtre Macro : Indice de la peur (VIX)
        try:
            vix_df = yf.download("^VIX", period="1d", progress=False)
            vix_val = float(vix_df['Close'].iloc[-1].item())
        except: vix_val = 20.0

        for ticker, df in self.data_store.items():
            try:
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Extraction des valeurs scalaires
                price = float(last['Close'].item())
                ema200 = float(last['EMA200'].item())
                rsi = float(last['RSI'].item())
                macd = float(last['MACD'].item())
                macd_h = float(last['MACD_Hist'].item())
                atr = float(last['ATR'].item())
                is_uptrend = bool(last['is_uptrend'])

                # --- ALGORITHME DE SCORING V1 ---
                prob = 0
                if price > ema200: prob += 35         # Règle d'or : Tendance saine
                if is_uptrend: prob += 25             # Graphique : Creux ascendants
                if 40 <= rsi <= 65: prob += 15        # RSI non surchargé
                if macd_h > prev['MACD_Hist']: prob += 15 # MACD s'accélère
                if vix_val < 25: prob += 10           # Contexte marché calme

                # --- GESTION DU RISQUE (ATR x2) ---
                sl_amount = atr * 2
                sl_pct = round((sl_amount / price) * 100, 2)
                # Ratio Gain/Risque 1:2
                gain_visé_pct = sl_pct * 2
                tp_price = round(price * (1 + gain_visé_pct/100), 2)

                # Classification de l'action
                action = "VEILLE"
                if prob >= 75 and vix_val < 30: 
                    action = "ACHAT"
                elif rsi > 75: 
                    action = "VENTE"

                sentiment, sector, nom = self.get_contextual_data(ticker)

                results.append({
                    'ticker': ticker, 'nom': nom, 'prix': round(price, 2),
                    'rsi': round(rsi, 2), 'macd': round(macd, 2), 'vix': round(vix_val, 2),
                    'ema200': round(ema200, 2), 'action': action, 'probabilite': prob,
                    'sl_pct': sl_pct, 'tp': tp_price, 'gain_pct': round(gain_visé_pct, 2),
                    'sector': sector, 'sentiment': sentiment
                })
            except Exception: continue
        
        # TRI FINAL : ACHATS d'abord, puis VENTES, par probabilité décroissante
        results.sort(key=lambda x: (x['action'] != 'ACHAT', x['action'] != 'VENTE', -x['probabilite']))
        self.last_results = results
        return results

    # --- SECTION : NOTIFICATIONS ENRICHIES ---

    def send_notification(self, s):
        """Envoi NTFY avec détails complets demandés."""
        if s['action'] == "VEILLE": return False
        
        emoji = "🚀" if s['action'] == "ACHAT" else "⚠️"
        title = f"{emoji} {s['action']} : {s['ticker']} ({s['probabilite']}%)"
        
        msg = (
            f"Nom: {s['nom']}\n"
            f"Prix Actuel: {s['prix']}€ | EMA200: {s['ema200']}\n"
            f"RSI: {s['rsi']} | MACD: {s['macd']}\n"
            f"VIX: {s['vix']} | Sentiment: {s['sentiment']}\n"
            f"---------------------------\n"
            f"💰 Achat Conseillé: {s['prix']}€\n"
            f"🎯 Vente Conseillée: {s['tp']}€\n"
            f"📈 Gain Prévu: +{s['gain_pct']}%\n"
            f"🛡️ Stop Loss Suiveur: {s['sl_pct']}% (ATR x2)"
        )
        
        try:
            requests.post(self.ntfy_url, data=msg.encode('utf-8'), 
                          headers={"Title": title.encode('utf-8'), "Priority": "high"})
            return True
        except: return False

    def get_last_signals(self):
        return self.last_results

    def get_data_for_ticker(self, ticker):
        return self.data_store.get(ticker)
