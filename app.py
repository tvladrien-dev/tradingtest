import streamlit as st
import pandas as pd
import time
import logging
import sys
import os
from datetime import datetime

# --- OPTIMISATION DU PATH SYSTEME ---
# S'assure que Streamlit Cloud voit les dossiers locaux même sans __init__.py complexes
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
    st.error(f"❌ ERREUR DE STRUCTURE : {e}")
    st.info("Assurez-vous que les dossiers 'engine', 'ui' et 'config' contiennent bien leurs fichiers respectifs.")
    st.stop()

# Configuration du logging professionnel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("QuantMaster")

def main():
    # --- INITIALISATION DE L'INTERFACE ---
    ui_tools = UIComponents()
    ui_tools.set_page_config() # Configuration thème sombre et layout large
    
    dashboard = Dashboard(settings)
    
    # --- PERSISTENCE DES MOTEURS (SESSION STATE) ---
    # On utilise le cache de session pour éviter de recharger les moteurs à chaque interaction
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = DataLoader()
    if 'bot' not in st.session_state:
        st.session_state.bot = TradingBotPEA()
    if 'regime_filter' not in st.session_state:
        st.session_state.regime_filter = MarketRegimeFilter()
    if 'news_engine' not in st.session_state:
        st.session_state.news_engine = NewsEngine()

    # --- BARRE LATÉRALE (SIDEBAR) ---
    # Récupère les filtres utilisateur (Recherche, Mode de scan)
    sidebar_params = dashboard.render_sidebar()
    
    # --- CYCLE DE TRADING ---
    st.toast("Synchronisation avec Euronext Paris en cours...", icon="🔄")
    
    try:
        # ÉTAPE 1 : Analyse du Régime de Marché (Macro Filter)
        with st.spinner("Analyse du contexte macro-économique..."):
            market_status = st.session_state.regime_filter.get_market_status()
        
        # ÉTAPE 2 : Acquisition massive des données
        # On utilise les tickers définis dans config/settings.py
        with st.spinner(f"Acquisition des flux pour {len(settings.TICKERS_PEA)} actifs..."):
            raw_data = st.session_state.data_loader.download_market_data(settings.TICKERS_PEA)
        
        if not raw_data:
            st.error("⚠️ Flux de données interrompu. Tentative de reconnexion au prochain cycle.")
            time.sleep(10)
            st.rerun()

        # ÉTAPE 3 : Traitement Quantitatif (Signaux Alpha)
        all_signals = []
        progress_bar = st.progress(0)
        
        for i, (ticker, df) in enumerate(raw_data.items()):
            # Analyse technique profonde pour chaque actif
            signal_data = st.session_state.bot.analyze(ticker, df)
            if signal_data:
                # On enrichit le signal avec le multiplicateur de risque macro
                signal_data['Risk_Adj_Size'] = market_status['multiplier']
                all_signals.append(signal_data)
            
            # Mise à jour de la barre de progression
            progress_bar.progress((i + 1) / len(raw_data))
        
        # Nettoyage de la barre de progression après le scan
        progress_bar.empty()
        
        # Conversion en DataFrame pour manipulation facile
        signals_df = pd.DataFrame(all_signals)

        # ÉTAPE 4 : Rendu du Dashboard Principal
        # On injecte les données traitées dans la vue
        dashboard.render_main_view(
            market_status=market_status,
            signals_df=signals_df,
            news_engine=st.session_state.news_engine
        )

        # ÉTAPE 5 : Calcul du prochain cycle de rafraîchissement
        # Si la volatilité est haute (>22%), on scanne plus vite
        refresh_delay = (
            settings.REFRESH_RATES["HIGH_VOLATILITY"] 
            if market_status['volatility'] > 22 
            else settings.REFRESH_RATES["LOW_VOLATILITY"]
        )

        dashboard.render_footer()

        # --- GESTION DU TEMPS RÉEL (AUTO-REFRESH) ---
        st.divider()
        placeholder_timer = st.empty()
        
        # Vérification si la bourse est ouverte avant de lancer le décompte
        is_open = st.session_state.data_loader.check_market_hours()
        
        if is_open:
            for i in range(refresh_delay, 0, -1):
                placeholder_timer.markdown(
                    f"<div style='text-align: center; color: #00FF41;'>"
                    f"⌛ PROCHAIN SCAN AUTOMATIQUE DANS {i} SECONDES"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(1)
            st.rerun()
        else:
            placeholder_timer.warning(
                "🌙 LE MARCHÉ EST ACTUELLEMENT FERMÉ. "
                "Le scan automatique est en veille jusqu'à demain 09:00."
            )
            if st.button("📊 Forcer un scan (Données de clôture)"):
                st.rerun()

    except Exception as e:
        logger.error(f"Erreur fatale de l'application : {e}", exc_info=True)
        st.error("### 🛑 Une erreur critique est survenue.")
        st.exception(e)
        if st.button("Redémarrer le moteur"):
            st.rerun()

if __name__ == "__main__":
    main()
