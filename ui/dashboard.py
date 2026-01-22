import streamlit as st
import pandas as pd
from datetime import datetime
from ui.components import UIComponents

class Dashboard:
    """
    Orchestrateur de l'interface utilisateur.
    Gère la disposition des panneaux, les onglets et les interactions utilisateur.
    """
    def __init__(self, settings):
        self.settings = settings
        self.ui = UIComponents()

    def render_sidebar(self):
        """Affiche les contrôles de configuration dans la barre latérale."""
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/2502/2502543.png", width=80)
            st.title("Configuration")
            st.divider()
            
            # Filtres globaux
            st.subheader("⚙️ Paramètres de Scan")
            scan_mode = st.radio("Fréquence", ["⚡ Temps Réel", "🛡️ Prudent", "💤 Veille"])
            
            st.subheader("🔍 Filtrage Actifs")
            search = st.text_input("Rechercher un ticker (ex: TTE.PA)")
            
            st.divider()
            st.info(f"Version: {self.settings.VERSION}\nBot actif sur Euronext Paris")
            
            return {"mode": scan_mode, "search": search}

    def render_main_view(self, market_status, signals_df, news_engine):
        """Génère la vue principale avec le système d'onglets."""
        
        # 1. En-tête Dynamique
        self.ui.header_component(market_status)
        st.divider()

        # 2. Système d'onglets (Navigation principale)
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 PRÉDICTIONS ALPHA", 
            "📈 ANALYSE TECHNIQUE", 
            "📊 BACKTEST PERFORMANCE",
            "📅 TIMELINE & NEWS"
        ])

        # --- ONGLET 1 : SIGNAUX D'ACHAT ---
        with tab1:
            st.subheader("Signaux d'achat détectés (Top Alphas)")
            buy_signals = signals_df[signals_df['Signal'] == 1]
            
            if buy_signals.empty:
                st.warning("Aucun signal d'achat clair pour le moment. Le marché est sous surveillance.")
            else:
                for idx, row in buy_signals.iterrows():
                    self.ui.signal_card(
                        ticker=row['Ticker'],
                        price=row['Close'],
                        change=row['Change'],
                        rsi=row['RSI'],
                        signal_type="ACHAT"
                    )

        # --- ONGLET 2 : ANALYSE DÉTAILLÉE ---
        with tab2:
            selected_ticker = st.selectbox("Sélectionner un actif pour analyse profonde", signals_df['Ticker'].unique())
            ticker_data = signals_df[signals_df['Ticker'] == selected_ticker]
            
            col_chart, col_info = st.columns([3, 1])
            
            with col_chart:
                # On suppose ici que ticker_data contient l'historique nécessaire pour le graphique
                # Dans l'implémentation réelle, on passerait le DF historique complet
                st.plotly_chart(self.ui.create_candlestick_chart(ticker_data, selected_ticker), use_container_width=True)
            
            with col_info:
                st.markdown("### Metrics Clés")
                st.json({
                    "RSI (14)": round(ticker_data['RSI'].iloc[-1], 2),
                    "Distance EMA200": f"{ticker_data['Dist_EMA200'].iloc[-1]:.2f}%",
                    "Statut Volatilité": "Élevé" if ticker_data['ATR'].iloc[-1] > 2 else "Faible"
                })

        # --- ONGLET 3 : PERFORMANCE ---
        with tab3:
            st.subheader("Résultats de la stratégie (Simulation 1 an)")
            # Ces données viendraient normalement du Backtester
            mock_metrics = {
                "TotalReturn": 0.245,
                "SharpeRatio": 1.82,
                "MaxDrawdown": -0.12,
                "FinalValue": 31125.00
            }
            self.ui.performance_dashboard(mock_metrics)
            
            # Graphique de la courbe d'équité (Equity Curve)
            st.line_chart(pd.DataFrame({"Equity": [25000, 26000, 25500, 28000, 31125]}))

        # --- ONGLET 4 : ACTUALITÉS ---
        with tab4:
            st.subheader("Flux d'actualités et Sentiment")
            macro_sentiment = news_engine.get_macro_sentiment()
            st.metric("Sentiment Global Marché", macro_sentiment)
            
            st.divider()
            # Affichage des news pour le CAC 40
            news_items = news_engine.get_news_for_ticker("CAC 40")
            for item in news_items:
                with st.expander(f"{item['date']} - {item['title']} ({item['source']})"):
                    st.write(f"Source: {item['source']}")
                    st.link_button("Lire l'article", item['link'])

    @staticmethod
    def render_footer():
        """Pied de page avec informations légales."""
        st.divider()
        st.caption("Avertissement : Le trading comporte des risques. Ce bot est un outil d'aide à la décision et non un conseil financier.")
