import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
from datetime import datetime

# Configuration du logging haute précision
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    QUANT MASTER v12.5.6 - ÉDITION INTÉGRALE
    Système expert de trading avec scoring probabiliste et routage d'alertes.
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        self.ntfy_url = "https://ntfy.sh/votre_topic_unique_2026"
        self.last_sync = None
        self.data_store = {}
        self.last_results = []
        logger.info("Bot Elite initialisé - Moteur prêt.")

    # --- SECTION : ACQUISITION ET CALCULS TECHNIQUES ---

    def sync_market_data(self, period="2y", interval="1d"):
        """Téléchargement massif et enrichissement par indicateurs techniques."""
        if not self.tickers:
            return {}

        logger.info(f"Synchronisation de {len(self.tickers)} actifs...")
        try:
            # Téléchargement multithreadé optimisé pour Streamlit Cloud
            raw_data = yf.download(
                tickers=self.tickers,
                period=period,
                interval=interval,
                group_by='ticker',
                auto_adjust=True,
                threads=True,
                progress=False
            )

            for ticker in self.tickers:
                try:
                    # Extraction sécurisée selon le format de retour (Single vs MultiIndex)
                    if len(self.tickers) == 1:
                        df = raw_data.copy()
                    else:
                        if ticker not in raw_data.columns.levels[0]:
                            continue
                        df = raw_data[ticker].copy()
                    
                    df = df.dropna(subset=['Close'])
                    
                    # Seuil critique de 200 points pour la validité des indicateurs LT
                    if len(df) >= 200:
                        self.data_store[ticker] = self._enrich_indicators(df)
                    else:
                        logger.debug(f"Historique insuffisant pour {ticker}")

                except Exception:
                    continue # Ignore silencieusement les erreurs sur actifs individuels (ex: delisted)

            self.last_sync = datetime.now()
            return self.data_store
        except Exception as e:
            logger.error(f"Échec critique du flux de données : {e}")
            return {}

    def _enrich_indicators(self, df):
        """Calcul de la matrice d'indicateurs Alpha."""
        # Moyennes Mobiles (Trend Structure)
        df['EMA20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
        df['EMA50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Momentum
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # Volatilité et Force
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()
        
        # Convergence/Divergence
        macd = ta.trend.MACD(df['Close'])
        df['MACD_Hist'] = macd.macd_diff()
        
        return df

    # --- SECTION : ANALYSE DE SENTIMENT ET SCORING ---

    def get_news_sentiment(self, ticker):
        """Extraction et analyse sémantique des flux Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            news = getattr(stock, 'news', [])
            if not news:
                return "Neutre ⚪", 0
            
            pos_words = {'hausse', 'profit', 'achat', 'croissance', 'succès', 'dividende', 'positive', 'upgrade'}
            neg_words = {'chute', 'baisse', 'perte', 'alerte', 'déficit', 'litige', 'negative', 'downgrade'}
            
            score = 0
            for n in news[:5]:
                title = n.get('title', '').lower()
                score += sum(1 for w in pos_words if w in title)
                score -= sum(1 for w in neg_words if w in title)
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except:
            return "Indisponible ❓", 0

    def process_signals(self):
        """Moteur de décision probabiliste corrigé pour Pandas 2.x/3.x."""
        results = []
        
        # Acquisition du VIX pour le régime de marché
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
                
                # Extraction des scalaires (Correction FutureWarning)
                price = float(last['Close'].item())
                rsi_val = float(last['RSI'].item())
                adx_val = float(last['ADX'].item())
                ema200 = float(last['EMA200'].item())
                ema50 = float(last['EMA50'].item())
                macd_h = float(last['MACD_Hist'].item())
                prev_macd_h = float(prev['MACD_Hist'].item())
                atr = float(last['ATR'].item())

                # Algorithme de Scoring
                prob = 0
                if price > ema200: prob += 30
                if ema50 > ema200: prob += 20
                if adx_val > 25: prob += 20
                if macd_h > prev_macd_h: prob += 15
                if 40 <= rsi_val <= 65: prob += 10
                if vix_val < 22: prob += 5

                # Risk Management
                sl_dist = atr * 2
                tp_dist = atr * 4
                
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
                    'sl_pct': round((sl_dist / price) * 100, 2),
                    'tp': round(price + tp_dist, 2),
                    'gain_pct': round((tp_dist / price) * 100, 2),
                    'last_update': datetime.now().strftime("%H:%M")
                })
            except Exception:
                continue
        
        self.last_results = results
        return results

    # --- SECTION : NOTIFICATIONS ET UTILITAIRES ---

    def send_notification(self, signal):
        """
        Expédie les alertes vers NTFY.
        Indispensable pour corriger l'AttributeError de app.py.
        """
        if signal['action'] == "VEILLE":
            return False
            
        emoji = "🚀" if signal['action'] == "ACHAT" else "⚠️"
        title = f"{emoji} {signal['action']} : {signal['ticker']} ({signal['probabilite']}%)"
        message = (
            f"💰 Prix : {signal['prix']}€\n"
            f"🛡️ Stop Loss : -{signal['sl_pct']}%\n"
            f"🎯 Objectif : +{signal['gain_pct']}%\n"
            f"📰 Sentiment : {signal['sentiment']}"
        )
        
        try:
            res = requests.post(
                self.ntfy_url,
                data=message.encode('utf-8'),
                headers={
                    "Title": title.encode('utf-8'),
                    "Priority": "high",
                    "Tags": "money,chart_with_upwards_trend"
                },
                timeout=5
            )
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Échec notification {signal['ticker']}: {e}")
            return False

    def get_last_signals(self):
        """Interface pour le Dashboard Streamlit."""
        return self.last_results if self.last_results else self.process_signals()

    def get_data_for_ticker(self, ticker):
        """Récupère le DataFrame complet pour visualisation."""
        return self.data_store.get(ticker)
