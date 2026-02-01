import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

class UIComponents:
    """
    Bibliothèque de composants graphiques pour le Terminal Quant.
    Gère le rendu visuel, les graphiques techniques et les styles CSS.
    Version : 12.5.2 (2026) - Intégration DataStore
    """
    
    @staticmethod
    def set_page_config():
        """Initialise la configuration système et le style Matrix/Dark."""
        st.set_page_config(
            page_title="ALPHA QUANT | Terminal",
            page_icon="⚡",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Injection CSS pour un look institutionnel (Bloomberg Dark)
        st.markdown("""
            <style>
            .stApp { background-color: #0E1117; }
            [data-testid="stMetricValue"] { font-family: 'Courier New', monospace; font-size: 28px !important; }
            .stTabs [data-baseweb="tab-list"] { gap: 10px; }
            .stTabs [data-baseweb="tab"] {
                background-color: #161B22;
                border-radius: 5px 5px 0px 0px;
                padding: 10px 20px;
                color: #8B949E;
            }
            .stTabs [aria-selected="true"] {
                background-color: #1F6FEB !important;
                color: white !important;
            }
            /* Style personnalisé pour les cartes de signaux */
            .signal-card {
                border: 1px solid #30363D;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
                background-color: #161B22;
            }
            </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def header_component(market_status):
        """Barre d'état supérieure dynamique."""
        cols = st.columns([2, 1, 1, 1])
        
        with cols[0]:
            st.title("⚡ QUANT MASTER v12.5")
            st.caption(f"Dernière synchronisation flux : {datetime.now().strftime('%H:%M:%S')}")
            
        with cols[1]:
            # Gestion de la couleur en fonction du régime (Bullish/Bearish)
            status_val = market_status.get('status', 'NEUTRE')
            color = "normal" if "BULLISH" in status_val else "inverse"
            st.metric("RÉGIME MARCHÉ", status_val, 
                      delta=f"{market_status.get('dist_ema_200', 0)}% / EMA200",
                      delta_color=color)
            
        with cols[2]:
            vol_val = market_status.get('volatility', 20.0)
            st.metric("VOLATILITÉ (VIX)", f"{vol_val}%", 
                      delta="RISQUE ÉLEVÉ" if vol_val > 22 else "STABLE",
                      delta_color="inverse")
            
        with cols[3]:
            st.metric("LEVIER CONSEILLÉ", f"x{market_status.get('multiplier', 1)}")

    @staticmethod
    def create_candlestick_chart(df, ticker_name):
        """
        Génère un graphique technique professionnel.
        Supporte l'historique complet et les indicateurs techniques du bot.
        """
        if df is None or df.empty:
            st.warning(f"Données graphiques indisponibles pour {ticker_name}")
            return None

        # --- NORMALISATION DE LA CASSE ---
        # On s'assure de trouver les colonnes peu importe si elles sont en MAJ ou min
        df.columns = [c.upper() for c in df.columns]

        # Création de la figure avec 2 lignes (Prix + RSI)
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05, 
            subplot_titles=(f'Analyse Technique : {ticker_name}', 'RSI (14)'),
            row_heights=[0.7, 0.3]
        )

        # 1. TRACÉ DES CHANDELIERS
        # Vérification de la présence des colonnes OHLC
        ohlc_cols = ['OPEN', 'HIGH', 'LOW', 'CLOSE']
        if all(col in df.columns for col in ohlc_cols):
            fig.add_trace(go.Candlestick(
                x=df.index, 
                open=df['OPEN'], high=df['HIGH'],
                low=df['LOW'], close=df['CLOSE'], 
                name='Prix (OHLC)'
            ), row=1, col=1)
        else:
            # Fallback sur une courbe de clôture simple
            fig.add_trace(go.Scatter(
                x=df.index, y=df['CLOSE'], 
                line=dict(color='#1F6FEB', width=2), 
                name='Prix Clôture'
            ), row=1, col=1)

        # 2. MOYENNES MOBILES (EMA)
        if 'EMA200' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df['EMA200'], 
                line=dict(color='#FFD700', width=1.5, dash='dash'), 
                name='EMA 200 (Tendance)'
            ), row=1, col=1)
            
        if 'EMA50' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df['EMA50'], 
                line=dict(color='#FF3131', width=1), 
                name='EMA 50'
            ), row=1, col=1)

        # 3. RSI
        if 'RSI' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df['RSI'], 
                line=dict(color='#ADFF2F', width=2), 
                name='RSI'
            ), row=2, col=1)
            # Seuils RSI standard
            fig.add_hline(y=70, line_dash="dot", row=2, col=1, line_color="#FF3131", annotation_text="Surachat")
            fig.add_hline(y=30, line_dash="dot", row=2, col=1, line_color="#00FF41", annotation_text="Survente")

        # Mise en forme Cosmétique
        fig.update_layout(
            height=700,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=50, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        # Ajustement des axes
        fig.update_yaxes(gridcolor='#30363D', zeroline=False)
        fig.update_xaxes(gridcolor='#30363D', zeroline=False)
        
        return fig

    @staticmethod
    def signal_card(ticker, price, rsi, proba, action, sentiment):
        """Affiche une alerte de trading stylisée basée sur les données du Bot."""
        # Détermination de la couleur en fonction de l'action
        if action == "ACHAT":
            color = "#00FF41"
            bg_glow = "rgba(0, 255, 65, 0.1)"
        elif action == "VENTE":
            color = "#FF3131"
            bg_glow = "rgba(255, 49, 49, 0.1)"
        else:
            color = "#8B949E"
            bg_glow = "transparent"
        
        st.markdown(f"""
            <div style="border: 1px solid #30363D; border-radius: 10px; padding: 15px; margin-bottom: 15px; 
                        background-color: #161B22; border-left: 5px solid {color}; box-shadow: 0 4px 15px {bg_glow};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 22px; font-weight: bold; color: white;">{ticker}</span><br>
                        <span style="color: #8B949E; font-family: monospace;">PRIX ACTUEL: {price:.2f}€</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: {color}; font-size: 24px; font-weight: bold;">{action}</span><br>
                        <span style="color: white; font-size: 14px;">Confiance: {proba}%</span>
                    </div>
                </div>
                <div style="margin-top: 12px; font-size: 13px; color: #8B949E; border-top: 1px solid #30363D; padding-top: 8px; display: flex; justify-content: space-between;">
                    <span>📊 RSI: {rsi:.1f}</span>
                    <span>📰 Sentiment: {sentiment}</span>
                    <span>🛡️ Protection: ATR Adaptatif</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def performance_dashboard(metrics):
        """Panneau de statistiques de backtest ou de session."""
        cols = st.columns(4)
        cols[0].metric("Performance", f"{metrics.get('TotalReturn', 0):.2%}")
        cols[1].metric("Ratio Sharpe", f"{metrics.get('SharpeRatio', 0):.2f}")
        cols[2].metric("Drawdown Max", f"{metrics.get('MaxDrawdown', 0):.2%}", delta_color="inverse")
        cols[3].metric("Capital Final", f"{metrics.get('FinalValue', 0):.0f} €")
