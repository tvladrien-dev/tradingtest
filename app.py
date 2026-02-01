import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
from engine.trading_bot import TradingBotV1Elite

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="QUANT MASTER V1 | Terminal Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GESTION DU FUSEAU HORAIRE (FRANCE) ---
def get_now_fr():
    return datetime.now(pytz.timezone('Europe/Paris'))

# --- 3. DESIGN CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    /* Fond des métriques et cartes */
    [data-testid="stMetric"] {
        background-color: #161a25;
        border: 1px solid #2e3446;
        padding: 20px;
        border-radius: 10px;
    }
    /* Stylisation des expanders (cartes signaux) */
    .stExpander {
        border: 1px solid #2e3446 !important;
        background-color: #0e1117 !important;
        border-radius: 12px !important;
        margin-bottom: 10px;
    }
    /* Boutons et alertes */
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        height: 3em;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        border-color: #00ffcc;
        color: #00ffcc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTO-REFRESH (5 MINUTES) ---
st_autorefresh(interval=300000, key="bot_refresh_loop")

# --- 5. INITIALISATION DU MOTEUR ---
@st.cache_resource
def init_bot():
    """
    Fusionne dynamiquement les tickers depuis les 3 fichiers de config.
    """
    combined_tickers = []
    inventory = {"Crypto": 0, "PEA": 0, "Commodities": 0}
    
    # Extraction sécurisée
    try:
        from config.cryptos import CRYPTO_UNIVERSE
        t_crypto = [i['ticker'] for i in CRYPTO_UNIVERSE]
        combined_tickers.extend(t_crypto)
        inventory["Crypto"] = len(t_crypto)
    except: pass

    try:
        from config.pea_stocks import PEA_UNIVERSE
        t_pea = [i['ticker'] for i in PEA_UNIVERSE]
        combined_tickers.extend(t_pea)
        inventory["PEA"] = len(t_pea)
    except: pass

    try:
        from config.commodities import COMMODITIES_UNIVERSE
        t_comm = [i['ticker'] for i in COMMODITIES_UNIVERSE]
        combined_tickers.extend(t_comm)
        inventory["Commodities"] = len(t_comm)
    except: pass

    final_list = list(set(combined_tickers))
    # Fallback si vide
    if not final_list: final_list = ["BTC-USD", "ETH-USD", "AIR.PA", "GC=F"]
    
    return TradingBotV1Elite(tickers=final_list), inventory

bot, market_stats = init_bot()

# --- 6. BARRE LATÉRALE (DASHBOARD CONTROL) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=70)
    st.title("ELITE CONTROL")
    
    # Affichage Heure France
    now = get_now_fr()
    st.write(f"📅 **Date :** {now.strftime('%d/%m/%Y')}")
    st.write(f"🕒 **Heure France :** {now.strftime('%H:%M:%S')}")
    st.success("Statut : Connecté au Marché")
    
    st.divider()
    st.subheader("📦 Portefeuille de Veille")
    st.write(f"🪙 Cryptos : `{market_stats['Crypto']}`")
    st.write(f"🇪🇺 Actions PEA : `{market_stats['PEA']}`")
    st.write(f"🛢️ Commodities : `{market_stats['Commodities']}`")
    st.info(f"Total : {sum(market_stats.values())} actifs analysés")
    
    st.divider()
    if st.button("🔄 ACTUALISER LE SCAN"):
        st.cache_resource.clear()
        st.rerun()

# --- 7. HEADER ET MÉTRIQUES ---
st.title("🛡️ QUANT MASTER V1 : Terminal de Trading")
st.caption(f"Système de détection de tendance et survente (RSI < 35).")

# Lancement du moteur
with st.spinner("Analyse quantitative et calcul du sentiment en cours..."):
    bot.sync_market_data()
    signals = bot.process_signals()

# Dashboard de tête
col1, col2, col3, col4 = st.columns(4)
with col1:
    achats = [s for s in signals if s['action'] == "ACHAT"]
    st.metric("📦 ORDRES ACHAT", len(achats))
