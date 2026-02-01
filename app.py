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
    # Importation du moteur Elite corrigé
    from engine.trading_bot import TradingBotV1Elite 
    from engine.regime import MarketRegimeFilter
    from engine.news import NewsEngine
    from ui.dashboard import Dashboard
    from ui.components import UIComponents
except ImportError as e:
    st.error(f"🛑 ERREUR DE STRUCTURE : {e}")
    st.info("💡 Vérifiez que la classe dans engine/trading_bot.py se nomme bien TradingBotV1Elite")
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
        # Initialisation du nouveau moteur V1 Elite avec les tickers du PEA
        st.session_state.bot = TradingBotV1Elite(settings.TICKERS_PEA)
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
        # Correction : On s'assure que le filtre de régime n'utilise pas de 5m
        with st.spinner("Analyse du sentiment de marché (VIX & CAC40)..."):
            market_status = st.session_state.regime_filter.get_market_status()
        
        # ÉTAPE 2 : Acquisition des flux boursiers
        # MODIFICATION CRITIQUE : On passe de "5m" à "1d" pour éviter le bug 
        # "requested range must be within the last 60 days" que tu as dans tes logs.
        with st.spinner(f"Synchronisation de {len(settings.TICKERS_PEA)} actifs..."):
            raw_data = st.session_state.data_loader.download_market_data(
                settings.TICKERS_PEA, 
                interval="1d"  # Changement effectué ici pour la stabilité
            )
        
        if not raw_data:
            st.error("⚠️ Impossible de joindre les serveurs de données (Rate Limit). Re-tentative dans 30s...")
            time.sleep(30)
            st.rerun()

        # ÉTAPE 3 : Analyse Quantitative & Signaux
        all_signals = []
        progress_bar = st.progress(0)
        
        # On itère sur les tickers pour calculer les probabilités et la stratégie V1
        for i, (ticker, df) in enumerate(raw_data.items()):
            # Analyse profonde via le moteur V1 Elite (ADX, RSI, EMA, Sentiment)
            signal_data = st.session_state.bot.process_ticker(ticker)
            
            if signal_data:
                # Injection de la direction macro calculée par le RegimeFilter
                signal_data['Market_Trend'] = market_status['status']
                all_signals.append(signal_data)
                
                # --- SYSTÈME DE NOTIFICATION NTFY (ACHATS PRIORITAIRES) ---
                if signal_data.get('action') == "ACHAT":
                    last_price = signal_data.get('prix')
                    prob = signal_data.get('probabilite')
                    
                    # On ne notifie que si Probabilité > 75% (Elite) et nouveau signal
                    should_notify = False
                    if ticker not in st.session_state.notified_tickers:
                        if prob >= 75: should_notify = True
                    else:
                        old_price = st.session_state.notified_tickers[ticker]
                        # Alerte si le prix varie de plus de 2% depuis la dernière notification
                        if abs((last_price / old_price) - 1) > 0.02:
                            should_notify = True
                    
                    if should_notify:
                        # Envoi via la méthode intégrée au bot (utilise ntfy)
                        success = st.session_state.bot.send_notification(signal_data)
                        if success:
                            st.session_state.notified_tickers[ticker] = last_price
                            st.toast(f"📱 Alerte Push envoyée : {ticker} ({prob}%)", icon="📲")

            progress_bar.progress((i + 1) / len(raw_data))
        
        progress_bar.empty()
        
        # --- ÉTAPE 4 : TRIAGE ET RENDU ---
        signals_df = pd.DataFrame(all_signals)
        
        if not signals_df.empty:
            # Tri : ACHAT en premier, puis par score de Probabilité décroissant
            signals_df['sort_order'] = signals_df['action'].apply(
                lambda x: 0 if x == "ACHAT" else (1 if x == "VENTE" else 2)
            )
            signals_df = signals_df.sort_values(by=['sort_order', 'probabilite'], ascending=[True, False])
            
            # Génération du graphique sectoriel avant le rendu final
            st.session_state.bot.plot_sectors(all_signals)

        # Rendu de l'Interface Dashboard via le module ui/
        dashboard.render_main_view(
            market_status=market_status,
            signals_df=signals_df,
            news_engine=st.session_state.news_engine
        )

        # ÉTAPE 5 : Gestion du cycle de rafraîchissement
        # On définit 300s (5 min) comme intervalle de repos
        refresh_delay = 300 

        dashboard.render_footer()

        # --- AUTO-REFRESH LOGIC ---
        st.divider()
        placeholder_timer = st.empty()
        
        # Vérification des heures d'ouverture (09:00 - 17:30 pour Euronext) via le DataLoader
        if st.session_state.data_loader.check_market_hours():
            for i in range(refresh_delay, 0, -1):
                placeholder_timer.markdown(
                    f"<div style='text-align:center; color:#00FF41; font-family:monospace; font-size:20px;'>"
                    f"🕒 PROCHAIN SCAN DANS {i}s | MODE: SWING DAILY OPTIMISÉ"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(1)
            st.rerun()
        else:
            placeholder_timer.warning("🌙 Marché Euronext fermé. Mode analyse de clôture activé.")
            if st.button("🔄 Lancer un scan manuel de nuit"):
                st.rerun()

    except Exception as e:
        logger.error(f"CRITICAL SYSTEM ERROR: {e}", exc_info=True)
        st.error(f"🚨 Erreur Système : {str(e)}")
        if st.button("Réinitialiser le Terminal"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
