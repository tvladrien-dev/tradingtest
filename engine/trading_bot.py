import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
import time
import os
from datetime import datetime

# --- CONFIGURATION DU SYSTÈME ---
try:
    # Optimisation pour Streamlit Cloud : Gestion du cache SQLite
    cache_dir = "/tmp/yf_cache_v1_final"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    yf.set_tz_cache_location(cache_dir)
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TradingBot_V1_Final")

class TradingBotV1Elite:
    """
    QUANT MASTER V1 - VERSION INTÉGRALE
    Stratégie : Achat sur repli (RSI <= 35) en tendance saine (EMA 200).
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        # URL NTFY à personnaliser
        self.ntfy_url = "https://ntfy.sh/votre_topic_secret_2026" 
        self.data_store = {}
        self.last_results = []
        logger.info("Moteur V1 activé : Focus RSI < 35 & EMA 200.")

    # --- ACQUISITION DES DONNÉES ---

    def sync_market_data(self, period="2y", interval="1d"):
        """Téléchargement par lots pour éviter les limitations d'API."""
        if not self.tickers: return {}

        # Nettoyage des tickers problématiques
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
                        # Extraction robuste du DataFrame
                        if len(chunk) == 1:
                            df = raw_data.copy()
                        else:
                            if ticker not in raw_data.columns.levels[0]: continue
                            df = raw_data[ticker].copy()
                        
                        df = df.dropna(subset=['Close'])
                        # Validation : EMA 200 nécessite 200 points de données
                        if len(df) >= 200:
                            self.data_store[ticker] = self._calculate_metrics(df)
                    except Exception: continue
                
                time.sleep(1.2) # Temporisation anti-rate limit
            except Exception as e:
                logger.error(f"Erreur Sync Lot {i}: {e}")
        
        return self.data_store

    def _calculate_metrics(self, df):
        """Calcul de la matrice technique V1 complète."""
        # Tendance : Moyenne Mobile Exponentielle 200
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Momentum : RSI (Indice de force relative)
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # Signal de sortie : MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Volatilité : ATR (Average True Range) pour le SL
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        
        # Analyse graphique : Creux ascendants (Higher Lows sur 10j)
        df['low_rolling'] = df['Low'].rolling(window=10).min()
        df['is_uptrend'] = df['low_rolling'] >= df['low_rolling'].shift(5)
        
        return df

    # --- ANALYSE DE L'ACTUALITÉ ET DU CONTEXTE ---

    def get_intelligence(self, ticker):
        """Récupère le sentiment des news et les informations sectorielles."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            news = getattr(stock, 'news', [])
            
            score = 0
            pos = {'profit', 'growth', 'buy', 'positive', 'gain', 'croissance', 'achat', 'hausse'}
            neg = {'loss', 'fall', 'alert', 'negative', 'crash', 'baisse', 'alerte', 'déficit'}
            
            for item in news[:5]:
                title = item.get('title', '').lower()
                score += sum(1 for w in pos if w in title)
                score -= sum(1 for w in neg if w in title)
            
            sentiment = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return sentiment, info.get('sector', 'Divers'), info.get('longName', ticker)
        except:
            return "Neutre ⚪", "Inconnu", ticker

    # --- MOTEUR DE DÉCISION (SCORING) ---

    def process_signals(self):
        """Moteur V1 : Priorité RSI <= 35 + EMA 200."""
        results = []
        
        # Indicateur de peur macro (VIX)
        try:
            vix_df = yf.download("^VIX", period="1d", progress=False)
            vix_val = float(vix_df['Close'].iloc[-1].item())
        except: vix_val = 22.0

        for ticker, df in self.data_store.items():
            try:
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                price = float(last['Close'].item())
                ema200 = float(last['EMA200'].item())
                rsi = float(last['RSI'].item())
                atr = float(last['ATR'].item())
                macd_h = float(last['MACD_Hist'].item())

                # --- ALGORITHME DE SCORING V1 ---
                prob = 0
                # 1. Filtre de Tendance (40 points)
                if price > ema200: prob += 40 
                
                # 2. Filtre de Survente (40 points) - TA CONDITION RSI < 35
                if rsi <= 35: 
                    prob += 40 
                elif 35 < rsi <= 45:
                    prob += 15 # Proche de la zone mais pas idéal
                
                # 3. Filtre Macro et Momentum (20 points)
                if vix_val < 28: prob += 10
                if macd_h > prev['MACD_Hist']: prob += 10

                # --- GESTION DU RISQUE (ATR x2) ---
                sl_distance = atr * 2
                sl_pct = round((sl_distance / price) * 100, 2)
                # Ratio Risk/Reward 1:2
                gain_vise_pct = sl_pct * 2
                tp_price = round(price * (1 + gain_vise_pct/100), 2)

                # Logique d'Action
                action = "VEILLE"
                # On achète si Tendance OK + RSI bas + Score global haut
                if prob >= 75 and price > ema200 and rsi <= 40:
                    action = "ACHAT"
                elif rsi > 75:
                    action = "VENTE"

                sentiment, sector, nom = self.get_intelligence(ticker)

                results.append({
                    'ticker': ticker, 'nom': nom, 'prix': round(price, 2),
                    'rsi': round(rsi, 2), 'macd': round(float(last['MACD'].item()), 2), 
                    'vix': round(vix_val, 2), 'ema200': round(ema200, 2), 
                    'action': action, 'probabilite': prob,
                    'sl_pct': sl_pct, 'tp': tp_price, 'gain_pct': round(gain_vise_pct, 2),
                    'sector': sector, 'sentiment': sentiment
                })
            except Exception: continue
        
        # TRI : ACHAT en premier, puis VENTE, par probabilité décroissante
        results.sort(key=lambda x: (x['action'] != 'ACHAT', x['action'] != 'VENTE', -x['probabilite']))
        self.last_results = results
        return results

    # --- NOTIFICATIONS ---

    def send_notification(self, s):
        """Alerte NTFY complète selon tes exigences."""
        if s['action'] == "VEILLE": return False
        
        emoji = "💎" if s['action'] == "ACHAT" else "⚠️"
        title = f"{emoji} {s['action']} : {s['ticker']} (RSI: {s['rsi']})"
        
        msg = (
            f"📍 Nom: {s['nom']}\n"
            f"🏷️ Ticker: {s['ticker']}\n"
            f"📊 RSI: {s['rsi']} | MACD: {s['macd']}\n"
            f"🌍 Macro: VIX {s['vix']} | EMA200 {s['ema200']}\n"
            f"📰 Sentiment: {s['sentiment']}\n"
            f"---------------------------\n"
            f"💰 Prix d'Achat : {s['prix']}€\n"
            f"🎯 Prix de Vente (TP) : {s['tp']}€\n"
            f"📈 Gain Prévu : +{s['gain_pct']}%\n"
            f"🛡️ Stop Loss Suiveur : {s['sl_pct']}% (ATR x2)"
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
