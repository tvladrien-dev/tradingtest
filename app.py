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
    # TradingBotV1Elite contient maintenant toute la logique Data + Analyse
    from engine.trading_bot import TradingBotV1Elite 
    from ui.dashboard import Dashboard
    from ui.components import UIComponents
except ImportError as e:
    st.error(f"🛑 ERREUR DE STRUCTURE : {e}")
    st.info("💡 Vérifiez que vos fichiers sont bien placés dans les dossiers engine/ et ui/")
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
    
    # --- PERSISTENCE DU MOTEUR ÉLITE ---
    # On initialise le bot une seule fois dans la session
    if 'bot' not in st.session_state:
        # Initialisation avec les tickers définis dans settings
        st.session_state.bot = TradingBotV1Elite(tickers=settings.TICKERS_PEA)
        logger.info("Moteur TradingBotV1Elite initialisé dans la session.")

    # Initialisation du Dashboard avec l'instance du bot
    dashboard = Dashboard(st.session_state.bot)
    
    # Cache pour éviter de notifier plusieurs fois le même signal dans la journée
    if 'notified_tickers' not in st.session_state:
        st.session_state.notified_tickers = {}

    # --- BARRE LATÉRALE ---
    # Récupération des paramètres de l'UI (mode de scan, etc.)
    sidebar_params = dashboard.render_sidebar()
    
    # --- DÉBUT DU CYCLE DE SCAN ---
    st.toast("Actualisation du terminal Alpha Quant...", icon="🚀")
    
    try:
        # ÉTAPE 1 : Synchronisation des données (Moteur fusionné)
        # On utilise la méthode interne du bot qui télécharge et enrichit les indicateurs
        with st.spinner(f"Acquisition des flux pour {len(settings.TICKERS_PEA)} actifs..."):
            # On force la sync en intervalle "1d" pour la stabilité du Swing Trading
            success_sync = st.session_state.bot.sync_market_data(period="2y", interval="1d")
        
        if not success_sync:
            st.error("⚠️ Échec de synchronisation. Limite API Yahoo atteinte ou problème réseau.")
            if st.button("Réessayer"):
                st.rerun()
            st.stop()

        # ÉTAPE 2 : Analyse Quantitative & Signaux
        # Le bot traite tout le data_store interne
        with st.spinner("Analyse algorithmique des vecteurs Alpha..."):
            all_signals = st.session_state.bot.process_signals()
        
        # Conversion en DataFrame pour le traitement UI
        signals_df = pd.DataFrame(all_signals) if all_signals else pd.DataFrame()

        # ÉTAPE 3 : Système de Notification Intelligent
        if not signals_df.empty:
            for _, signal in signals_df.iterrows():
                ticker = signal['ticker']
                prob = signal['probabilite']
                action = signal['action']
                last_price = signal['prix']

                # Logique d'alerte : Seulement si probabilité Elite (>= 75%)
                if action == "ACHAT" and prob >= 75:
                    should_notify = False
                    
                    if ticker not in st.session_state.notified_tickers:
                        should_notify = True
                    else:
                        old_price = st.session_state.notified_tickers[ticker]
                        # On re-notifie si le prix a bougé de 2% depuis la dernière alerte
                        if abs((last_price / old_price) - 1) > 0.02:
                            should_notify = True
                    
                    if should_notify:
                        # Envoi via la méthode ntfy intégrée au bot
                        notif_sent = st.session_state.bot.send_notification(signal)
                        if notif_sent:
                            st.session_state.notified_tickers[ticker] = last_price
                            st.toast(f"📱 Alerte Push : {ticker} ({prob}%)", icon="📲")

        # --- ÉTAPE 4 : RENDU DE L'INTERFACE ---
        # On délègue tout l'affichage au dashboard
        dashboard.render_main_view()

        # ÉTAPE 5 : Gestion du cycle de rafraîchissement
        refresh_delay = 300  # 5 minutes
        dashboard.render_footer()

        # --- LOGIQUE D'AUTO-REFRESH (MATRICE) ---
        st.divider()
        placeholder_timer = st.empty()
        
        # On vérifie si on est en heure de trading (09h00 - 17h30)
        now = datetime.now()
        is_market_open = (now.weekday() < 5) and (9 <= now.hour < 18)

        if is_market_open:
            for i in range(refresh_delay, 0, -1):
                placeholder_timer.markdown(
                    f"<div style='text-align:center; color:#00FF41; font-family:monospace; font-size:18px;'>"
                    f"🕒 PROCHAIN SCAN DANS {i}s | MODE: ÉLITE V1 (1D)"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(1)
            st.rerun()
        else:
            placeholder_timer.warning("🌙 Marché Euronext fermé. Analyse sur cours de clôture.")
            if st.button("🔄 Lancer un scan manuel"):
                st.rerun()

    except Exception as e:
        logger.error(f"CRITICAL SYSTEM ERROR: {e}", exc_info=True)
        st.error(f"🚨 Erreur Système : {str(e)}")
        if st.button("Réinitialiser le Terminal"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
