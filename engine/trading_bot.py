import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
import logging
from datetime import datetime

# Configuration du logging institutionnel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TradingBotElite")

class TradingBotV1Elite:
    """
    QUANT MASTER v12.5.4 - ELITE EDITION
    Moteur de trading algorithmique haute performance.
    """
    
    def __init__(self, tickers=None):
        self.tickers = tickers if tickers else []
        self.ntfy_url = "https://ntfy.sh/trading_master_2026"
        self.last_sync = None
        self.data_store = {}
        self.last_results = []
        logger.info("Bot Elite prêt pour exécution.")

    # --- SECTION : ACQUISITION ET ENRICHISSEMENT ---

    def sync_market_data(self, period="2y", interval="1d"):
        """Téléchargement groupé et calcul des indicateurs Alpha."""
        if not self.tickers:
            return {}

        logger.info(f"Synchronisation de {len(self.tickers)} actifs...")
        
        try:
            # Téléchargement groupé avec threads pour la performance
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
                    # Gestion dynamique selon le nombre de tickers (format yfinance variable)
                    if len(self.tickers) == 1:
                        df = raw_data.copy()
                    else:
                        if ticker not in raw_data.columns.levels[0]:
                            continue
                        df = raw_data[ticker].copy()
                    
                    # Nettoyage des valeurs manquantes
                    df = df.dropna(subset=['Close'])
                    
                    # Validation : l'EMA200 requiert au moins 200 points
                    if len(df) >= 200:
                        self.data_store[ticker] = self._enrich_indicators(df)
                    
                except Exception:
                    continue # On ignore les erreurs individuelles (tickers invalides)

            self.last_sync = datetime.now()
            return self.data_store

        except Exception as e:
            logger.error(f"Échec critique du flux : {e}")
            return {}

    def _enrich_indicators(self, df):
        """Calcul de la matrice technique complète."""
        # Moyennes Mobiles (Trend)
        df['EMA50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Momentum
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # Force de tendance
        df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()
        
        # Volatilité & Risk
        df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
        
        # MACD (Accélération)
        macd = ta.trend.MACD(df['Close'])
        df['MACD_Hist'] = macd.macd_diff()
        
        return df

    # --- SECTION : BRAIN & SCORING ---

    def get_news_sentiment(self, ticker):
        """Moteur d'analyse sémantique des titres d'actualité."""
        try:
            stock = yf.Ticker(ticker)
            news = getattr(stock, 'news', [])
            if not news:
                return "Neutre ⚪", 0
            
            pos_words = {'hausse', 'profit', 'croissance', 'achat', 'contrat', 'rebond', 'record', 'dividende', 'positive'}
            neg_words = {'chute', 'baisse', 'perte', 'alerte', 'déficit', 'litige', 'inflation', 'krach', 'negative'}
            
            score = 0
            for item in news[:5]:
                title = item.get('title', '').lower()
                score += sum(1 for w in pos_words if w in title)
                score -= sum(1 for w in neg_words if w in title)
            
            label = "Positif ✅" if score > 0 else ("Négatif ⚠️" if score < 0 else "Neutre ⚪")
            return label, score
        except:
            return "Neutre ⚪", 0

    def process_signals(self):
        """Moteur de décision probabiliste avec protection contre les dépréciations Pandas."""
        results = []
        
        # Récupération sécurisée du VIX
        try:
            vix_df = yf.download("^VIX", period="1d", progress=False)
            if not vix_df.empty:
                vix_val = float(vix_df['Close'].iloc[-1].item())
            else:
                vix_val = 22.0
        except:
            vix_val = 22.0

        for ticker, df in self.data_store.items():
            try:
                if len(df) < 2: continue
                
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Extraction des valeurs scalaires via .item()
                close_price = float(last['Close'].item())
                ema200 = float(last['EMA200'].item())
                ema50 = float(last['EMA50'].item())
                rsi = float(last['RSI'].item())
                adx = float(last['ADX'].item())
                macd_h = float(last['MACD_Hist'].item())
                prev_macd_h = float(prev['MACD_Hist'].item())
                atr_val = float(last['ATR'].item())

                # Algorithme de Scoring Alpha
                prob = 0
                if close_price > ema200: prob += 30
                if ema50 > ema200: prob += 20
                if adx > 25: prob += 20
                if macd_h > prev_macd_h: prob += 15
                if 40 <= rsi <= 65: prob += 10
                if vix_val < 22: prob += 5

                # Risk Management
                sl_pct = ( (atr_val * 2) / close_price ) * 100
                tp_price = close_price + (atr_val * 4)
                gain_pct = ( (tp_price / close_price) - 1 ) * 100

                # Classification de l'action
                action = "VEILLE"
                if prob >= 75: action = "ACHAT"
                elif rsi > 80: action = "VENTE"

                sentiment_label, _ = self.get_news_sentiment(ticker)
                
                results.append({
                    'ticker': ticker,
                    'prix': round(close_price, 2),
                    'rsi': round(rsi, 2),
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
        
        self.last_results = results
        return results

    # --- SECTION : UTILITAIRES ---

    def get_last_signals(self):
        """Récupère les résultats mis en cache ou force un calcul."""
        return self.last_results if self.last_results else self.process_signals()

    def get_data_for_ticker(self, ticker):
        """Expose les données historiques pour les graphiques de détail."""
        return self.data_store.get(ticker)
