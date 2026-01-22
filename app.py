import streamlit as st
import time
from engine.trading_bot import TradingBotPEA
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(page_title="ALPHA TERMINAL v2.0", layout="wide")

# Injection de CSS pour un look "Terminal Bloomberg"
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ff99; }
    </style>
""", unsafe_allow_html=True)

# Initialisation du bot dans la session
if 'bot' not in st.session_state:
    st.session_state.bot = TradingBotPEA()
    st.session_state.last_alert_time = {}

bot = st.session_state.bot

st.title("🚀 Alpha PEA : Surveillance Temps Réel 2026")

# --- BARRE LATÉRALE ---
st.sidebar.header("Paramètres")
refresh_rate = st.sidebar.slider("Rafraîchissement (sec)", 10, 300, 30)
enable_notifications = st.sidebar.checkbox("Activer Notifications Bureau", True)

# --- CONTENEURS DYNAMIQUES ---
status_bar = st.sidebar.empty()
thermo_col = st.columns(1)[0]
main_container = st.empty()

# --- BOUCLE DE SURVEILLANCE ---
while True:
    try:
        # 1. Mise à jour des données
        with st.spinner('Mise à jour du marché...'):
            bot.download_data(period="2y", interval="1d") # Pour tes indicateurs quotidiens
            bot.generate_elite_signals()
        
        # 2. Gestion des Notifications
        new_alerts = bot.check_new_alerts()
        for alert in new_alerts:
            alert_id = f"{alert['ticker']}_{alert['type']}"
            # On ne notifie qu'une fois toutes les 4 heures pour le même ticker
            if alert_id not in st.session_state.last_alert_time or (time.time() - st.session_state.last_alert_time[alert_id]) > 14400:
                if enable_notifications:
                    # Notification Windows/Mac/Linux
                    os.system(f"msg * 'ALERTE {alert['type']} : {alert['nom']} à {alert['prix']}€'") 
                st.toast(f"🚨 {alert['type']} sur {alert['nom']}", icon="📈")
                st.session_state.last_alert_time[alert_id] = time.time()

        # 3. Affichage du Thermomètre
        stats = bot.get_market_thermometer()
        with thermo_col:
            st.info(f"État Global : **{stats['status']}** | Surchauffe : {stats['overbought_pct']:.1f}% | Capitulation : {stats['oversold_pct']:.1f}%")

        # 4. Affichage du Dashboard
        with main_container.container():
            last_state = bot.get_last_state()
            
            # --- SECTION SIGNAUX ACTIFS ---
            st.subheader("🟢 Signaux d'Achat Elite")
            buys = last_state[last_state['Signal'] == 1]
            if not buys.empty:
                cols = st.columns(len(buys) if len(buys) < 4 else 4)
                for i, (_, row) in enumerate(buys.iterrows()):
                    with cols[i % 4]:
                        st.markdown(row['Alpha_HTML'], unsafe_allow_html=True)
            else:
                st.write("Aucun signal immédiat. Analyse en cours...")

            # --- SECTION RADAR ---
            st.divider()
            st.subheader("🔍 Radar de Proximité (Actions saines en correction)")
            proximity = bot.get_proximity_scan().head(8)
            prox_cols = st.columns(4)
            for i, (_, row) in enumerate(proximity.iterrows()):
                with prox_cols[i % 4]:
                    st.markdown(f"**{row['Nom']}**")
                    st.markdown(row['Alpha_HTML'], unsafe_allow_html=True)

        status_bar.write(f"Dernier Scan : {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        st.error(f"Erreur de mise à jour : {e}")
    
    time.sleep(refresh_rate)
