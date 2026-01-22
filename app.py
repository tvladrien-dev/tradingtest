import streamlit as st
import time
from engine.trading_bot import TradingBotPEA
from datetime import datetime

st.set_page_config(page_title="ALPHA TERMINAL", layout="wide")

# Initialisation persistante du bot
if 'bot' not in st.session_state:
    st.session_state.bot = TradingBotPEA()
    st.session_state.run = True

bot = st.session_state.bot

st.title("🚀 Alpha PEA - Surveillance Elite 2026")

# Zone d'affichage
thermo_placeholder = st.empty()
signals_placeholder = st.empty()
radar_placeholder = st.empty()

while st.session_state.run:
    try:
        # Analyse
        bot.download_data()
        bot.generate_elite_signals()
        last_state = bot.get_last_state()
        stats = bot.get_market_thermometer()

        # Thermomètre
        with thermo_placeholder.container():
            st.metric("Marché", stats['status'], f"Survente: {stats.get('oversold_pct',0):.1f}%")
            st.divider()

        # Signaux d'achat
        with signals_placeholder.container():
            st.subheader("🎯 Signaux d'Achat Actifs")
            buys = last_state[last_state['Signal'] == 1]
            if not buys.empty:
                cols = st.columns(3)
                for i, (_, row) in enumerate(buys.iterrows()):
                    with cols[i % 3]: st.markdown(row['Alpha_HTML'], unsafe_allow_html=True)
            else: st.info("Recherche de signaux Alpha...")

        # Radar (Tendance haussière + correction RSI)
        with radar_placeholder.container():
            st.subheader("🔍 Radar de Proximité")
            proximity = last_state[(last_state['RSI'] < 45) & (last_state['Close'] > last_state['EMA200'])].sort_values('RSI').head(6)
            cols = st.columns(3)
            for i, (_, row) in enumerate(proximity.iterrows()):
                with cols[i % 3]: st.markdown(f"**{row['Nom']}**\n{row['Alpha_HTML']}", unsafe_allow_html=True)

        st.sidebar.write(f"Dernière MAJ: {datetime.now().strftime('%H:%M:%S')}")
        time.sleep(60) # Rafraîchissement automatique chaque minute
        st.rerun() # Relance le script pour l'effet temps réel

    except Exception as e:
        st.error(f"Erreur flux: {e}")
        time.sleep(10)
