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
# 300 000 ms = 5 minutes
st_autorefresh(interval=300000, key="bot_refresh_loop")

# --- INITIALISATION DU MOTEUR ---
@st.cache_resource
def init_bot():
    # Liste consolidée de tes actifs (Cryptos, CAC40, Nasdaq, etc.)
    # Note : Le bot gère le nettoyage des actifs délistés en interne
    from data.tickers_list import TICKERS_CONSOLIDATED  # Import de ta liste existante
    return TradingBotV1Elite(tickers=TICKERS_CONSOLIDATED)

bot = init_bot()

# --- BARRE LATÉRALE (SIDEBAR) ---
st.sidebar.title("🚀 Contrôle Elite V1")
st.sidebar.markdown(f"**Heure France :** {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.success("Système : Connecté aux Marchés")

# Option pour forcer manuellement si besoin
if st.sidebar.button("🔄 Lancer un Scan Manuel"):
    st.cache_resource.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("""
**Stratégie V1 activée :**
- ✅ Tendance EMA200
- ✅ Graphique (Higher Lows)
- ✅ Sentiment (News)
- ✅ Macro (VIX)
""")

# --- TITRE ET RÉSUMÉ ---
st.title("🛡️ Quant Master V1 : Tendance Saine & Sentiment")
st.caption("Analyse automatisée basée sur l'ADN de la stratégie Mean Reversion confirmée.")

# --- MOTEUR DE SCAN ---
with st.spinner("Analyse approfondie des graphiques et de l'actualité mondiale..."):
    # 1. On synchronise les données
    bot.sync_market_data()
    # 2. On traite les signaux (Triés par Action puis Probabilité en interne)
    signals = bot.process_signals()

# Indicateurs clés en haut
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Ordres d'Achat", len([s for s in signals if s['action'] == "ACHAT"]))
with col_m2:
    st.metric("Ordres de Vente", len([s for s in signals if s['action'] == "VENTE"]))
with col_m3:
    vix_val = signals[0]['vix'] if signals else "N/A"
    st.metric("Indice VIX (Peur)", vix_val)
with col_m4:
    st.metric("Scan Actif", f"{len(signals)} actifs")

st.divider()

# --- VISUEL : PRIORITÉ AUX ORDRES D'ACHAT ET VENTE ---
st.subheader("🎯 Opportunités à Haute Probabilité")

if not signals:
    st.info("Recherche de signaux confirmés en cours...")
else:
    # On isole uniquement les conseils d'action (Achat/Vente)
    oportunites = [s for s in signals if s['action'] in ["ACHAT", "VENTE"]]
    
    if not oportunites:
        st.warning("Aucune opportunité confirmée pour le moment (Filtres V1 stricts).")
    else:
        for s in oportunites:
            # Code couleur selon l'action
            header_color = "🟢" if s['action'] == "ACHAT" else "🔴"
            
            with st.expander(f"{header_color} **{s['action']}** | {s['nom']} ({s['ticker']}) — Confiance : {s['probabilite']}%", expanded=(s['action']=="ACHAT")):
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

                # Bouton de notification manuelle
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
        title="Répartition par Secteur d'Activité",
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
        df_full[['ticker', 'nom', 'action', 'probabilite', 'prix', 'sentiment', 'sector']],
        use_container_width=True,
        hide_index=True
    )

# PIED DE PAGE
st.markdown("---")
st.caption(f"Quant Master V1 • Système de trading automatisé • Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
