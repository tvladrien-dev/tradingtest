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
# Le bot s'actualise toutes les 300 secondes (5 min) automatiquement
st_autorefresh(interval=300000, key="bot_refresh_loop")

# --- INITIALISATION DU MOTEUR ---
@st.cache_resource
def init_bot():
    """
    Initialisation du bot avec import depuis le dossier config.
    """
    try:
        from config.tickers_list import TICKERS_CONSOLIDATED
        return TradingBotV1Elite(tickers=TICKERS_CONSOLIDATED)
    except ModuleNotFoundError:
        # Fallback de sécurité pour éviter le crash au lancement
        st.error("⚠️ Erreur : Dossier 'config' introuvable ou __init__.py manquant.")
        backup_tickers = ["BTC-USD", "ETH-USD", "AIR.PA", "MC.PA", "TSLA", "AAPL"]
        return TradingBotV1Elite(tickers=backup_tickers)

bot = init_bot()

# --- BARRE LATÉRALE (SIDEBAR) ---
st.sidebar.title("🚀 Contrôle Elite V1")
st.sidebar.markdown(f"**Heure France :** {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.success("Système : Connecté aux Marchés")

if st.sidebar.button("🔄 Lancer un Scan Manuel"):
    st.cache_resource.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("""
**Stratégie V1 activée :**
- ✅ Tendance EMA200
- ✅ Survente RSI <= 35
- ✅ Sentiment (News)
- ✅ Macro (VIX)
""")

# --- TITRE ET RÉSUMÉ ---
st.title("🛡️ Quant Master V1 : Tendance Saine & Sentiment")
st.caption(f"Analyse automatisée basée sur l'ADN de la stratégie V1 - RSI < 35. France : {datetime.now().strftime('%H:%M')}")

# --- MOTEUR DE SCAN ---
with st.spinner("Analyse approfondie des graphiques et de l'actualité mondiale..."):
    # 1. On synchronise les données
    bot.sync_market_data()
    # 2. On traite les signaux (Triés par Action puis Probabilité en interne)
    signals = bot.process_signals()

# Indicateurs clés en haut
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    achats_count = len([s for s in signals if s['action'] == "ACHAT"])
    st.metric("Ordres d'Achat", achats_count)
with col_m2:
    ventes_count = len([s for s in signals if s['action'] == "VENTE"])
    st.metric("Ordres de Vente", ventes_count)
with col_m3:
    vix_val = signals[0]['vix'] if signals else "N/A"
    st.metric("Indice VIX (Peur)", vix_val)
with col_m4:
    st.metric("Scan Actif", f"{len(signals)} actifs")

st.divider()

# --- VISUEL : PRIORITÉ AUX ORDRES D'ACHAT PUIS ORDRES DE VENTE ---
st.subheader("🎯 Opportunités à Haute Probabilité")

# Filtrage pour l'affichage prioritaire
oportunites = [s for s in signals if s['action'] in ["ACHAT", "VENTE"]]

if not oportunites:
    st.info("Recherche de signaux confirmés (RSI < 35 & EMA200) en cours...")
else:
    # Le bot trie déjà par probabilité décroissante dans process_signals()
    for s in oportunites:
        # Code couleur selon l'action
        header_color = "🟢" if s['action'] == "ACHAT" else "🔴"
        
        # Expander visuel
        with st.expander(f"{header_color} **{s['action']}** | {s['nom']} ({s['ticker']}) — Probabilité : {s['probabilite']}%", expanded=(s['action']=="ACHAT")):
            c1, c2, c3 = st.columns([1, 1, 1])
            
            with c1:
                st.markdown("**🔍 Technique & Macro**")
                st.write(f"Prix Actuel : `{s['prix']}€`")
                st.write(f"EMA 200 : `{s['ema200']}€`")
                st.write(f"VIX : `{s['vix']}`")
                st.write(f"RSI : `{s['rsi']}` | MACD : `{s['macd']}`")
            
            with c2:
                st.markdown("**🌍 Sentiment & Graphique**")
                st.write(f"Secteur : `{s['sector']}`")
                st.write(f"Actu : **{s['sentiment']}**")
                st.write(f"Tendance Graphique : `Confirmée ✅`")
            
            with c3:
                st.markdown("**💰 Management du Risque**")
                st.success(f"Vente Conseillée : **{s['tp']}€**")
                st.info(f"Gain Potentiel : **+{s['gain_pct']}%**")
                st.error(f"Stop Loss Suiveur : **-{s['sl_pct']}%**")
                st.caption("Protection : Volatilité ATR x2")

            # Bouton de notification NTFY
            if st.button(f"Envoyer Alerte NTFY pour {s['ticker']}", key=f"btn_{s['ticker']}"):
                if bot.send_notification(s):
                    st.toast(f"Alerte envoyée pour {s['ticker']} !", icon="🚀")

# --- GRAPHIQUE DES SECTEURS ---
st.divider()
st.subheader("📊 Analyse Sectorielle des Conseils")

if oportunites:
    df_sect = pd.DataFrame(oportunites)
    fig = px.pie(
        df_sect, 
        names='sector', 
        hole=0.4,
        title="Répartition par Secteur d'Activité (Signaux Actifs)",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("En attente de signaux pour générer le graphique sectoriel.")

# --- SCAN COMPLET (TABLEAU DE VEILLE) ---
st.divider()
st.subheader("🔍 Tableau de Veille Global")
df_full = pd.DataFrame(signals)
if not df_full.empty:
    st.dataframe(
        df_full[['ticker', 'nom', 'action', 'probabilite', 'prix', 'rsi', 'sentiment', 'sector']],
        use_container_width=True,
        hide_index=True
    )

# PIED DE PAGE
st.markdown("---")
st.caption(f"Quant Master V1 • Système de trading automatisé • Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
