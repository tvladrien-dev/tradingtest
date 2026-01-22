import streamlit as st
import pandas as pd
from datetime import datetime
from ui.components import UIComponents

class Dashboard:
    """
    Orchestrateur de l'interface utilisateur Alpha Quant.
    Gère la mise en page, les onglets et la sécurité des données affichées.
    """
    def __init__(self, settings):
        self.settings = settings
        self.ui = UIComponents()

    def render_sidebar(self):
        """Rendu de la barre latérale avec contrôles utilisateur."""
        with st.sidebar:
            st.markdown("### 🛠️ PANNEAU DE CONTRÔLE")
            st.divider()
            
            scan_mode = st.selectbox(
                "Mode de Scan", 
                ["⚡ Temps Réel (60s)", "🛡️ Prudent (5min)", "💤 Veille"],
                index=0
            )
            
            search_query = st.text_input("🔍 Rechercher un Ticker", "").upper()
            
            st.divider()
            st.markdown("### 📊 STATUT SYSTÈME")
            st.success("Connexion Euronext : OK")
            st.info(f"Version Bot : {self.settings.VERSION}")
            
            return {"mode": scan_mode, "search": search_query}

    def render_main_view(self, market_status, signals_df, news_engine):
        """Génère l'interface principale organisée en onglets."""
        
        # 1. En-tête avec métriques macro
        self.ui.header_component(market_status)
        st.divider()

        # 2. Structure par onglets
        tab_signals, tab_analysis, tab_news = st.tabs([
            "🎯 SIGNAUX ALPHA", 
            "📈 ANALYSE TECHNIQUE", 
            "📰 FLUX ACTUALITÉS"
        ])

        # --- ONGLET 1 : SIGNAUX D'ACHAT ---
        with tab_signals:
            if signals_df is None or signals_df.empty:
                st.warning("Aucune donnée disponible. Attente du prochain flux...")
            else:
                # Filtrage des signaux d'achat (Signal == 1)
                buy_signals = signals_df[signals_df['Signal'] == 1]
                
                if buy_signals.empty:
                    st.info("💡 Aucun signal d'achat détecté. Le marché est en phase d'observation.")
                else:
                    st.subheader(f"Opportunités détectées ({len(buy_signals)})")
                    # On affiche les cartes de signaux
                    for _, row in buy_signals.iterrows():
                        self.ui.signal_card(
                            ticker=row.get('Ticker', 'N/A'),
                            price=row.get('Close', 0.0),
                            change=row.get('Change', 0.0),
                            rsi=row.get('RSI', 0.0),
                            signal_type="ACHAT"
                        )

        # --- ONGLET 2 : ANALYSE TECHNIQUE DÉTAILLÉE ---
        with tab_analysis:
            if signals_df is not None and not signals_df.empty:
                # Menu de sélection de l'actif
                available_tickers = sorted(signals_df['Ticker'].unique())
                selected_ticker = st.selectbox("Choisir un actif à analyser", available_tickers)
                
                # Extraction sécurisée de la ligne de données
                ticker_row = signals_df[signals_df['Ticker'] == selected_ticker].iloc[0]
                
                col_chart, col_metrics = st.columns([3, 1])
                
                with col_chart:
                    # Rendu du graphique via components.py
                    # Note : ticker_row est transformé en DataFrame pour le graphique
                    chart_df = pd.DataFrame([ticker_row]) 
                    fig = self.ui.create_candlestick_chart(chart_df, selected_ticker)
                    if fig:
                        st.plotly_chart(fig, width='stretch')
                    else:
                        st.error("Impossible de générer le graphique pour cet actif.")
                
                with col_metrics:
                    st.markdown("#### ⚡ Métriques Clés")
                    # Utilisation de .get() pour éviter tout crash si une colonne manque
                    st.metric("RSI (14)", f"{ticker_row.get('RSI', 'N/A')}")
                    st.metric("Dist. EMA200", f"{ticker_row.get('Dist_EMA200', 'N/A')}%")
                    st.metric("ATR (Volatilité)", f"{ticker_row.get('ATR', 'N/A')}")
                    
                    status_color = "green" if ticker_row.get('Signal') == 1 else "gray"
                    st.markdown(f"**Statut :** :{status_color}[{ticker_row.get('Status', 'NEUTRE')}]")
            else:
                st.info("Veuillez attendre la fin du premier scan pour l'analyse détaillée.")

        # --- ONGLET 3 : ACTUALITÉS ET SENTIMENT ---
        with tab_news:
            st.subheader("Dernières Actualités Marché")
            try:
                # Récupération des news macro (CAC 40 par défaut)
                news_items = news_engine.get_news_for_ticker("CAC 40")
                if news_items:
                    for item in news_items[:8]: # Top 8 news
                        with st.expander(f"{item['title']}"):
                            st.write(f"**Source :** {item['source']}")
                            st.write(f"**Date :** {item['date']}")
                            st.link_button("Lire l'article", item['link'])
                else:
                    st.write("Aucune actualité récente trouvée.")
            except Exception as e:
                st.error(f"Erreur de chargement du flux news : {e}")

    def render_footer(self):
        """Pied de page avec avertissements légaux."""
        st.divider()
        footer_cols = st.columns([3, 1])
        with footer_cols[0]:
            st.caption("© 2026 Alpha Quant PEA Engine - Terminal Professionnel.")
            st.caption("Avertissement : Les performances passées ne préjugent pas des performances futures. Risque de perte en capital.")
        with footer_cols[1]:
            if st.button("🔄 Refresh"):
                st.rerun()
