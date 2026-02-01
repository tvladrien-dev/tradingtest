import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
import time
import os
from datetime import datetime

# --- CONFIGURATION SYSTÈME CRITIQUE 2026 ---
# Fix pour Streamlit Cloud : Redirection forcée du cache vers un dossier accessible en écriture
# Cela évite l'erreur "OperationalError: database is locked"
try:
    cache_path = '/tmp/yfinance_cache'
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    yf.set_tz_cache_location(cache_path)
except Exception as e:
    # Fallback silencieux si le système de fichiers est restreint
    pass

# Configuration du logging haute précision pour le monitoring en temps réel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    QUANT MASTER v12.6.0 - ÉDITION INTÉGRALE
    Système expert de trading avec scoring probabiliste et résilience multi-flux.
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        # Topic NTFY pour les alertes mobiles (à personnaliser)
        self.ntfy_url = "https://ntfy.sh/trading_master_2026_notif" 
        self.last_sync = None
        self.data_store = {}
        self.last_results = []
        logger.info("Moteur Elite initialisé - Prêt pour exécution.")

    # --- SECTION : ACQUISITION DE DONNÉES ET RÉSILIENCE API ---

    def sync_market_data(self, period="2y", interval="1d"):
        """Téléchargement par lots pour contourner le Rate Limit et les erreurs 404."""
        if not self.tickers:
            return {}

        # Blacklist dynamique basée sur tes logs (actifs délistés ou corrompus)
        blacklist = [
            'POL-USD', 'COMP-USD', 'GRT-USD', 'MNT-USD', 'ALT-USD', 
            'BOUY.PA', 'EXO.PA', 'FDJ.PA', 'TRIA.PA', 'ALMD.PA', 'LUM=F',
            'RELX.AS', 'BPER.MI', 'AGEAS.BR', 'IMX-USD', 'GMX-USD',
            'PEPE-USD', 'RON-USD', 'BRETT-USD', 'TAO-USD', 'AXL-USD'
        ]
        active_tickers = [t for t in self.tickers if t not in blacklist]

        logger.info(f"Synchronisation de {len(active_tickers)} actifs par lots de 40...")
        
        # Découpage en lots (Chunks) pour éviter le bannissement IP par Yahoo Finance
        chunk_size = 40
        for i in range(0, len(active_tickers), chunk_size):
            chunk = active_tickers[i:i + chunk_size]
            try:
                # Utilisation de threads=True pour optimiser le temps de calcul
                raw_data = yf.download(
                    tickers=chunk,
                    period=period,
                    interval=interval,
                    group_by='ticker',
                    auto_adjust=True,
                    threads=True,
                    progress=False
                )

                for ticker in chunk:
                    try:
                        # Gestion intelligente du format de retour (Single vs MultiIndex)
                        if len(chunk) == 1:
                            df = raw_data.copy()
                        else:
                            if ticker not in raw_data.columns.levels[0]:
                                continue
                            df = raw_data[ticker].copy()
                        
                        df = df.dropna(subset=['Close'])
                        
                        # Vérification de l'historique suffisant pour l'EMA 200
                        if len(df) >= 200:
                            self.data_store[ticker] = self._enrich_indicators(df)
                    except Exception:
                        continue
                
                # Pause stratégique (Anti-Rate Limit)
                time.sleep(1.5)
                
            except Exception as e:
                logger.error(f"Échec sur le lot {i} : {e}")

        self.last_sync = datetime.now()
        return self.data_store

    def _enrich_indicators(self, df):
        """Calcul de la matrice complète d'indicateurs techniques Alpha."""
        # Moyennes Mobiles Exponentielles (Tendance)
        df['EMA50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Momentum et Force de la tendance (RSI / ADX)
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()
        
        # Volatilité (ATR pour le Risk Management)
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        
        # Accélération (MACD Histogramme)
        macd = ta.trend.MACD(df['Close'])
        df['MACD_Hist'] = macd.macd_diff()
        
        return df

    # --- SECTION : ANALYSE ET SCORING PROBABILISTE ---

    def get_news_sentiment(self, ticker):
        """Scoring sémantique des flux d'actualités financières."""
        try:
            stock = yf.Ticker(ticker)
            news = getattr(stock, 'news', [])
            if not news: return "Neutre ⚪", 0
            
            score = 0
            pos_words = {'hausse', 'profit', 'achat', 'croissance', 'positif', 'gain', 'upgrade'}
            neg_words = {'chute', 'baisse', 'perte', 'alerte', 'négatif', 'déficit', 'downgrade'}
            
            for item in news[:5]:
                title = item.get('title', '').lower()
                score += sum(1 for w in pos_words if w in title)
                score -= sum(1 for w in neg_words if w in title)
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except:
            return "Indisponible ❓", 0

    def process_signals(self):
        """Moteur de décision probabiliste avec protection contre les dépréciations Pandas."""
        results = []
        
        # Récupération du VIX pour le "Fear & Greed" contextuel
        try:
            vix_df = yf.download("^VIX", period="1d", progress=False)
            vix_val = float(vix_df['Close'].iloc[-1].item()) if not vix_df.empty else 22.0
        except:
            vix_val = 22.0

        for ticker, df in self.data_store.items():
            try:
                if len(df) < 2: continue
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Extraction sécurisée des scalaires avec .item() (Requis par Pandas 2.2+)
                price = float(last['Close'].item())
                rsi_val = float(last['RSI'].item())
                adx_val = float(last['ADX'].item())
                ema200 = float(last['EMA200'].item())
                ema50 = float(last['EMA50'].item())
                macd_h = float(last['MACD_Hist'].item())
                prev_macd_h = float(prev['MACD_Hist'].item())
                atr = float(last['ATR'].item())

                # Algorithme de Scoring Propriétaire (Max 100 points)
                prob = 0
                if price > ema200: prob += 30
                if ema50 > ema200: prob += 20
                if adx_val > 25: prob += 20
                if macd_h > prev_macd_h: prob += 15
                if 40 <= rsi_val <= 65: prob += 10
                if vix_val < 22: prob += 5

                # Risk Management : Calcul dynamique des Stop-Loss et Take-Profit
                sl_pct = ( (atr * 2) / price ) * 100
                tp_price = price + (atr * 4)
                gain_pct = ( (atr * 4) / price ) * 100

                # Détermination de l'action trading
                action = "VEILLE"
                if prob >= 75: action = "ACHAT"
                elif rsi_val > 80: action = "VENTE"

                sentiment, _ = self.get_news_sentiment(ticker)
                
                results.append({
                    'ticker': ticker,
                    'prix': round(price, 2),
                    'rsi': round(rsi_val, 2),
                    'probabilite': prob,
                    'action': action,
                    'sentiment': sentiment,
                    'sl_pct': round(sl_pct, 2),
                    'tp': round(tp_price, 2),
                    'gain_pct': round(gain_pct, 2),
                    'last_update': datetime.now().strftime("%H:%M")
                })
            except Exception:
                continue
        
        # Tri des résultats par probabilité décroissante
        self.last_results = sorted(results, key=lambda x: x['probabilite'], reverse=True)
        return self.last_results

    # --- SECTION : NOTIFICATIONS ET UTILITAIRES (Fix AttributeError) ---

    def send_notification(self, signal):
        """Envoie une alerte push via NTFY (Requis par app.py)."""
        if signal['action'] == "VEILLE":
            return False
            
        emoji = "🚀" if signal['action'] == "ACHAT" else "⚠️"
        title = f"{emoji} {signal['action']} : {signal['ticker']} ({signal['probabilite']}%)"
        body = (
            f"💰 Prix: {signal['prix']}€\n"
            f"🛡️ SL: -{signal['sl_pct']}% | TP: +{signal['gain_pct']}%"
        )
        
        try:
            res = requests.post(
                self.ntfy_url,
                data=body.encode('utf-8'),
                headers={
                    "Title": title.encode('utf-8'),
                    "Priority": "high",
                    "Tags": "money,chart_with_upwards_trend"
                },
                timeout=5
            )
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Échec notification {signal['ticker']} : {e}")
            return False

    def get_last_signals(self):
        """Récupère les derniers signaux calculés pour l'interface."""
        return self.last_results if self.last_results else self.process_signals()

    def get_data_for_ticker(self, ticker):
        """Expose le DataFrame historique pour les graphiques Plotly."""
        return self.data_store.get(ticker)
