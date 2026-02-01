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
    # On importe uniquement la classe fusionnée TradingBotV1Elite
    from engine.trading_bot import TradingBotV1Elite 
    from ui.dashboard import Dashboard
    from ui.components import UIComponents
except ImportError as e:
    st.error(f"🛑 ERREUR DE STRUCTURE : {e}")
    st.info("💡 Vérifiez que TradingBotV1Elite est bien défini dans engine/trading_bot.py")
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
    
    # --- GESTION DYNAMIQUE DES TICKERS (Correction AttributeError) ---
    if 'bot' not in st.session_state:
        # On récupère toutes les listes possibles de ton fichier config
        # getattr permet d'éviter le crash si une variable est absente
        listes_actifs = [
            getattr(settings, 'TICKERS_PEA', []),
            getattr(settings, 'CRYPTO_LIST', []),
            getattr(settings, 'COMMODITIES', []),
            getattr(settings, 'STOCKS', [])
        ]
        
        # Fusion de toutes les listes en une seule liste plate sans doublons
        all_tickers = list(set([item for sous_liste in listes_actifs for item in sous_liste]))
        
        if not all_tickers:
            st.error("❌ Aucun ticker trouvé dans config.py (Vérifiez TICKERS_PEA, CRYPTO_LIST, etc.)")
            st.stop()
            
        # Initialisation du moteur fusionné avec la liste consolidée
        st.session_state.bot = TradingBotV1Elite(tickers=all_tickers)
        logger.info(f"Moteur Elite initialisé avec {len(all_tickers)} actifs.")

    # Initialisation du Dashboard avec l'instance du bot présente en session
    dashboard = Dashboard(st.session_state.bot)
    
    # Cache pour éviter les notifications répétitives
    if 'notified_tickers' not in st.session_state:
        st.session_state.notified_tickers = {}

    # --- BARRE LATÉRALE ---
    sidebar_params = dashboard.render_sidebar()
    
    # --- DÉBUT DU CYCLE DE SCAN ---
    st.toast("Actualisation du terminal Alpha Quant...", icon="🚀")
    
    try:
        # ÉTAPE 1 : Synchronisation (Moteur fusionné Data + Indicateurs)
        with st.spinner(f"Acquisition des flux ({len(st.session_state.bot.tickers)} actifs)..."):
            # On utilise l'intervalle "1d" pour la stabilité sur Streamlit Cloud
            success_sync = st.session_state.bot.sync_market_data(period="2y", interval="1d")
        
        if not success_sync:
            st.error("⚠️ Échec de synchronisation. Vérifiez votre connexion ou les symboles Yahoo.")
            if st.button("Réessayer"):
                st.rerun()
            st.stop()

        # ÉTAPE 2 : Analyse Quantitative
        with st.spinner("Calcul des probabilités et analyse du sentiment..."):
            all_signals = st.session_state.bot.process_signals()
        
        signals_df = pd.DataFrame(all_signals) if all_signals else pd.DataFrame()

        # ÉTAPE 3 : Système de Notification (Probabilité >= 75%)
        if not signals_df.empty:
            for _, signal in signals_df.iterrows():
                ticker = signal['ticker']
                prob = signal['probabilite']
                action = signal['action']
                last_price = signal['prix']

                if action == "ACHAT" and prob >= 75:
                    should_notify = False
                    if ticker not in st.session_state.notified_tickers:
                        should_notify = True
                    else:
                        old_price = st.session_state.notified_tickers[ticker]
                        if abs((last_price / old_price) - 1) > 0.02: # Seuil 2%
                            should_notify = True
                    
                    if should_notify:
                        notif_sent = st.session_state.bot.send_notification(signal)
                        if notif_sent:
                            st.session_state.notified_tickers[ticker] = last_price
                            st.toast(f"📱 Signal envoyé : {ticker}", icon="📲")

        # --- ÉTAPE 4 : RENDU DE L'INTERFACE ---
        dashboard.render_main_view()

        # ÉTAPE 5 : Footer et Logique de Refresh
        refresh_delay = 300  # 5 minutes
        dashboard.render_footer()

        # --- AUTO-REFRESH (MATRICE) ---
        st.divider()
        placeholder_timer = st.empty()
        
        now = datetime.now()
        # On vérifie si on est en semaine (Lundi-Vendredi) et en heures de bourse
        is_market_open = (now.weekday() < 5) and (9 <= now.hour < 18)

        if is_market_open:
            for i in range(refresh_delay, 0, -1):
                placeholder_timer.markdown(
                    f"<div style='text-align:center; color:#00FF41; font-family:monospace; font-size:18px;'>"
                    f"🕒 PROCHAIN SCAN DANS {i}s | MODE: ÉLITE MULTI-ACTIFS"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(1)
            st.rerun()
        else:
            placeholder_timer.info("🌙 Marché fermé. Prochain scan automatique à l'ouverture.")
            if st.button("🔄 Forcer un scan manuel"):
                st.rerun()

    except Exception as e:
        logger.error(f"Erreur critique app.py : {e}", exc_info=True)
        st.error(f"🚨 Erreur Système : {str(e)}")
        if st.button("Réinitialiser le Terminal"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
