import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from engine.trading_bot import TradingBotV1Elite

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Quant Master V1 - Terminal Elite",
    page_icon="📈",
    layout="wide"
)

# --- AUTO-REFRESH (TEMPS RÉEL : 5 MINUTES) ---
# Actualisation automatique toutes les 300 000 ms (5 minutes)
st_autorefresh(interval=300000, key="bot_refresh_loop")

# --- INITIALISATION DU MOTEUR ---
@st.cache_resource
def init_bot():
    """
    Initialise le bot avec la liste des tickers située dans le dossier config.
    Incorpore une sécurité si le module config est mal lu par Streamlit Cloud.
    """
    try:
        # Import dynamique depuis ton dossier config/
        from config.tickers_list import TICKERS_CONSOLIDATED
        return TradingBotV1Elite(tickers=TICKERS_CONSOLIDATED)
    except ModuleNotFoundError:
        # Liste de secours pour éviter le plantage complet de l'app
        st.error("🚨 Erreur d'import : Dossier 'config' ou 'tickers_list.py' introuvable.")
        st.info("Vérifiez la présence de __init__.py dans le dossier config.")
        backup_tickers = ["BTC-USD", "ETH-USD", "AIR.PA", "MC.PA", "TSLA", "AAPL", "NVDA", "MSFT"]
        return TradingBotV1Elite(tickers=backup_tickers)

bot = init_bot()

# --- BARRE LATÉRALE (SIDEBAR) ---
st.sidebar.title("🚀 Contrôle Elite V1")
st.sidebar.markdown(f"**Heure France :** {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.info("Statut : Analyse Temps Réel Active")

if st.sidebar.button("🔄 Forcer un Scan Manuel"):
    st.cache_resource.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("""
**Configuration Stratégie :**
- 🟢 **Achat :** RSI ≤ 35 & Prix > EMA200
- 🔴 **Vente :** RSI > 75
- 📊 **Risk :** ATR x2 (Stop Loss Suiveur)
- 🌎 **Filtres :** Sentiment News + VIX Macro
""")

# --- TITRE PRINCIPAL ---
st.title("🛡️ Quant Master V1 : Tendance & Sentiment")
st.caption("Système expert de détection de rebonds sur tendance saine.")
st.markdown("---")

# --- LOGIQUE DE SCAN ---
with st.spinner("Analyse des graphiques et scan de l'actualité mondiale en cours..."):
    # Synchronisation des données via Yahoo Finance
    bot.sync_market_data()
    # Traitement des signaux avec le tri (Achat > Vente > Probabilité)
    signals = bot.process_signals()

# --- RÉSUMÉ ANALYTIQUE (METRICS) ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    achats = [s for s in signals if s['action'] == "ACHAT"]
    st.metric("Signaux d'Achat", len(achats), delta=None)
with col_m2:
    ventes = [s for s in signals if s['action'] == "VENTE"]
    st.metric("Signaux de Vente", len(ventes), delta=None, delta_color="inverse")
with col_m3:
    vix_val = signals[0]['vix'] if signals else "N/A"
    st.metric("Indice VIX (Peur)", vix_val)
with col_m4:
    st.metric("Actifs Analysés", len(signals))

st.divider()

# --- SECTION 1 : SIGNAUX PRIORITAIRES (VISUEL EXPENDER) ---
st.subheader("🎯 Opportunités Prioritaires (RSI < 35 & EMA200)")

oportunites = [s for s in signals if s['action'] in ["ACHAT", "VENTE"]]

if not oportunites:
    st.warning("Aucun signal d'achat (RSI < 35) ou de vente détecté pour le moment.")
else:
    for s in oportunites:
        # Code couleur et icône selon l'action
        color_tag = "🟢" if s['action'] == "ACHAT" else "🔴"
        
        with st.expander(f"{color_tag} **{s['action']}** | {s['nom']} ({s['ticker']}) — Confiance : {s['probabilite']}%", expanded=(s['action']=="ACHAT")):
            c1, c2, c3 = st.columns([1, 1, 1])
            
            with c1:
                st.markdown("**🔍 Analyse Technique**")
                st.write(f"Prix : `{s['prix']}€`")
                st.write(f"RSI (14j) : `{s['rsi']}`")
                st.write(f"EMA 200 : `{s['ema200']}€`")
                st.write(f"MACD Hist : `{s['macd']}`")
            
            with c2:
                st.markdown("**🌍 Contexte & Secteur**")
                st.write(f"Secteur : `{s['sector']}`")
                st.write(f"Sentiment : **{s['sentiment']}**")
                st.write(f"Macro (VIX) : `{s['vix']}`")
                st.write("Tendance : `Confirmée ✅`")
            
            with c3:
                st.markdown("**💰 Ordre & Risque**")
                st.success(f"Objectif de Vente (TP) : **{s['tp']}€**")
                st.info(f"Gain Potentiel : **+{s['gain_pct']}%**")
                st.error(f"Stop Loss Suiveur : **-{s['sl_pct']}%**")
                st.caption("Protection basée sur ATR x2")

            # Bouton pour déclencher une alerte NTFY manuelle si besoin
            if st.button(f"Envoyer Alerte NTFY pour {s['ticker']}", key=f"ntfy_{s['ticker']}"):
                if bot.send_notification(s):
                    st.toast(f"Notification envoyée avec succès pour {s['ticker']} !", icon="🚀")

# --- SECTION 2 : ANALYSE DES SECTEURS (PIE CHART) ---
st.divider()
st.subheader("📊 Répartition par Secteur d'Activité")

if oportunites:
    df_sect = pd.DataFrame(oportunites)
    fig_sector = px.pie(
        df_sect, 
        names='sector', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="Secteurs favorisés par le Bot"
    )
    st.plotly_chart(fig_sector, use_container_width=True)
else:
    st.info("Données sectorielles insuffisantes (aucun signal détecté).")

# --- SECTION 3 : TABLEAU DE VEILLE COMPLET ---
st.divider()
st.subheader("🔍 Scan Global du Marché")
df_full = pd.DataFrame(signals)
if not df_full.empty:
    # On affiche le tableau complet trié pour la surveillance
    st.dataframe(
        df_full[['ticker', 'nom', 'action', 'probabilite', 'prix', 'rsi', 'sentiment', 'sector']],
        use_container_width=True,
        hide_index=True
    )

# --- PIED DE PAGE ---
st.markdown("---")
st.caption(f"Quant Master Terminal v1.0.2 • France • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
