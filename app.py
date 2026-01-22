import streamlit as st
import pandas as pd
import time
import logging
from datetime import datetime

# 1. Imports des modules propriétaires
from config import settings
from engine.data_loader import DataLoader
from engine.trading_bot import TradingBotPEA
from engine.regime import MarketRegimeFilter
from engine.news import NewsEngine
from ui.dashboard import Dashboard
from ui.components import UIComponents

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # --- INITIALISATION UI ---
    ui_tools = UIComponents()
    ui_tools.set_page_config()
    
    dashboard = Dashboard(settings)
    
    # --- INITIALISATION MOTEURS (CACHÉS DANS LA SESSION) ---
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = DataLoader()
    if 'bot' not in st.session_state:
        st.session_state.bot = TradingBotPEA()
    if 'regime_filter' not in st.session_state:
        st.session_state.regime_filter = MarketRegimeFilter()
    if 'news_engine' not in st.session_state:
        st.session_state.news_engine = NewsEngine()

    # --- BARRE LATÉRALE & FILTRES ---
    sidebar_params = dashboard.render_sidebar()
    
    # --- LOGIQUE DE SCAN ---
    st.toast("Initialisation du scan Euronext...", icon="🚀")
    
    try:
        # 1. Analyse du Régime de Marché (Macro)
        with st.spinner("Analyse du contexte macro (CAC40)..."):
            market_status = st.session_state.regime_filter.get_market_status()
        
        # 2. Acquisition des Données (Flux yFinance)
        with st.spinner(f"Téléchargement de {len(settings.TICKERS_PEA)} actifs..."):
            raw_data = st.session_state.data_loader.download_market_data(settings.TICKERS_PEA)
        
        if not raw_data:
            st.error("Impossible de récupérer les données boursières. Vérifiez votre connexion.")
            return

        # 3. Génération des Signaux (Quant Engine)
        all_signals = []
        for ticker, df in raw_data.items():
            # Le bot analyse chaque dataframe pour trouver des opportunités
            signal_data = st.session_state.bot.analyze(ticker, df)
            if signal_data:
                all_signals.append(signal_data)
        
        signals_df = pd.DataFrame(all_signals)

        # 4. Rendu de l'Interface Principale
        dashboard.render_main_view(
            market_status=market_status,
            signals_df=signals_df,
            news_engine=st.session_state.news_engine
        )

        # 5. Gestion de la boucle de rafraîchissement
        refresh_time = (
            settings.REFRESH_RATES["HIGH_VOLATILITY"] 
            if market_status['volatility'] > 22 
            else settings.REFRESH_RATES["LOW_VOLATILITY"]
        )

        dashboard.render_footer()

        # --- SYSTÈME DE COMPTE À REBOURS ---
        st.divider()
        placeholder_timer = st.empty()
        
        if st.session_state.data_loader.check_market_hours():
            for i in range(refresh_time, 0, -1):
                placeholder_timer.caption(f"🕒 Prochain scan automatique dans {i} secondes (Mode: {sidebar_params['mode']})")
                time.sleep(1)
            st.rerun()
        else:
            st.info("🌙 Marché fermé. Le scan automatique reprendra à l'ouverture d'Euronext (09:00).")
            if st.button("🔄 Forcer un rafraîchissement manuel"):
                st.rerun()

    except Exception as e:
        st.error(f"Erreur critique lors de l'exécution : {str(e)}")
        logging.error(f"CRITICAL ERROR: {e}", exc_info=True)

if __name__ == "__main__":
    main()
