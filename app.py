import streamlit as st
import pandas as pd
import time
import logging
import sys
import os
from datetime import datetime

# --- CONFIGURATION DU CHEMIN SYSTÈME ---
# Garantit que les modules dans les sous-dossiers sont importables
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. INITIALISATION DES VARIABLES GLOBALES DE TICKERS
all_tickers = []

# 2. IMPORTS SÉCURISÉS DES CONFIGURATIONS ET DU MOTEUR
try:
    # Réglages généraux
    from config import settings
    
    # Importation et extraction depuis config/pea_stocks.py
    try:
        from config.pea_stocks import PEA_UNIVERSE
        all_tickers.extend([item['ticker'] for item in PEA_UNIVERSE])
    except (ImportError, KeyError, AttributeError) as e:
        st.error(f"❌ Erreur dans config/pea_stocks.py: {e}")

    # Importation et extraction depuis config/cryptos.py
    try:
        from config.cryptos import CRYPTO_UNIVERSE
        all_tickers.extend([item['ticker'] for item in CRYPTO_UNIVERSE])
    except (ImportError, KeyError, AttributeError) as e:
        st.error(f"❌ Erreur dans config/cryptos.py: {e}")

    # Importation et extraction depuis config/commodities.py
    try:
        from config.commodities import COMMODITIES_UNIVERSE
        all_tickers.extend([item['ticker'] for item in COMMODITIES_UNIVERSE])
    except (ImportError, KeyError, AttributeError) as e:
        st.error(f"❌ Erreur dans config/commodities.py: {e}")

    # Importation des classes métier (engine/ et ui/)
    from engine.trading_bot import TradingBotV1Elite 
    from ui.dashboard import Dashboard
    from ui.components import UIComponents
    
except Exception as e:
    st.error(f"🛑 ERREUR DE STRUCTURE CRITIQUE : {e}")
    st.stop()

# Configuration du logging professionnel
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QuantMaster_App")

def main():
    # --- INITIALISATION DE L'INTERFACE ---
    ui_tools = UIComponents()
    ui_tools.set_page_config()
    
    # --- INSTANCIATION DU MOTEUR ÉLITE (SINGLETON VIA SESSION STATE) ---
    if 'bot' not in st.session_state:
        # Nettoyage de la liste (suppression des doublons et valeurs nulles)
        clean_tickers = list(dict.fromkeys([t for t in all_tickers if t]))
        
        if not clean_tickers:
            st.error("❌ La liste consolidée des tickers est vide. Vérifiez vos fichiers de config.")
            st.stop()
            
        # Création de l'instance du bot
        st.session_state.bot = TradingBotV1Elite(tickers=clean_tickers)
        logger.info(f"Bot initialisé avec {len(clean_tickers)} tickers consolidés.")

    # Liaison du Dashboard avec l'instance du bot
    dashboard = Dashboard(st.session_state.bot)
    
    # Gestionnaire de mémoire des notifications pour éviter les doublons
    if 'notified_tickers' not in st.session_state:
        st.session_state.notified_tickers = {}

    # --- AFFICHAGE DE LA SIDEBAR ---
    # Permet de récupérer les paramètres de filtrage utilisateur
    sidebar_params = dashboard.render_sidebar()
    
    # --- DÉBUT DU CYCLE D'ANALYSE ---
    st.toast("Mise à jour des flux de marché...", icon="🚀")
    
    try:
        # ÉTAPE 1 : Synchronisation des données Yahoo Finance
        with st.spinner(f"Acquisition en cours ({len(st.session_state.bot.tickers)} actifs)..."):
            # On utilise l'intervalle "1d" (Daily) pour l'analyse Swing
            success = st.session_state.bot.sync_market_data(period="2y", interval="1d")
        
        if not success:
            st.error("⚠️ Problème de connexion aux serveurs de données (Yahoo Finance).")
            st.stop()

        # ÉTAPE 2 : Traitement des Signaux via le moteur Elite
        with st.spinner("Calcul des indicateurs et probabilités..."):
            all_signals = st.session_state.bot.process_signals()
        
        # Conversion des signaux en DataFrame pour le traitement
        signals_df = pd.DataFrame(all_signals) if all_signals else pd.DataFrame()

        # ÉTAPE 3 : Logique de Notification Automatique (NTFY)
        if not signals_df.empty:
            # On filtre les signaux d'achat avec une probabilité >= 75%
            high_prob_signals = signals_df[
                (signals_df['action'] == "ACHAT") & 
                (signals_df['probabilite'] >= 75)
            ]
            
            for _, signal in high_prob_signals.iterrows():
                ticker = signal['ticker']
                current_price = signal['prix']
                
                # Vérification si une notification a déjà été envoyée pour ce ticker
                is_new_alert = ticker not in st.session_state.notified_tickers
                
                # Si déjà notifié, on ne renvoie que si le prix a bougé de plus de 2%
                price_moved_significantly = False
                if not is_new_alert:
                    last_notified_price = st.session_state.notified_tickers[ticker]
                    if abs((current_price / last_notified_price) - 1) > 0.02:
                        price_moved_significantly = True
                
                if is_new_alert or price_moved_significantly:
                    # Envoi via le canal configuré dans le bot
                    if st.session_state.bot.send_notification(signal):
                        st.session_state.notified_tickers[ticker] = current_price
                        st.toast(f"📱 Alerte envoyée pour {ticker}", icon="📲")

        # --- ÉTAPE 4 : AFFICHAGE DE LA VUE PRINCIPALE ---
        # dashboard.render_main_view() centralise l'affichage des graphiques et tableaux
        dashboard.render_main_view()

        # ÉTAPE 5 : Pied de page et informations système
        dashboard.render_footer()

        # --- LOGIQUE DE RAFRAÎCHISSEMENT AUTOMATIQUE ---
        st.divider()
        refresh_placeholder = st.empty()
        
        # On définit le comportement selon l'heure (Marché ouvert/fermé)
        maintenant = datetime.now()
        is_weekday = maintenant.weekday() < 5
        
        if is_weekday:
            # Cycle de 300 secondes (5 minutes)
            for i in range(300, 0, -1):
                refresh_placeholder.markdown(
                    f"<div style='text-align:center; color:#00FF41; font-family:monospace; font-size:16px;'>"
                    f"🕒 PROCHAIN SCAN GLOBAL DANS {i}s"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(1)
            st.rerun()
        else:
            refresh_placeholder.info("🌙 Mode Week-end : Rafraîchissement automatique suspendu pour les actions.")
            if st.button("🔄 Forcer un scan manuel (Cryptos)"):
                st.rerun()

    except Exception as e:
        logger.error(f"Erreur d'exécution app.py : {str(e)}", exc_info=True)
        st.error(f"🚨 Erreur Système : {str(e)}")
        if st.button("Réinitialiser le Terminal"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
