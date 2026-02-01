import streamlit as st
import pandas as pd
import time
import logging
import sys
import os
from datetime import datetime

# --- CONFIGURATION DU CHEMIN SYSTÈME ---
# Assure la liaison entre app.py et les modules dans engine/, ui/, config/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. INITIALISATION DES RÉPERTOIRES DE TICKERS
all_tickers = []

# 2. CHARGEMENT SÉCURISÉ DES CONFIGURATIONS
try:
    from config import settings
    
    # Chargement PEA Stocks (Extraction des tickers depuis config/pea_stocks.py)
    try:
        from config.pea_stocks import PEA_UNIVERSE
        all_tickers.extend([item['ticker'] for item in PEA_UNIVERSE if 'ticker' in item])
    except (ImportError, AttributeError, NameError) as e:
        st.error(f"⚠️ Erreur de chargement dans config/pea_stocks.py : {e}")

    # Chargement Cryptos (Extraction depuis config/cryptos.py)
    try:
        from config.cryptos import CRYPTO_UNIVERSE
        all_tickers.extend([item['ticker'] for item in CRYPTO_UNIVERSE if 'ticker' in item])
    except (ImportError, AttributeError, NameError) as e:
        st.error(f"⚠️ Erreur de chargement dans config/cryptos.py : {e}")

    # Chargement Commodities (Extraction depuis config/commodities.py)
    try:
        from config.commodities import COMMODITIES_UNIVERSE
        all_tickers.extend([item['ticker'] for item in COMMODITIES_UNIVERSE if 'ticker' in item])
    except (ImportError, AttributeError, NameError) as e:
        st.error(f"⚠️ Erreur de chargement dans config/commodities.py : {e}")

    # Importation du Moteur et des Composants UI
    from engine.trading_bot import TradingBotV1Elite 
    from ui.dashboard import Dashboard
    from ui.components import UIComponents
    
except Exception as e:
    st.error(f"🛑 ERREUR CRITIQUE D'IMPORTATION : {e}")
    st.info("Vérifiez que vos fichiers config/ contiennent bien PEA_UNIVERSE, CRYPTO_UNIVERSE ou COMMODITIES_UNIVERSE.")
    st.stop()

# Configuration du Logging Professionnel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QuantMaster_Core")

def main():
    # --- INITIALISATION DE L'INTERFACE ---
    ui_tools = UIComponents()
    ui_tools.set_page_config()
    
    # --- PERSISTENCE DU MOTEUR (SESSION STATE) ---
    if 'bot' not in st.session_state:
        # Nettoyage strict : suppression des doublons et des entrées vides
        clean_tickers = list(dict.fromkeys([t for t in all_tickers if t]))
        
        if not clean_tickers:
            st.error("❌ La liste consolidée des actifs est vide. Vérifiez vos fichiers dans config/.")
            st.stop()
            
        # Initialisation de l'instance du Bot Elite
        st.session_state.bot = TradingBotV1Elite(tickers=clean_tickers)
        logger.info(f"Bot initialisé avec {len(clean_tickers)} actifs consolidés.")

    # Liaison du Dashboard avec l'instance active
    dashboard = Dashboard(st.session_state.bot)
    
    # Gestionnaire de mémoire des notifications
    if 'notified_tickers' not in st.session_state:
        st.session_state.notified_tickers = {}

    # --- AFFICHAGE DE LA BARRE LATÉRALE ---
    sidebar_params = dashboard.render_sidebar()
    
    # --- DÉBUT DU CYCLE D'ANALYSE ---
    st.toast("Synchronisation des flux Quant...", icon="🚀")
    
    try:
        # ÉTAPE 1 : Synchronisation des données du marché
        with st.spinner(f"Acquisition des flux ({len(st.session_state.bot.tickers)} actifs)..."):
            # On utilise 2y / 1d pour garantir le calcul des indicateurs de tendance (EMA200)
            st.session_state.bot.sync_market_data(period="2y", interval="1d")
        
        # ÉTAPE 2 : Analyse Quantitative via le moteur Elite
        with st.spinner("Traitement des probabilités et analyse sentimentale..."):
            all_signals = st.session_state.bot.process_signals()
        
        signals_df = pd.DataFrame(all_signals) if all_signals else pd.DataFrame()

        # ÉTAPE 3 : Système de Notifications (Seuil Elite >= 75%)
        if not signals_df.empty:
            for _, signal in signals_df.iterrows():
                ticker = signal['ticker']
                prob = signal.get('probabilite', 0)
                
                if signal['action'] == "ACHAT" and prob >= 75:
                    # Vérification si alerte déjà envoyée
                    if ticker not in st.session_state.notified_tickers:
                        if st.session_state.bot.send_notification(signal):
                            st.session_state.notified_tickers[ticker] = signal['prix']
                            st.toast(f"📱 Signal Alpha : {ticker}", icon="📲")

        # --- ÉTAPE 4 : RENDU DE LA VUE PRINCIPALE (SÉCURISÉE) ---
        # Le bloc try/except ici protège contre les KeyError: 'Close' du Dashboard
        try:
            dashboard.render_main_view()
        except KeyError as ke:
            if "'Close'" in str(ke):
                st.error("⚠️ Données Yahoo incomplètes sur certains actifs.")
                st.info("Certains tickers délistés ou sans historique bloquent l'affichage. Nettoyage auto...")
            else:
                logger.error(f"Erreur UI : {ke}")
                st.error(f"Erreur d'affichage : {ke}")

        # ÉTAPE 5 : Pied de page
        dashboard.render_footer()

        # --- LOGIQUE DE RAFRAÎCHISSEMENT AUTOMATIQUE ---
        st.divider()
        timer_placeholder = st.empty()
        
        maintenant = datetime.now()
        # Le rafraîchissement est plus rapide pendant les heures de trading (Lun-Ven)
        if maintenant.weekday() < 5:
            for i in range(300, 0, -1):
                timer_placeholder.markdown(
                    f"<div style='text-align:center; color:#00FF41; font-family:monospace; font-size:16px;'>"
                    f"🕒 PROCHAIN SCAN GLOBAL DANS {i}s | MODE: MULTI-FLUX"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(1)
            st.rerun()
        else:
            timer_placeholder.info("🌙 Mode Week-end : Marchés actions fermés. Auto-refresh suspendu.")
            if st.button("🔄 Lancer un scan manuel (Crypto/Commo)"):
                st.rerun()

    except Exception as e:
        logger.error(f"Erreur fatale app.py : {str(e)}", exc_info=True)
        st.error(f"🚨 Erreur Système : {str(e)}")
        if st.button("Réinitialiser le Terminal"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
