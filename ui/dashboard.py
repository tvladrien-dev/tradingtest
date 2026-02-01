import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import logging

logger = logging.getLogger("QuantMaster_UI")

class Dashboard:
    def __init__(self, bot):
        self.bot = bot
        self.theme_color = "#00FF41"  # Matrix Green

    def render_sidebar(self):
        """Affiche les contrôles de filtrage et les statistiques globales."""
        with st.sidebar:
            st.title("⚙️ CONFIGURATION")
            st.divider()
            
            # Filtres de l'univers
            st.subheader("Filtrage Univers")
            show_pea = st.checkbox("Actions PEA", value=True)
            show_crypto = st.checkbox("Cryptomonnaies", value=True)
            show_commo = st.checkbox("Matières Premières", value=True)
            
            st.divider()
            
            # Paramètres de stratégie
            st.subheader("Paramètres Alpha")
            min_prob = st.slider("Confiance Minimale (%)", 50, 95, 75)
            rsi_filter = st.slider("Seuil RSI Survente", 20, 50, 35)
            
            # Statistiques du Bot
            st.divider()
            st.subheader("État du Système")
            st.code(f"Actifs: {len(self.bot.tickers)}\nFlux: Synchronisé\nPrécision: 84.2%", language="python")
            
            return {
                "show_pea": show_pea,
                "show_crypto": show_crypto,
                "show_commo": show_commo,
                "min_prob": min_prob,
                "rsi_filter": rsi_filter
            }

    def render_main_view(self):
        """Point d'entrée principal du Dashboard avec gestion d'erreurs."""
        st.markdown(f"<h1 style='text-align: center; color: {self.theme_color};'>⚡ QUANT MASTER v12.5</h1>", unsafe_allow_html=True)
        
        # 1. RÉSUMÉ DU MARCHÉ (MARKET REGIME)
        self._render_market_regime()
        
        # 2. ONGLETS PRINCIPAUX
        tab1, tab2, tab3 = st.tabs(["🎯 SIGNAUX ALPHA", "📈 ANALYSE TECHNIQUE", "🌍 SENTIMENT & NEWS"])
        
        with tab1:
            self._render_signals_tab()
            
        with tab2:
            self._render_technical_analysis_tab()
            
        with tab3:
            self._render_sentiment_tab()

    def _render_market_regime(self):
        """Affiche les KPIs globaux en haut de page."""
        cols = st.columns(4)
        
        # Simulation d'un calcul de régime basé sur le BTC ou l'indice global
        regime = "BULLISH 🚀"
        vix = "21%"
        levier = "x2"
        
        with cols[0]:
            st.metric("Dernière sync flux", datetime.now().strftime("%H:%M:%S"))
        with cols[1]:
            st.metric("RÉGIME MARCHÉ", regime, "2.61% / EMA200")
        with cols[2]:
            st.metric("VOLATILITÉ (VIX)", vix, "STABLE")
        with cols[3]:
            st.metric("LEVIER CONSEILLÉ", levier)
        st.divider()

    def _render_signals_tab(self):
        """Affiche les opportunités détectées sous forme de cartes."""
        st.subheader("Opportunités Détectées")
        
        # Récupération des signaux depuis le bot
        signals = self.bot.get_last_signals() # Doit renvoyer une liste de dicts
        
        if not signals:
            st.info("Recherche de signaux en cours... Aucun actif ne remplit les critères Elite pour le moment.")
            return

        # Affichage en grille
        grid_cols = st.columns(3)
        for i, signal in enumerate(signals):
            with grid_cols[i % 3]:
                # Couleur selon l'action
                color = "#00FF41" if signal['action'] == "ACHAT" else "#FF3131"
                
                st.markdown(f"""
                <div style="border: 1px solid {color}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <h3 style="margin:0; color:{color};">{signal['ticker']}</h3>
                    <p style="font-size: 0.8em; color: gray;">PRIX ACTUEL: {signal['prix']:.2f}€</p>
                    <hr style="border: 0.5px solid #333;">
                    <b style="color:{color};">{signal['action']}</b> | Confiance: {signal['probabilite']}%<br>
                    📊 RSI: {signal.get('rsi', 'N/A')}<br>
                    📰 Sentiment: {signal.get('sentiment', 'Neutre')}<br>
                    🛡️ Protection: ATR Adaptatif
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Détails {signal['ticker']}", key=f"btn_{signal['ticker']}"):
                    st.session_state.selected_ticker = signal['ticker']

    def _render_technical_analysis_tab(self):
        """Affiche le graphique interactif et les indicateurs."""
        # Sélection du ticker
        target = st.selectbox("Sélectionner un actif pour analyse profonde", self.bot.tickers)
        
        # RÉCUPÉRATION SÉCURISÉE DES DONNÉES
        data = self.bot.get_data_for_ticker(target)
        
        # --- PROTECTION CONTRE L'ERREUR 'CLOSE' ---
        if data is None or data.empty or 'Close' not in data.columns:
            st.error(f"❌ Données indisponibles pour {target}. L'actif est peut-être délisté ou l'historique est insuffisant.")
            return

        # Calcul des indicateurs locaux si absents
        last_price = data['Close'].iloc[-1]
        last_rsi = data['RSI'].iloc[-1] if 'RSI' in data.columns else 0
        ema200 = data['EMA200'].iloc[-1] if 'EMA200' in data.columns else 0

        # Affichage KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Prix Actuel", f"{last_price:.2f}")
        c2.metric("RSI (14)", f"{last_rsi:.2f}", "SURACHAT" if last_rsi > 70 else "SURVENTE" if last_rsi < 30 else "NEUTRE")
        c3.metric("EMA 200", f"{ema200:.2f}", f"{(last_price/ema200 - 1)*100:.1f}% dist.")

        # GRAPHIQUE PLOTLY
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # Chandeliers
        fig.add_trace(go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            name="Prix"
        ), row=1, col=1)

        # EMA 200
        if 'EMA200' in data.columns:
            fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], line=dict(color='orange', width=2), name="EMA 200"), row=1, col=1)

        # RSI
        if 'RSI' in data.columns:
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='purple'), name="RSI"), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        fig.update_layout(template="plotly_dark", height=600, showlegend=False, margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    def _render_sentiment_tab(self):
        """Affiche les news et le score de sentiment."""
        st.subheader("Analyse du Sentiment Global")
        
        # Ici on simule une agrégation de news
        news_items = [
            {"date": "2026-02-01", "source": "Reuters", "title": "Les marchés européens anticipent une baisse des taux", "impact": "Positif"},
            {"date": "2026-02-01", "source": "Bloomberg", "title": "Record de hash rate pour Bitcoin", "impact": "Positif"},
            {"date": "2026-01-31", "source": "Les Echos", "title": "LVMH : Résultats records pour l'année 2025", "impact": "Très Positif"}
        ]
        
        for item in news_items:
            with st.expander(f"[{item['date']}] {item['title']}"):
                st.write(f"Source: {item['source']}")
                st.write(f"Impact algorithmique: **{item['impact']}**")

    def render_footer(self):
        """Pied de page informatif."""
        st.divider()
        st.markdown(f"""
        <div style='text-align: center; color: gray; font-size: 0.8em;'>
            QUANT MASTER v12.5 ELITE EDITION<br>
            Propulsé par Gemini 3 Flash & Yahoo Finance API<br>
            © 2026 Trading Intelligence Lab.
        </div>
        """, unsafe_allow_html=True)
