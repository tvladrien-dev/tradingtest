import streamlit as st
import time
import requests
from engine.trading_bot import TradingBotPEA
from datetime import datetime

# --- CONFIGURATION TELEGRAM ---
TELEGRAM_TOKEN = "TON_TOKEN_ICI"
TELEGRAM_CHAT_ID = "TON_CHAT_ID_ICI"

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except:
        pass

st.set_page_config(page_title="ALPHA TERMINAL v2", layout="wide")

if 'bot' not in st.session_state:
    st.session_state.bot = TradingBotPEA()
    st.session_state.notified_tickers = {} # Mémoire pour ne pas spammer

bot = st.session_state.bot

st.title("🛰️ Alpha Terminal : Flux Temps Réel")

# Side bar de contrôle
st.sidebar.header("📡 État du Serveur")
refresh_sec = st.sidebar.slider("Fréquence (sec)", 30, 600, 60)
enable_tg = st.sidebar.checkbox("Activer Alertes Telegram", value=False)

# Placeholders
stats_box = st.empty()
buy_zone = st.empty()
radar_zone = st.empty()

# BOUCLE INFINIE
while True:
    try:
        # 1. Fetch & Calcul
        bot.download_data(period="2y")
        bot.generate_elite_signals()
        last_state = bot.get_last_state()
        stats = bot.get_market_thermometer()

        # 2. Gestion des notifications (Uniquement les nouveaux signaux)
        buys = last_state[last_state['Signal'] == 1]
        for _, row in buys.iterrows():
            ticker = row['Ticker']
            # On ne notifie qu'une fois toutes les 6h par action
            if ticker not in st.session_state.notified_tickers or (time.time() - st.session_state.notified_tickers[ticker] > 21600):
                msg = f"🚀 SIGNAL ACHAT ELITE\nAction: {row['Nom']}\nPrix: {row['Close']:.2f}€\nRSI: {row['RSI']:.1f}"
                if enable_tg:
                    send_telegram(msg)
                st.toast(msg)
                st.session_state.notified_tickers[ticker] = time.time()

        # 3. Rendu UI - Thermomètre
        with stats_box.container():
            st.metric("Sentiment de Marché", stats['status'], f"Survente: {stats.get('oversold_pct',0):.1f}%")
        
        # 4. Rendu UI - Signaux
        with buy_zone.container():
            st.subheader("🎯 Signaux d'Achat en cours")
            if not buys.empty:
                cols = st.columns(min(len(buys), 4))
                for i, (_, row) in enumerate(buys.iterrows()):
                    with cols[i % 4]:
                        st.markdown(row['Alpha_HTML'], unsafe_allow_html=True)
            else:
                st.info("Aucun signal d'achat immédiat détecté sur les 250 actifs.")

        # 5. Rendu UI - Radar
        with radar_zone.container():
            st.subheader("🔍 Radar de Proximité (Actions en correction saine)")
            radar_df = last_state[(last_state['RSI'] < 42) & (last_state['Close'] > last_state['EMA200'])]
            radar_df = radar_df.sort_values('RSI').head(8)
            cols = st.columns(4)
            for i, (_, row) in enumerate(radar_df.iterrows()):
                with cols[i % 4]:
                    st.markdown(f"**{row['Nom']}**")
                    st.markdown(row['Alpha_HTML'], unsafe_allow_html=True)

        st.sidebar.success(f"Dernier Scan: {datetime.now().strftime('%H:%M:%S')}")
        time.sleep(refresh_sec)
        st.rerun()

    except Exception as e:
        st.sidebar.error(f"Erreur flux: {e}")
        time.sleep(30)
