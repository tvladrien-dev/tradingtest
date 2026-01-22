import streamlit as st
import pandas as pd
import time
import logging
import sys
import os
from datetime import datetime

# --- OPTIMISATION DU CHEMIN SYSTÈME ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. IMPORTS DES MODULES PROPRIÉTAIRES
try:
    from config import settings
    from engine.data_loader import DataLoader
    from engine.trading_bot import TradingBotPEA
    from engine.regime import MarketRegimeFilter
    from engine.news import NewsEngine
    from ui.dashboard import Dashboard
    from ui.components import UIComponents
except ImportError as e:
    st.error(f"🛑 ERREUR DE STRUCTURE : {e}")
    st.stop()

# Configuration du logging professionnel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QuantMaster")

def main():
    # --- INITIALISATION UI & THÈME ---
    ui_tools = UIComponents()
    ui_tools.set_page_config()
    dashboard = Dashboard(settings)
    
    # --- PERSISTENCE DES MOTEURS & ÉTAT DE SESSION ---
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = DataLoader()
    if 'bot' not in st.session_state:
        st.session_state.bot = TradingBotPEA()
    if 'regime_filter' not in st.session_state:
        st.session_state.regime_filter = MarketRegimeFilter()
    if 'news_engine' not in st.session_state:
        st.session_state.news_engine = NewsEngine()
    
    # Cache pour éviter de notifier plusieurs fois le même signal dans la journée
    if 'notified_tickers' not in st.session_state:
        st.session_state.notified_tickers = {}

    # --- BARRE LATÉRALE ---
    sidebar_params = dashboard.render_sidebar()
    
    # --- DÉBUT DU CYCLE DE SCAN ---
    st.toast("Initialisation du terminal Alpha Quant...", icon="🚀")
    
    try:
        # ÉTAPE 1 : Analyse Macro (Régime de Marché)
        with st.spinner("Analyse du sentiment de marché (CAC40)..."):
            market_status = st.session_state.regime_filter.get_market_status()
        
        # ÉTAPE 2 : Acquisition des flux boursiers
        with st.spinner(f"Synchronisation de {len(settings.TICKERS_PEA)} actifs..."):
            raw_data = st.session_state.data_loader.download_market_data(settings.TICKERS_PEA)
        
        if not raw_data:
            st.error("⚠️ Impossible de joindre les serveurs de données. Re-tentative automatique...")
            time.sleep(10)
            st.rerun()

        # ÉTAPE 3 : Analyse Quantitative & Signaux
        all_signals = []
        progress_bar = st.progress(0)
        
        for i, (ticker, df) in enumerate(raw_data.items()):
            # Analyse profonde via le moteur de trading
            signal_data = st.session_state.bot.analyze(ticker, df)
            
            if signal_data:
                # Injection de la direction macro dans le signal
                signal_data['Market_Trend'] = market_status['status']
                all_signals.append(signal_data)
                
                # --- SYSTÈME DE NOTIFICATION NTFY ---
                if signal_data.get('Signal') == 1:
                    last_price = signal_data.get('Close')
                    
                    # On ne notifie que si c'est un nouveau signal ou si le prix a bougé de 2%
                    should_notify = False
                    if ticker not in st.session_state.notified_tickers:
                        should_notify = True
                    else:
                        old_price = st.session_state.notified_tickers[ticker]
                        if abs((last_price / old_price) - 1) > 0.02:
                            should_notify = True
                    
                    if should_notify:
                        success = st.session_state.news_engine.send_ntfy_alert(
                            signal_data=signal_data,
                            topic=settings.NOTIFICATIONS.get("NTFY_TOPIC")
                        )
                        if success:
                            st.session_state.notified_tickers[ticker] = last_price
                            st.toast(f"📱 Alerte Push envoyée pour {ticker}", icon="📲")

            progress_bar.progress((i + 1) / len(raw_data))
        
        progress_bar.empty()
        signals_df = pd.DataFrame(all_signals)

        # ÉTAPE 4 : Rendu de l'Interface Dashboard
        dashboard.render_main_view(
            market_status=market_status,
            signals_df=signals_df,
            news_engine=st.session_state.news_engine
        )

        # ÉTAPE 5 : Gestion du cycle de rafraîchissement
        refresh_delay = (
            settings.REFRESH_RATES["HIGH_VOLATILITY"] 
            if market_status['volatility'] > 22 
            else settings.REFRESH_RATES["LOW_VOLATILITY"]
        )

        dashboard.render_footer()

        # --- AUTO-REFRESH LOGIC ---
        st.divider()
        placeholder_timer = st.empty()
        
        if st.session_state.data_loader.check_market_hours():
            for i in range(refresh_delay, 0, -1):
                placeholder_timer.markdown(
                    f"<div style='text-align:center; color:#00FF41; font-family:monospace;'>"
                    f"🕒 PROCHAIN SCAN DANS {i}s (MODE: {sidebar_params['mode'].upper()})"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(1)
            st.rerun()
        else:
            placeholder_timer.info("🌙 Marché fermé. Scan automatique en pause (Ouverture 09:00).")
            if st.button("🔄 Lancer un scan manuel (Données différées)"):
                st.rerun()

    except Exception as e:
        logger.error(f"CRITICAL SYSTEM ERROR: {e}", exc_info=True)
        st.error(f"🚨 Erreur Système : {str(e)}")
        if st.button("Réinitialiser le Terminal"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
