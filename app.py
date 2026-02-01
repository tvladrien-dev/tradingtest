import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from engine.trading_bot import TradingBotV1Elite

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="QUANT MASTER V1 | Elite Terminal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE CSS PERSONNALISÉ (TERMINAL LOOK) ---
st.markdown("""
    <style>
    /* Style des métriques */
    [data-testid="stMetric"] {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #3d4156;
    }
    /* Style des expanders */
    .stExpander {
        border: 1px solid #3d4156 !important;
        background-color: #0e1117 !important;
        border-radius: 8px !important;
    }
    /* Boutons personnalisés */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #00cc96;
        color: #00cc96;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTO-REFRESH (TEMPS RÉEL : 5 MINUTES) ---
st_autorefresh(interval=300000, key="bot_refresh_loop")

# --- 4. INITIALISATION & FUSION DES UNIVERS ---
@st.cache_resource
def init_bot():
    """
    Importe et fusionne les tickers depuis commodities.py, cryptos.py et pea_stocks.py.
    """
    combined_tickers = []
    market_counts = {"Cryptos": 0, "PEA": 0, "Commodities": 0}
    
    # Extraction sécurisée des tickers
    try:
        from config.cryptos import CRYPTO_UNIVERSE
        t_crypto = [item['ticker'] for item in CRYPTO_UNIVERSE]
        combined_tickers.extend(t_crypto)
        market_counts["Cryptos"] = len(t_crypto)
    except Exception: pass

    try:
        from config.pea_stocks import PEA_UNIVERSE
        t_pea = [item['ticker'] for item in PEA_UNIVERSE]
        combined_tickers.extend(t_pea)
        market_counts["PEA"] = len(t_pea)
    except Exception: pass

    try:
        from config.commodities import COMMODITIES_UNIVERSE
        t_comm = [item['ticker'] for item in COMMODITIES_UNIVERSE]
        combined_tickers.extend(t_comm)
        market_counts["Commodities"] = len(t_comm)
    except Exception: pass

    # Nettoyage et Instanciation
    final_list = list(set(combined_tickers))
    if not final_list:
        final_list = ["BTC-USD", "ETH-USD", "AIR.PA"] # Secours minimal
        
    return TradingBotV1Elite(tickers=final_list), market_counts

bot, counts = init_bot()

# --- 5. BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/diamond.png", width=60)
    st.title("Elite Control")
    st.markdown(f"**Flux :** Synchronisé ✅")
    st.markdown(f"**Dernier Scan :** {datetime.now().strftime('%H:%M:%S')}")
    
    st.divider()
    st.subheader("📊 Inventaire des Actifs")
    st.write(f"🪙 Cryptomonnaies : `{counts['Cryptos']}`")
    st.write(f"🇪🇺 Actions PEA : `{counts['PEA']}`")
    st.write(f"🛢️ Commodities : `{counts['Commodities']}`")
    st.info(f"Total : {sum(counts.values())} actifs analysés")
    
    st.divider()
    if st.button("🔄 FORCER RE-SCAN"):
        st.cache_resource.clear()
        st.rerun()
    
    st.divider()
    st.caption("Stratégie V1 Elite : RSI < 35, EMA 200, Sentiment News, VIX Macro.")

# --- 6. ENTÊTE PRINCIPALE ---
st.title("🛡️ QUANT MASTER V1 : Intelligence de Marché")
st.caption("Analyse de tendance saine et détection de survente sur 340+ actifs mondiaux.")
st.markdown("---")

# --- 7. EXÉCUTION DU MOTEUR ---
with st.spinner("Analyse quantitative et sentimentale en cours..."):
    bot.sync_market_data()
    signals = bot.process_signals()

# --- 8. DASHBOARD MÉTRIQUES ---
m1, m2, m3, m4 = st.columns(4)
with m1:
    achats = [s for s in signals if s['action'] == "ACHAT"]
    st.metric("📦 ORDRES ACHAT", len(achats))
with m2:
    ventes = [s for s in signals if s['action'] == "VENTE"]
    st.metric("🔴 ORDRES VENTE", len(ventes))
with m3:
    vix_val = signals[0]['vix'] if signals else 0
    st.metric("📉 INDICE VIX", vix_val, 
              delta="Marché Calme" if vix_val < 20 else "Alerte Volatilité", 
              delta_color="inverse")
with m4:
    st.metric("🔄 SCAN GLOBAL", f"{len(signals)} Actifs")

st.divider()

# --- 9. OPPORTUNITÉS PRIORITAIRES (ACHATS/VENTES) ---
st.subheader("🎯 Opportunités de Trading (Priorité RSI < 35)")

priorites = [s for s in signals if s['action'] in ["ACHAT", "VENTE"]]

if not priorites:
    st.warning("Aucun signal d'achat/vente détecté. Le bot surveille les niveaux de survente.")
else:
    for s in priorites:
        # Couleur et icône dynamiques
        color = "🟢" if s['action'] == "ACHAT" else "🔴"
        
        with st.expander(f"{color} **{s['action']}** | {s['nom']} ({s['ticker']}) — Score Confiance : {s['probabilite']}%", expanded=(s['action']=="ACHAT")):
            col_a, col_b, col_c = st.columns([1, 1, 1])
            
            with col_a:
                st.markdown("**🔍 Technique**")
                st.write(f"Prix : `{s['prix']} €/$`")
                st.write(f"RSI (14j) : `{s['rsi']}`")
                st.write(f"EMA 200 : `{s['ema200']} €/$`")
                st.write(f"MACD : `{s['macd']}`")
            
            with col_b:
                st.markdown("**🌍 Analyse Contextuelle**")
                st.write(f"Secteur : `{s['sector']}`")
                st.write(f"Sentiment : **{s['sentiment']}**")
                st.write(f"Tendance : `Haussière Long Terme ✅`")
            
            with col_c:
                st.markdown("**🛡️ Gestion & Risque**")
                st.success(f"Objectif TP : **{s['tp']} €/$**")
                st.error(f"Stop Loss : **-{s['sl_pct']}%**")
                st.info(f"Potentiel : **+{s['gain_pct']}%**")
                
                if st.button(f"Envoyer Alerte : {s['ticker']}", key=f"ntfy_{s['ticker']}"):
                    if bot.send_notification(s):
                        st.toast(f"Alerte envoyée pour {s['ticker']} !", icon="🚀")

# --- 10. VISUALISATION ANALYTIQUE ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 Répartition Sectorielle")
    if priorites:
        df_prio = pd.DataFrame(priorites)
        fig_bar = px.bar(df_prio, x='sector', color='action', barmode='group',
                         color_discrete_map={'ACHAT':'#00cc96', 'VENTE':'#ef553b'},
                         template="plotly_dark")
        st.plotly_chart(fig_bar, width="stretch")
    else:
        st.info("Données sectorielles en attente de signaux.")

with c2:
    st.subheader("🧬 Équilibre de l'Univers")
    fig_pie = px.pie(values=list(counts.values()), names=list(counts.keys()), 
                     hole=0.4, template="plotly_dark",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_pie, width="stretch")

# --- 11. TERMINAL COMPLET (TABLEAU DE VEILLE) ---
st.divider()
st.subheader("🔍 Tableau de Veille Global (Temps Réel)")
df_full = pd.DataFrame(signals)
if not df_full.empty:
    st.dataframe(
        df_full[['ticker', 'nom', 'action', 'probabilite', 'prix', 'rsi', 'sentiment', 'sector']],
        width="stretch",
        hide_index=True
    )

st.markdown("---")
st.caption(f"Quant Master V1 Elite Terminal • 2026 • Dernière synchronisation : {datetime.now().strftime('%H:%M:%S')}")
