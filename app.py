import streamlit as st
import pandas as pd
import time
import logging
import sys
import os
from datetime import datetime

# --- OPTIMISATION DU CHEMIN SYSTÈME ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. IMPORTS DES MODULES PROPRIÉTAIRES (Respect strict de ta structure de dossiers)
try:
    # On importe les réglages généraux
    from config import settings
    
    # On importe les listes spécifiques depuis tes fichiers dédiés dans config/
    from config.pea_stocks import TICKERS_PEA
    from config.cryptos import CRYPTO_LIST
    from config.commodities import COMMODITIES
    
    # Import du moteur Elite et de l'UI
    from engine.trading_bot import TradingBotV1Elite 
    from ui.dashboard import Dashboard
    from ui.components import UIComponents
    
except ImportError as e:
    st.error(f"🛑 ERREUR D'IMPORTATION : {e}")
    st.info("💡 Vérifiez que vos fichiers existent dans config/ (pea_stocks.py, cryptos.py, commodities.py)")
    st.stop()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QuantMaster")

def main():
    # --- INITIALISATION UI ---
    ui_tools = UIComponents()
    ui_tools.set_page_config()
    
    # --- PERSISTENCE DU MOTEUR ÉLITE ---
    if 'bot' not in st.session_state:
        # CONSOLIDATION DE TOUS TES ACTIFS (Fusion des fichiers du dossier config/)
        # On regroupe tes actions PEA, tes cryptos et tes matières premières
        all_tickers = []
        if 'TICKERS_PEA' in globals() or 'TICKERS_PEA' in locals() or locals().get('TICKERS_PEA'):
            all_tickers.extend(TICKERS_PEA)
        if 'CRYPTO_LIST' in globals() or 'CRYPTO_LIST' in locals() or locals().get('CRYPTO_LIST'):
            all_tickers.extend(CRYPTO_LIST)
        if 'COMMODITIES' in globals() or 'COMMODITIES' in locals() or locals().get('COMMODITIES'):
            all_tickers.extend(COMMODITIES)
            
        # Suppression des doublons éventuels
        all_tickers = list(dict.fromkeys(all_tickers))
        
        if not all_tickers:
            st.error("❌ Aucune liste d'actifs trouvée dans config/pea_stocks.py, cryptos.py ou commodities.py")
            st.stop()
            
        # Initialisation du bot avec l'intégralité de tes actifs
        st.session_state.bot = TradingBotV1Elite(tickers=all_tickers)
        logger.info(f"Moteur Elite initialisé avec {len(all_tickers)} actifs variés.")

    # Instance du Dashboard
    dashboard = Dashboard(st.session_state.bot)
    
    # Cache des notifications
    if 'notified_tickers' not in st.session_state:
        st.session_state.notified_tickers = {}

    # --- BARRE LATÉRALE ---
    sidebar_params = dashboard.render_sidebar()
    
    # --- CYCLE DE SCAN ---
    st.toast("Synchronisation globale des flux Alpha Quant...", icon="🚀")
    
    try:
        # ÉTAPE 1 : Synchronisation (Moteur fusionné)
        with st.spinner(f"Acquisition des flux ({len(st.session_state.bot.tickers)} actifs)..."):
            # On utilise l'intervalle "1d" pour la stabilité
            success = st.session_state.bot.sync_market_data(period="2y", interval="1d")
        
        if not success:
            st.error("⚠️ Échec de la récupération des données Yahoo Finance.")
            if st.button("Réessayer"):
                st.rerun()
            st.stop()

        # ÉTAPE 2 : Analyse Quantitative
        with st.spinner("Calcul des probabilités Elite et analyse sentimentale..."):
            all_signals = st.session_state.bot.process_signals()
        
        signals_df = pd.DataFrame(all_signals) if all_signals else pd.DataFrame()

        # ÉTAPE 3 : Notifications NTFY (Seuil >= 75%)
        if not signals_df.empty:
            for _, signal in signals_df.iterrows():
                ticker = signal['ticker']
                prob = signal['probabilite']
                action = signal['action']
                price = signal['prix']

                if action == "ACHAT" and prob >= 75:
                    is_new = ticker not in st.session_state.notified_tickers
                    price_change = False
                    if not is_new:
                        old_p = st.session_state.notified_tickers[ticker]
                        if abs((price / old_p) - 1) > 0.02:
                            price_change = True
                            
                    if is_new or price_change:
                        notif_sent = st.session_state.bot.send_notification(signal)
                        if notif_sent:
                            st.session_state.notified_tickers[ticker] = price
                            st.toast(f"📱 Signal : {ticker}", icon="📲")

        # --- ÉTAPE 4 : RENDU INTERFACE ---
        dashboard.render_main_view()

        # ÉTAPE 5 : Footer et Rafraîchissement
        refresh_delay = 300  # 5 minutes
        dashboard.render_footer()

        # --- AUTO-REFRESH LOGIC ---
        st.divider()
        timer_box = st.empty()
        
        now = datetime.now()
        # On vérifie si on est en semaine pour l'auto-refresh
        if now.weekday() < 5:
            for i in range(refresh_delay, 0, -1):
                timer_box.markdown(
                    f"<div style='text-align:center; color:#00FF41; font-family:monospace; font-size:18px;'>"
                    f"🕒 PROCHAIN SCAN DANS {i}s | MODE: MULTI-FLUX (ACTIONS/CRYPTO/COMMO)"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(1)
            st.rerun()
        else:
            timer_box.info("🌙 Mode Week-end : Les marchés traditionnels sont fermés.")
            if st.button("🔄 Lancer un scan manuel (Crypto)"):
                st.rerun()

    except Exception as e:
        logger.error(f"ERREUR CRITIQUE app.py : {e}", exc_info=True)
        st.error(f"🚨 Erreur Système : {str(e)}")
        if st.button("Réinitialiser le Terminal"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