with col2:
    ventes = [s for s in signals if s['action'] == "VENTE"]
    st.metric("🔴 ORDRES VENTE", len(ventes))
with col3:
    vix_val = signals[0]['vix'] if signals else 0
    st.metric("📉 VOLATILITÉ (VIX)", vix_val, delta="Stable" if vix_val < 25 else "Danger", delta_color="inverse")
with col4:
    st.metric("🔍 ACTIFS SCANNÉS", len(signals))

st.markdown("---")

# --- 8. SECTION DES SIGNAUX (PRO CARDS) ---
st.subheader("🎯 Opportunités Prioritaires")

opportunites = [s for s in signals if s['action'] in ["ACHAT", "VENTE"]]

if not opportunites:
    st.warning("Aucun signal détecté sur les seuils RSI < 35 / EMA 200 pour le moment.")
else:
    # On affiche les achats en premier
    for s in opportunites:
        status_color = "🟢" if s['action'] == "ACHAT" else "🔴"
        
        with st.expander(f"{status_color} **{s['action']}** | {s['nom']} ({s['ticker']}) — Confiance : {s['probabilite']}%", expanded=(s['action']=="ACHAT")):
            c_tech, c_sent, c_risk = st.columns(3)
            
            with c_tech:
                st.markdown("**🔍 Données Techniques**")
                st.write(f"Prix : `{s['prix']} €/$`")
                st.write(f"RSI (14j) : `{s['rsi']}` (Seuil : 35)")
                st.write(f"EMA 200 : `{s['ema200']} €/$`")
                st.write(f"MACD Hist : `{s['macd']}`")
            
            with c_sent:
                st.markdown("**🌍 Contexte & Sentiment**")
                st.write(f"Secteur : `{s['sector']}`")
                st.write(f"Sentiment Actu : **{s['sentiment']}**")
                st.write(f"VIX Macro : `{s['vix']}`")
                st.write(f"Tendance : `Saine ✅`")
                
            with c_risk:
                st.markdown("**🛡️ Management du Risque**")
                st.success(f"Objectif Vente (TP) : **{s['tp']}**")
                st.error(f"Stop Loss (ATR x2) : **-{s['sl_pct']}%**")
                st.info(f"Potentiel : **+{s['gain_pct']}%**")
                
                if st.button(f"🚀 Alerter NTFY : {s['ticker']}", key=f"ntfy_{s['ticker']}"):
                    if bot.send_notification(s):
                        st.toast(f"Signal envoyé pour {s['ticker']} !")

# --- 9. ANALYSE GRAPHIQUE ---
st.markdown("---")
g1, g2 = st.columns([1.5, 1])

with g1:
    st.subheader("📊 Distribution Sectorielle des Opportunités")
    if opportunites:
        df_opt = pd.DataFrame(opportunites)
        fig_bar = px.bar(df_opt, x='sector', color='action', barmode='group',
                         color_discrete_map={'ACHAT':'#00cc96', 'VENTE':'#ef553b'},
                         template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Attente de signaux pour générer le graphique.")

with g2:
    st.subheader("🧬 Équilibre de l'Univers")
    fig_pie = px.pie(values=list(market_stats.values()), names=list(market_stats.keys()),
                     hole=0.5, template="plotly_dark", 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- 10. TERMINAL DE SURVEILLANCE GLOBAL ---
st.markdown("---")
st.subheader("🔍 Tableau de Veille Global (Live Feed)")
df_full = pd.DataFrame(signals)
if not df_full.empty:
    st.dataframe(
        df_full[['ticker', 'nom', 'action', 'probabilite', 'prix', 'rsi', 'sentiment', 'sector']],
        use_container_width=True,
        hide_index=True
    )

st.caption(f"Quant Master Terminal v1.0.3 • Paris, France • {get_now_fr().strftime('%H:%M:%S')}")
