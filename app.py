import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from engine.trading_bot import TradingBotV1Elite

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="QUANT MASTER V1 | Terminal Elite",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE CSS PERSONNALISÉ (POUR UN LOOK PRO) ---
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4156; }
    .stExpander { border: 1px solid #3d4156 !important; background-color: #0e1117 !important; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTO-REFRESH (5 MINUTES) ---
st_autorefresh(interval=300000, key="bot_refresh_loop")

# --- INITIALISATION DU MOTEUR ---
@st.cache_resource
def init_bot():
    """
    Fusionne les tickers des 3 fichiers de config : cryptos, pea_stocks, commodities.
    """
    all_tickers = []
    sources = {"Cryptos": 0, "Actions PEA": 0, "Matières Premières": 0}
    
    try:
        # Import des listes spécifiques
        try:
            from config.cryptos import CRYPTO_TICKERS
            all_tickers += CRYPTO_TICKERS
            sources["Cryptos"] = len(CRYPTO_TICKERS)
        except ImportError: pass
        
        try:
            from config.pea_stocks import PEA_TICKERS
            all_tickers += PEA_TICKERS
            sources["Actions PEA"] = len(PEA_TICKERS)
        except ImportError: pass
        
        try:
            from config.commodities import COMMODITIES_TICKERS
            all_tickers += COMMODITIES_TICKERS
            sources["Matières Premières"] = len(COMMODITIES_TICKERS)
        except ImportError: pass

        # Nettoyage des doublons
        all_tickers = list(set(all_tickers))
        
        if not all_tickers:
            all_tickers = ["BTC-USD", "ETH-USD", "GC=F", "AIR.PA", "MC.PA"] # Secours ultime
            
        bot_instance = TradingBotV1Elite(tickers=all_tickers)
        return bot_instance, sources
        
    except Exception as e:
        st.error(f"Erreur fatale d'initialisation : {e}")
        return TradingBotV1Elite(tickers=["BTC-USD"]), sources

# Chargement du bot et des stats sources
bot, source_stats = init_bot()

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=80)
    st.title("CONTRÔLE V1 ELITE")
    st.markdown(f"🗓️ **{datetime.now().strftime('%d %b %Y')}**")
    st.markdown(f"⏰ **{datetime.now().strftime('%H:%M:%S')}**")
    
    st.divider()
    st.subheader("📦 Actifs par Catégories")
    for cat, count in source_stats.items():
        st.write(f"• {cat} : `{count}`")
    
    st.divider()
    if st.button("🔄 RE-SCANNER LE MARCHÉ"):
        st.cache_resource.clear()
        st.rerun()
    
    st.divider()
    st.info("""
    **STRATÉGIE V1**
    - Achat : RSI ≤ 35 + EMA 200
    - Vente : RSI > 75
    - Risk : ATR x2 Suiveur
    """)

# --- TITRE ET RÉSUMÉ DES PERFORMANCES ---
st.title("⚖️ QUANT MASTER V1 : Tendance & Sentiment")
st.markdown("---")

# --- MOTEUR DE SCAN ---
with st.spinner("Analyse quantitative des 340+ actifs en cours..."):
    bot.sync_market_data()
    signals = bot.process_signals()

# INDICATEURS MACRO (METRICS)
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    achats = [s for s in signals if s['action'] == "ACHAT"]
    st.metric("🎯 SIGNAUX D'ACHAT", len(achats))
with col_m2:
    ventes = [s for s in signals if s['action'] == "VENTE"]
    st.metric("🔴 SIGNAUX DE VENTE", len(ventes))
with col_m3:
    vix_val = signals[0]['vix'] if signals else 20.0
    st.metric("📉 INDICE VIX (PEUR)", vix_val, delta="- stable" if vix_val < 25 else "+ Alerte")
with col_m4:
    st.metric("🔄 SCAN GLOBAL", f"{len(signals)} actifs")

st.divider()

# --- SECTION 1 : OPPORTUNITÉS PRIORITAIRES ---
st.subheader("🚀 Opportunités Prioritaires (RSI < 35)")

priorites = [s for s in signals if s['action'] in ["ACHAT", "VENTE"]]

if not priorites:
    st.warning("Aucun signal détecté sur les critères RSI < 35 / EMA 200.")
else:
    for s in priorites:
        # Couleur dynamique selon l'action
        if s['action'] == "ACHAT":
            tag_label = "🟢 SIGNAL ACHAT"
            border_color = "green"
        else:
            tag_label = "🔴 SIGNAL VENTE"
            border_color = "red"
            
        with st.expander(f"{tag_label} | {s['nom']} ({s['ticker']}) — Score : {s['probabilite']}%", expanded=(s['action']=="ACHAT")):
            col_left, col_mid, col_right = st.columns([1.2, 1, 1])
            
            with col_left:
                st.markdown("**📊 Données Techniques**")
                st.markdown(f"""
                - **Prix Actuel :** `{s['prix']} €/$`
                - **RSI (14j) :** `{s['rsi']}` (Seuil : 35)
                - **EMA 200 :** `{s['ema200']} €/$`
                - **Momentum :** `MACD {s['macd']}`
                """)
            
            with col_mid:
                st.markdown("**🌍 Intelligence Marché**")
                st.markdown(f"""
                - **Sentiment :** {s['sentiment']}
                - **Secteur :** `{s['sector']}`
                - **Macro :** `VIX {s['vix']}`
                - **Tendance :** `Saine ✅`
                """)
                
            with col_right:
                st.markdown("**🛡️ Gestion du Risque**")
                st.success(f"**TP (Cible) : {s['tp']} €/$**")
                st.error(f"**Stop Loss : -{s['sl_pct']}%**")
                st.info(f"**Ratio Reward : +{s['gain_pct']}%**")
                
                if st.button(f"ALERTE NTFY : {s['ticker']}", key=f"ntfy_{s['ticker']}"):
                    if bot.send_notification(s):
                        st.toast(f"Notification envoyée pour {s['ticker']} !")

# --- SECTION 2 : VISUALISATION DATA ---
st.divider()
c_chart1, c_chart2 = st.columns([1.5, 1])

with c_chart1:
    st.subheader("📊 Distribution Sectorielle des Signaux")
    if priorites:
        df_viz = pd.DataFrame(priorites)
        fig = px.bar(df_viz, x='sector', color='action', 
                     barmode='group', color_discrete_map={'ACHAT':'#00cc96', 'VENTE':'#ef553b'},
                     template="plotly_dark")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Attente de signaux pour graphique.")

with c_chart2:
    st.subheader("💡 Force du Sentiment")
    if priorites:
        fig_pie = px.pie(df_viz, names='sentiment', hole=0.5, template="plotly_dark")
        st.plotly_chart(fig_pie, width="stretch")

# --- SECTION 3 : TABLEAU DE SURVEILLANCE GLOBAL ---
st.divider()
st.subheader("🔍 Terminal de Veille Temps Réel")
df_full = pd.DataFrame(signals)
if not df_full.empty:
    # Stylisation du tableau
    st.dataframe(
        df_full[['ticker', 'nom', 'action', 'probabilite', 'prix', 'rsi', 'sentiment', 'sector']],
        width="stretch",
        hide_index=True
    )

st.markdown("---")
st.caption(f"QUANT MASTER V1 ELITE TERMINAL | Powered by Python 3.13 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
