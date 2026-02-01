import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
import time
import os
from datetime import datetime

# Configuration du cache pour éviter "OperationalError: database is locked"
# On force le cache dans un dossier temporaire accessible en écriture sur Streamlit Cloud
os.environ['YF_CACHE_DIR'] = '/tmp/yfinance'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    QUANT MASTER v12.5.7 - PRODUCTION READY
    Moteur de trading algorithmique avec gestion de flux par lots et notifications.
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        self.ntfy_url = "https://ntfy.sh/votre_topic_unique_2026"
        self.last_sync = None
        self.data_store = {}
        self.last_results = []
        logger.info("Bot Elite initialisé avec moteur de résilience 2026.")

    # --- SECTION : ACQUISITION DE DONNÉES PAR LOTS ---

    def sync_market_data(self, period="2y", interval="1d"):
        """Téléchargement par lots pour contourner le Rate Limit de Yahoo."""
        if not self.tickers:
            return {}

        # Filtrage préventif des tickers identifiés comme HS dans les logs
        blacklisted = [
            'POL-USD', 'COMP-USD', 'GRT-USD', 'MNT-USD', 'ALT-USD', 
            'BOUY.PA', 'EXO.PA', 'FDJ.PA', 'TRIA.PA', 'ALMD.PA'
        ]
        active_tickers = [t for t in self.tickers if t not in blacklisted]

        logger.info(f"Synchronisation de {len(active_tickers)} actifs par lots de 40...")
        
        # Découpage en lots (Chunks) pour éviter d'être banni
        chunk_size = 40
        for i in range(0, len(active_tickers), chunk_size):
            chunk = active_tickers[i:i + chunk_size]
            try:
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
                        # Extraction sécurisée
                        if len(chunk) == 1:
                            df = raw_data.copy()
                        else:
                            if ticker not in raw_data.columns.levels[0]: continue
                            df = raw_data[ticker].copy()
                        
                        df = df.dropna(subset=['Close'])
                        
                        if len(df) >= 200:
                            self.data_store[ticker] = self._enrich_indicators(df)
                    except Exception:
                        continue
                
                # Pause de sécurité pour le Rate Limiting
                time.sleep(1.2)
                
            except Exception as e:
                logger.error(f"Erreur sur le lot commençant par {chunk[0]} : {e}")

        self.last_sync = datetime.now()
        return self.data_store

    def _enrich_indicators(self, df):
        """Calcul complet de la matrice technique Alpha."""
        # Moyennes Mobiles
        df['EMA50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Momentum & Force
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()
        
        # Volatilité
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD_Hist'] = macd.macd_diff()
        
        return df

    # --- SECTION : LOGIQUE DE SCORING ---

    def get_news_sentiment(self, ticker):
        """Scoring sémantique des news pour validation du signal."""
        try:
            stock = yf.Ticker(ticker)
            news = getattr(stock, 'news', [])
            if not news: return "Neutre ⚪", 0
            
            score = 0
            keywords = {
                'pos': ['hausse', 'profit', 'achat', 'croissance', 'positive'],
                'neg': ['chute', 'baisse', 'perte', 'alerte', 'negative']
            }
            
            for item in news[:3]:
                title = item.get('title', '').lower()
                score += sum(1 for w in keywords['pos'] if w in title)
                score -= sum(1 for w in keywords['neg'] if w in title)
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except:
            return "Neutre ⚪", 0

    def process_signals(self):
        """Moteur de décision probabiliste avec protection contre les dépréciations Pandas."""
        results = []
        
        # VIX Fix
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
                
                # Extraction scalaire sécurisée (.item())
                price = float(last['Close'].item())
                prob = 0
                
                if price > float(last['EMA200'].item()): prob += 30
                if float(last['EMA50'].item()) > float(last['EMA200'].item()): prob += 20
                if float(last['ADX'].item()) > 25: prob += 20
                if float(last['MACD_Hist'].item()) > float(prev['MACD_Hist'].item()): prob += 15
                if 40 <= float(last['RSI'].item()) <= 65: prob += 10
                if vix_val < 22: prob += 5

                # Risk Management
                atr = float(last['ATR'].item())
                sl_pct = ( (atr * 2) / price ) * 100
                tp_price = price + (atr * 4)
                gain_pct = ( (atr * 4) / price ) * 100

                action = "VEILLE"
                if prob >= 75: action = "ACHAT"
                elif float(last['RSI'].item()) > 80: action = "VENTE"

                sentiment, _ = self.get_news_sentiment(ticker)
                
                results.append({
                    'ticker': ticker,
                    'prix': round(price, 2),
                    'rsi': round(float(last['RSI'].item()), 2),
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
        
        self.last_results = results
        return results

    # --- SECTION : NOTIFICATIONS (Fix de l'AttributeError) ---

    def send_notification(self, signal):
        """Envoie une alerte vers NTFY pour les signaux d'achat/vente."""
        if signal['action'] == "VEILLE":
            return False
            
        emoji = "🚀" if signal['action'] == "ACHAT" else "📉"
        title = f"{emoji} {signal['action']} : {signal['ticker']}"
        body = (
            f"💰 Prix: {signal['prix']}€\n"
            f"🎯 Confiance: {signal['probabilite']}%\n"
            f"🛡️ SL: -{signal['sl_pct']}% | TP: +{signal['gain_pct']}%"
        )
        
        try:
            res = requests.post(
                self.ntfy_url,
                data=body.encode('utf-8'),
                headers={"Title": title.encode('utf-8'), "Priority": "high"},
                timeout=5
            )
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Notification échouée pour {signal['ticker']} : {e}")
            return False

    def get_last_signals(self):
        """Récupération des signaux pour l'interface UI."""
        return self.last_results if self.last_results else self.process_signals()

    def get_data_for_ticker(self, ticker):
        """Données historiques pour graphiques détaillés."""
        return self.data_store.get(ticker)
