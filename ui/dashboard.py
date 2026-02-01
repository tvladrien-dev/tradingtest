import streamlit as st
import pandas as pd
from datetime import datetime
from ui.components import UIComponents

class Dashboard:
    """
    Orchestrateur de l'interface utilisateur Alpha Quant.
    Connecte le moteur TradingBotV1Elite aux composants graphiques.
    """
    def __init__(self, bot_instance):
        """
        Initialise le dashboard avec l'instance du bot pour accéder aux données.
        :param bot_instance: Instance de TradingBotV1Elite
        """
        self.bot = bot_instance
        self.ui = UIComponents()
        self.version = "12.5.2"

    def render_sidebar(self):
        """Rendu de la barre latérale avec contrôles système."""
        with st.sidebar:
            st.markdown("### 🛠️ PANNEAU DE CONTRÔLE")
            st.divider()
            
            scan_mode = st.selectbox(
                "Fréquence d'Analyse", 
                ["⚡ Haute Fréquence", "🛡️ Modéré", "💤 Mode Économie"],
                index=0
            )
            
            st.text_input("🔍 Focus Ticker (Recherche)", "").upper()
            
            if st.button("🚀 Lancer Synchronisation", use_container_width=True):
                with st.spinner("Sync en cours..."):
                    self.bot.sync_market_data()
                    st.success("Flux synchronisé !")

            st.divider()
            st.markdown("### 📊 STATUT SYSTÈME")
            st.success(f"Moteur Quant : OK")
            st.info(f"Version : {self.version}")
            
            # Affichage de la date de dernière sync
            last_sync_str = self.bot.last_sync.strftime('%H:%M:%S') if self.bot.last_sync else "Aucune"
            st.caption(f"Dernier flux : {last_sync_str}")
            
            return {"mode": scan_mode}

    def render_main_view(self):
        """Génère l'interface principale organisée en onglets."""
        
        # 1. Calcul des métriques macro pour le Header
        # On simule ou calcule le régime de marché basé sur le premier ticker (ex: CAC40)
        market_status = self._get_market_regime()
        self.ui.header_component(market_status)
        st.divider()

        # 2. Exécution de l'analyse pour obtenir les signaux récents
        signals = self.bot.process_signals()
        signals_df = pd.DataFrame(signals) if signals else pd.DataFrame()

        # 3. Structure par onglets
        tab_signals, tab_analysis, tab_news = st.tabs([
            "🎯 SIGNAUX ALPHA", 
            "📈 ANALYSE TECHNIQUE", 
            "📰 SENTIMENT & NEWS"
        ])

        # --- ONGLET 1 : SIGNAUX D'ACHAT ---
        with tab_signals:
            if signals_df.empty:
                st.warning("⚠️ En attente de données. Veuillez lancer une synchronisation.")
            else:
                # Filtrage des opportunités (Probabilité > 70%)
                buy_signals = signals_df[signals_df['probabilite'] >= 70]
                
                if buy_signals.empty:
                    st.info("💡 Aucun signal fort détecté. Le marché est en phase de compression.")
                else:
                    st.subheader(f"Opportunités Détectées ({len(buy_signals)})")
                    # Affichage des cartes stylisées
                    for _, row in buy_signals.iterrows():
                        self.ui.signal_card(
                            ticker=row['ticker'],
                            price=row['prix'],
                            rsi=row['rsi'],
                            proba=row['probabilite'],
                            action=row['action'],
                            sentiment=row['sentiment']
                        )

        # --- ONGLET 2 : ANALYSE TECHNIQUE DÉTAILLÉE ---
        with tab_analysis:
            if not self.bot.data_store:
                st.info("Lancez une synchronisation pour charger les graphiques.")
            else:
                available_tickers = list(self.bot.data_store.keys())
                selected_ticker = st.selectbox("Sélectionner un actif pour analyse profonde", available_tickers)
                
                # RÉCUPÉRATION DE L'HISTORIQUE COMPLET (Point crucial pour le graphique)
                df_full = self.bot.data_store[selected_ticker]
                
                col_chart, col_metrics = st.columns([3, 1])
                
                with col_chart:
                    # On passe le DataFrame complet au composant UI
                    fig = self.ui.create_candlestick_chart(df_full, selected_ticker)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                with col_metrics:
                    # Affichage des métriques de la dernière bougie
                    last_data = df_full.iloc[-1]
                    st.markdown("#### ⚡ Dernières Données")
                    st.metric("RSI (14)", f"{last_data.get('RSI', 0):.2f}")
                    st.metric("EMA 200", f"{last_data.get('EMA200', 0):.2f}€")
                    
                    # Distance EMA200
                    dist = ((last_data['Close'] / last_data['EMA200']) - 1) * 100
                    st.metric("Distance EMA200", f"{dist:.2f}%", delta=f"{dist:.1f}%")
                    
                    st.markdown("---")
                    st.caption("Stratégie : Convergence Trend-Following")

        # --- ONGLET 3 : ACTUALITÉS ET SENTIMENT ---
        with tab_news:
            st.subheader("Analyse du Sentiment Algorithmique")
            if not signals_df.empty:
                # Création d'un tableau propre pour les news/sentiments
                sentiment_table = signals_df[['ticker', 'prix', 'sentiment']].copy()
                st.table(sentiment_table)
            else:
                st.write("Aucun sentiment extrait pour le moment.")

    def _get_market_regime(self):
        """Détermine le régime de marché global pour le header."""
        # On vérifie si on a des données, sinon on renvoie des valeurs par défaut
        if not self.bot.data_store:
            return {'status': 'SCAN REQUIS', 'dist_ema_200': 0, 'volatility': 0, 'multiplier': 1}
        
        # Logique simplifiée : on prend le premier ticker pour l'indice de tendance
        first_ticker = list(self.bot.data_store.keys())[0]
        df = self.bot.data_store[first_ticker]
        last = df.iloc[-1]
        
        dist = ((last['Close'] / last['EMA200']) - 1) * 100
        regime = "BULLISH 🚀" if dist > 0 else "BEARISH 📉"
        
        return {
            'status': regime,
            'dist_ema_200': round(dist, 2),
            'volatility': 21, # Valeur fixe ou calculée via ATR/VIX
            'multiplier': 1 if dist < 0 else 2
        }

    def render_footer(self):
        """Pied de page institutionnel."""
        st.divider()
        st.caption("ALPHA QUANT TERMINAL © 2026 - Flux de données sécurisé via Yahoo Finance API.")
        if st.button("♻️ Recharger l'Interface"):
            st.rerun()
