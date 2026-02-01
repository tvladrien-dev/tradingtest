import streamlit as st
import pandas as pd
import time
import logging
import sys
import os
from datetime import datetime

# --- CONFIGURATION DU CHEMIN SYSTÈME ---
# Assure la liaison entre app.py et les dossiers engine/ , ui/ , config/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. INITIALISATION DES RÉPERTOIRES DE TICKERS
all_tickers = []

# 2. CHARGEMENT SÉCURISÉ DES CONFIGURATIONS (Vérification des noms de variables)
try:
    from config import settings
    
    # Chargement PEA Stocks (Extraction des tickers depuis la liste de dictionnaires)
    try:
        from config.pea_stocks import PEA_UNIVERSE
        all_tickers.extend([item['ticker'] for item in PEA_UNIVERSE if 'ticker' in item])
    except (ImportError, AttributeError) as e:
        st.error(f"⚠️ Erreur config/pea_stocks.py : {e}")

    # Chargement Cryptos
    try:
        from config.cryptos import CRYPTO_UNIVERSE
        all_tickers.extend([item['ticker'] for item in CRYPTO_UNIVERSE if 'ticker' in item])
    except (ImportError, AttributeError) as e:
        st.error(f"⚠️ Erreur config/cryptos.py : {e}")

    # Chargement Commodities
    try:
        from config.commodities import COMMODITIES_UNIVERSE
        all_tickers.extend([item['ticker'] for item in COMMODITIES_UNIVERSE if 'ticker' in item])
    except (ImportError, AttributeError) as e:
        st.error(f"⚠️ Erreur config/commodities.py : {e}")

    # Imports des modules logiques
    from engine.trading_bot import TradingBotV1Elite 
    from ui.dashboard import Dashboard
    from ui.components import UIComponents
    
except Exception as e:
    st.error(f"🛑 ERREUR D'INITIALISATION : {e}")
    st.stop()

# Configuration du Logging pour le debug Streamlit
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QuantMaster")

def main():
    # --- SETUP UI ---
    ui_tools = UIComponents()
    ui_tools.set_page_config()
    
    # --- PERSISTENCE DU MOTEUR (SESSION STATE) ---
    if 'bot' not in st.session_state:
        # Nettoyage strict : pas de doublons, pas de valeurs vides
        clean_tickers = list(dict.fromkeys([t for t in all_tickers if t]))
        if not clean_tickers:
            st.error("❌ Aucun ticker n'a été chargé depuis le dossier config/.")
            st.stop()
        
        st.session_state.bot = TradingBotV1Elite(tickers=clean_tickers)
        logger.info(f"Moteur Elite initialisé avec {len(clean_tickers)} actifs.")

    # Instance du Dashboard liée au bot
    dashboard = Dashboard(st.session_state.bot)
    
    # Cache local pour éviter le spam de notifications NTFY
    if 'notified_tickers' not in st.session_state:
        st.session_state.notified_tickers = {}

    # Rendu de la Sidebar (Paramètres utilisateur)
    sidebar_params = dashboard.render_sidebar()
    
    # --- CYCLE D'ANALYSE ET RENDU ---
    try:
        # ÉTAPE 1 : Synchronisation des données Yahoo Finance
        with st.spinner(f"Acquisition des flux ({len(st.session_state.bot.tickers)} actifs)..."):
            # On force la période à 2y pour garantir le calcul de l'EMA200
            st.session_state.bot.sync_market_data(period="2y", interval="1d")
        
        # ÉTAPE 2 : Traitement des Signaux (Calcul Probabilités + Sentiment)
        with st.spinner("Calcul des probabilités Elite..."):
            all_signals = st.session_state.bot.process_signals()
        
        signals_df = pd.DataFrame(all_signals) if all_signals else pd.DataFrame()

        # ÉTAPE 3 : Système d'Alerte (Filtrage de confiance >= 75%)
        if not signals_df.empty:
            for _, signal in signals_df.iterrows():
                ticker = signal['ticker']
                prob = signal.get('probabilite', 0)
                
                if signal['action'] == "ACHAT" and prob >= 75:
                    # Logique anti-doublon par session
                    if ticker not in st.session_state.notified_tickers:
                        if st.session_state.bot.send_notification(signal):
                            st.session_state.notified_tickers[ticker] = signal['prix']
                            st.toast(f"📱 Signal envoyé : {ticker}", icon="📲")

        # --- ÉTAPE 4 : RENDU DASHBOARD (PROTECTION CONTRE KEYERROR 'CLOSE') ---
        # Si un ticker échoue, on l'isole pour ne pas faire crash l'UI
        try:
            dashboard.render_main_view()
        except KeyError as ke:
            if str(ke) == "'Close'":
                st.error("⚠️ Données incomplètes détectées pour certains actifs.")
                st.info("💡 Yahoo Finance n'a pas pu fournir de prix pour certains tickers (Delisted).")
            else:
                st.error(f"🚨 Erreur UI : {ke}")
        
        # ÉTAPE 5 : Footer et Temps de rafraîchissement
        dashboard.render_footer()

        # --- GESTION DE L'AUTO-REFRESH ---
        st.divider()
        timer_placeholder = st.empty()
        
        now = datetime.now()
        is_market_open = (now.weekday() < 5) and (9 <= now.hour < 22) # Plage large Crypto + Stocks

        if is_market_open:
            refresh_sec = 300 # 5 minutes
            for i in range(refresh_sec, 0, -1):
                timer_placeholder.markdown(
                    f"<div style='text-align:center; color:#00FF41; font-family:monospace;'>"
                    f"🕒 PROCHAIN SCAN GLOBAL DANS {i}s"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(1)
            st.rerun()
        else:
            timer_placeholder.info("🌙 Marchés actions fermés. Scan automatique en pause.")
            if st.button("🔄 Lancer un scan manuel"):
                st.rerun()

    except Exception as e:
        logger.error(f"Erreur fatale app.py : {e}", exc_info=True)
        st.error(f"🚨 Erreur Système : {str(e)}")
        if st.button("Réinitialiser le Terminal"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
