import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
import time
import os
from datetime import datetime

# --- CONFIGURATION ENVIRONNEMENTALE ---
try:
    # Indispensable sur Streamlit Cloud pour éviter les erreurs de base de données verrouillée
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
    QUANT MASTER V1 - VERSION FULL PRODUCTION
    Analyse : EMA200 + Higher Lows + Sentiment News + Macro VIX + ATR Trail SL
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        # URL NTFY - À personnaliser dans votre application
        self.ntfy_url = "https://ntfy.sh/votre_topic_unique_2026" 
        self.data_store = {}
        self.last_results = []
        logger.info("Bot V1 Elite initialisé - En attente de signaux confirmés.")

    # --- ÉTAPE 1 : ACQUISITION MASSIVE ---

    def sync_market_data(self, period="2y", interval="1d"):
        """Téléchargement par lots de 40 pour la résilience API."""
        if not self.tickers: return {}

        # Exclusion des actifs identifiés comme problématiques dans les logs récents
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
                        # Extraction sécurisée (MultiIndex ou DataFrame simple)
                        if len(chunk) == 1:
                            df = raw_data.copy()
                        else:
                            if ticker not in raw_data.columns.levels[0]: continue
                            df = raw_data[ticker].copy()
                        
                        df = df.dropna(subset=['Close'])
                        
                        # Validation technique : EMA200 nécessite 200 points
                        if len(df) >= 200:
                            self.data_store[ticker] = self._calculate_v1_indicators(df)
                    except Exception: continue
                
                time.sleep(1.2) # Pause anti-bannissement
            except Exception as e:
                logger.error(f"Erreur Sync Lot {i}: {e}")
        
        return self.data_store

    def _calculate_v1_indicators(self, df):
        """Calcul des indicateurs de la stratégie V1."""
        # Tendance Majeure
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Analyse Graphique : Confirmation des creux ascendants (Higher Lows sur 10j)
        df['low_rolling'] = df['Low'].rolling(window=10).min()
        df['is_uptrend'] = df['low_rolling'] >= df['low_rolling'].shift(5)
        
        # Momentum & Force
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Volatilité (Base du Stop Loss Suiveur)
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        
        return df

    # --- ÉTAPE 2 : ANALYSE DU MONDE (SENTIMENT & INFOS) ---

    def get_market_intelligence(self, ticker):
        """Analyse sémantique des actualités mondiales et données sectorielles."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            news = getattr(stock, 'news', [])
            
            # Algorithme de sentiment NLP simplifié
            score = 0
            pos = {'profit', 'growth', 'buy', 'positive', 'gain', 'croissance', 'achat', 'succès'}
            neg = {'loss', 'fall', 'alert', 'negative', 'crash', 'baisse', 'alerte', 'déficit'}
            
            for item in news[:5]:
                title = item.get('title', '').lower()
                score += sum(1 for w in pos if w in title)
                score -= sum(1 for w in neg if w in title)
            
            sentiment = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return sentiment, info.get('sector', 'Divers'), info.get('longName', ticker)
        except:
            return "Neutre ⚪", "Inconnu", ticker

    # --- ÉTAPE 3 : MOTEUR DE DÉCISION ET TRI ---

    def process_signals(self):
        """Analyse probabiliste V1 : Technique + Graphique + Macro + News."""
        results = []
        
        # Filtre Macro Global : Indice VIX
        try:
            vix_df = yf.download("^VIX", period="1d", progress=False)
            vix_val = float(vix_df['Close'].iloc[-1].item())
        except: vix_val = 22.0

        for ticker, df in self.data_store.items():
            try:
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Conversion sécurisée en scalaires
                price = float(last['Close'].item())
                ema200 = float(last['EMA200'].item())
                rsi = float(last['RSI'].item())
                macd = float(last['MACD'].item())
                macd_h = float(last['MACD_Hist'].item())
                atr = float(last['ATR'].item())
                is_uptrend = bool(last['is_uptrend'])

                # --- ALGORITHME DE SCORING V1 (Base 100) ---
                prob = 0
                if price > ema200: prob += 35         # Règle d'or : Au-dessus de l'EMA200
                if is_uptrend: prob += 25             # Confirmation graphique (Higher Lows)
                if 40 <= rsi <= 65: prob += 15        # RSI en zone de rebond saine
                if macd_h > prev['MACD_Hist']: prob += 15 # Accélération haussière
                if vix_val < 25: prob += 10           # Marché global serein

                # --- RISK MANAGEMENT (ATR x2) ---
                sl_distance = atr * 2
                sl_pct = round((sl_distance / price) * 100, 2)
                # Objectif de gain : Ratio 1:2 (On cherche 2x plus que le risque)
                gain_vise_pct = sl_pct * 2
                tp_price = round(price * (1 + gain_vise_pct/100), 2)

                # Logique d'action
                action = "VEILLE"
                if prob >= 75 and vix_val < 30: 
                    action = "ACHAT"
                elif rsi > 80: 
                    action = "VENTE"

                sentiment, sector, nom = self.get_market_intelligence(ticker)

                results.append({
                    'ticker': ticker, 'nom': nom, 'prix': round(price, 2),
                    'rsi': round(rsi, 2), 'macd': round(macd, 2), 'vix': round(vix_val, 2),
                    'ema200': round(ema200, 2), 'action': action, 'probabilite': prob,
                    'sl_pct': sl_pct, 'tp': tp_price, 'gain_pct': round(gain_vise_pct, 2),
                    'sector': sector, 'sentiment': sentiment
                })
            except Exception: continue
        
        # --- TRI FINAL DEMANDÉ ---
        # 1. ACHAT en priorité, puis VENTE
        # 2. Tri par Probabilité décroissante (les plus sûrs en haut)
        results.sort(key=lambda x: (x['action'] != 'ACHAT', x['action'] != 'VENTE', -x['probabilite']))
        self.last_results = results
        return results

    # --- ÉTAPE 4 : NOTIFICATIONS ENRICHIES ---

    def send_notification(self, s):
        """Envoi de l'alerte NTFY avec le format complet exigé."""
        if s['action'] == "VEILLE": return False
        
        emoji = "🚀" if s['action'] == "ACHAT" else "⚠️"
        title = f"{emoji} {s['action']} : {s['ticker']} ({s['probabilite']}%)"
        
        # Construction du message riche
        message = (
            f"📍 Nom: {s['nom']}\n"
            f"🏷️ Ticker: {s['ticker']}\n"
            f"📊 Technique: RSI {s['rsi']} | MACD {s['macd']}\n"
            f"🌍 Macro: VIX {s['vix']} | EMA200 {s['ema200']}\n"
            f"📰 Sentiment: {s['sentiment']}\n"
            f"---------------------------\n"
            f"💰 Prix d'Achat Conseillé: {s['prix']}€\n"
            f"🎯 Prix de Vente (TP): {s['tp']}€\n"
            f"📈 Gains Prévus: +{s['gain_pct']}%\n"
            f"🛡️ SL Suiveur: {s['sl_pct']}% (ATR x2)"
        )
        
        try:
            requests.post(
                self.ntfy_url, 
                data=message.encode('utf-8'), 
                headers={
                    "Title": title.encode('utf-8'),
                    "Priority": "high",
                    "Tags": "chart_with_upwards_trend,moneybag"
                },
                timeout=5
            )
            return True
        except: return False

    def get_last_signals(self):
        return self.last_results

    def get_data_for_ticker(self, ticker):
        return self.data_store.get(ticker)
