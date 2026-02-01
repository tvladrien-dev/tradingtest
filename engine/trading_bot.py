import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
import time
import os
from datetime import datetime

# --- CONFIGURATION ENVIRONNEMENTALE CRITIQUE 2026 ---
# Streamlit Cloud interdit l'écriture dans les dossiers système.
# On force yfinance à utiliser /tmp pour éviter "OperationalError: database is locked".
try:
    cache_dir = "/tmp/yf_cache_production"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    yf.set_tz_cache_location(cache_dir)
except Exception as e:
    # Fallback sécurisé
    pass

# Logging professionnel pour le monitoring distant
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    QUANT MASTER v12.7.0 - ÉDITION DE PRODUCTION SANS SIMPLIFICATION
    Moteur de trading algorithmique avec filtrage d'actifs et scoring Alpha.
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        # Endpoint NTFY pour les alertes smartphone
        self.ntfy_url = "https://ntfy.sh/votre_topic_secret_unique_2026"
        self.last_sync = None
        self.data_store = {}
        self.last_results = []
        logger.info("Bot Elite initialisé - Moteur de résilience 2026 opérationnel.")

    # --- SECTION : ACQUISITION DE DONNÉES PAR LOTS (ANTI-BAN) ---

    def sync_market_data(self, period="2y", interval="1d"):
        """Téléchargement par lots pour éviter le Rate Limit et gérer les 404/Delisted."""
        if not self.tickers:
            return {}

        # Blacklist consolidée basée sur les logs d'erreurs récents
        blacklist = [
            'POL-USD', 'COMP-USD', 'GRT-USD', 'MNT-USD', 'ALT-USD', 
            'BOUY.PA', 'EXO.PA', 'FDJ.PA', 'TRIA.PA', 'ALMD.PA', 'LUM=F',
            'RELX.AS', 'BPER.MI', 'AGEAS.BR', 'IMX-USD', 'GMX-USD',
            'TAO-USD', 'AXL-USD', 'RON-USD', 'BRETT-USD', 'PEPE-USD'
        ]
        active_tickers = [t for t in self.tickers if t not in blacklist]

        logger.info(f"Synchronisation de {len(active_tickers)} actifs par lots de 40...")
        
        chunk_size = 40
        for i in range(0, len(active_tickers), chunk_size):
            chunk = active_tickers[i:i + chunk_size]
            try:
                # Utilisation de threads=True pour maximiser la vitesse de traitement
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
                        # Extraction robuste selon la structure MultiIndex de yfinance
                        if len(chunk) == 1:
                            df = raw_data.copy()
                        else:
                            if ticker not in raw_data.columns.levels[0]:
                                continue
                            df = raw_data[ticker].copy()
                        
                        df = df.dropna(subset=['Close'])
                        
                        # Le Bot nécessite au moins 200 jours pour l'EMA200
                        if len(df) >= 200:
                            self.data_store[ticker] = self._enrich_indicators(df)
                    except Exception as e:
                        continue
                
                # Sommeil de sécurité (Anti-Rate Limit)
                time.sleep(1.2)
                
            except Exception as e:
                logger.error(f"Erreur sur le lot {i} : {e}")

        self.last_sync = datetime.now()
        return self.data_store

    def _enrich_indicators(self, df):
        """Calcul exhaustif de la matrice d'indicateurs Alpha Matrix."""
        # --- Tendance ---
        df['EMA50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # --- Momentum ---
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()
        
        # --- Volatilité & Accélération ---
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        macd = ta.trend.MACD(df['Close'])
        df['MACD_Hist'] = macd.macd_diff()
        
        return df

    # --- SECTION : LOGIQUE DE SCORING ET DÉCISION ---

    def get_news_sentiment(self, ticker):
        """Scoring sémantique des actualités financières pour validation du signal."""
        try:
            stock = yf.Ticker(ticker)
            news = getattr(stock, 'news', [])
            if not news: return "Neutre ⚪", 0
            
            score = 0
            pos = {'hausse', 'profit', 'achat', 'croissance', 'positif', 'gain', 'upgrade'}
            neg = {'chute', 'baisse', 'perte', 'alerte', 'négatif', 'déficit', 'downgrade'}
            
            for item in news[:5]:
                title = item.get('title', '').lower()
                score += sum(1 for w in pos if w in title)
                score -= sum(1 for w in neg if w in title)
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except:
            return "Neutre ⚪", 0

    def process_signals(self):
        """Moteur de scoring probabiliste (Base 100) compatible Pandas 2.3+."""
        results = []
        
        # Contexte de marché (VIX)
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
                
                # Conversion scalaire sécurisée (.item()) pour éviter les FutureWarnings
                price = float(last['Close'].item())
                rsi_val = float(last['RSI'].item())
                adx_val = float(last['ADX'].item())
                ema200 = float(last['EMA200'].item())
                ema50 = float(last['EMA50'].item())
                macd_h = float(last['MACD_Hist'].item())
                prev_macd_h = float(prev['MACD_Hist'].item())
                atr = float(last['ATR'].item())

                # Algorithme de Scoring Propriétaire
                prob = 0
                if price > ema200: prob += 30
                if ema50 > ema200: prob += 20
                if adx_val > 25: prob += 20
                if macd_h > prev_macd_h: prob += 15
                if 40 <= rsi_val <= 65: prob += 10
                if vix_val < 22: prob += 5

                # Risk Management (SL: 2*ATR, TP: 4*ATR)
                sl_pct = ((atr * 2) / price) * 100
                tp_price = price + (atr * 4)
                gain_pct = ((atr * 4) / price) * 100

                action = "VEILLE"
                if prob >= 75: action = "ACHAT"
                elif rsi_val > 80: action = "VENTE"

                sentiment_label, _ = self.get_news_sentiment(ticker)
                
                results.append({
                    'ticker': ticker,
                    'prix': round(price, 2),
                    'rsi': round(rsi_val, 2),
                    'probabilite': prob,
                    'action': action,
                    'sentiment': sentiment_label,
                    'sl_pct': round(sl_pct, 2),
                    'tp': round(tp_price, 2),
                    'gain_pct': round(gain_pct, 2),
                    'last_update': datetime.now().strftime("%H:%M")
                })
            except Exception:
                continue
        
        # Tri par probabilité de succès
        self.last_results = sorted(results, key=lambda x: x['probabilite'], reverse=True)
        return self.last_results

    # --- SECTION : SYSTÈME DE NOTIFICATIONS (API REQUESTS) ---

    def send_notification(self, signal):
        """Envoi des alertes vers smartphone via NTFY (Requis par app.py)."""
        if signal['action'] == "VEILLE":
            return False
            
        emoji = "🚀" if signal['action'] == "ACHAT" else "⚠️"
        title = f"{emoji} {signal['action']} : {signal['ticker']} ({signal['probabilite']}%)"
        message = (f"💰 Prix: {signal['prix']}€\n"
                  f"🛡️ SL: -{signal['sl_pct']}% | TP: +{signal['gain_pct']}%")
        
        try:
            res = requests.post(
                self.ntfy_url,
                data=message.encode('utf-8'),
                headers={
                    "Title": title.encode('utf-8'),
                    "Priority": "high",
                    "Tags": "chart_with_upwards_trend,moneybag"
                },
                timeout=5
            )
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Erreur notification {signal['ticker']} : {e}")
            return False

    def get_last_signals(self):
        """Retourne les signaux en cache pour l'UI."""
        return self.last_results if self.last_results else self.process_signals()

    def get_data_for_ticker(self, ticker):
        """Retourne les données brutes pour les graphiques Plotly."""
        return self.data_store.get(ticker)
