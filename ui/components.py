import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

class UIComponents:
    """
    Bibliothèque de composants graphiques haute performance pour l'interface Quant.
    Optimisé pour le rendu Dark Mode et la lisibilité des données financières.
    """
    
    @staticmethod
    def set_page_config():
        """Initialise le style global de la page."""
        st.set_page_config(
            page_title="QUANT MASTER | Terminal",
            page_icon="⚡",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Injection de CSS personnalisé pour le look "Bloomberg / Matrix"
        st.markdown("""
            <style>
            .stApp { background-color: #0E1117; }
            .metric-card {
                background-color: #161B22;
                border: 1px solid #30363D;
                padding: 20px;
                border-radius: 10px;
                color: white;
            }
            .status-up { color: #00FF41; font-weight: bold; }
            .status-down { color: #FF3131; font-weight: bold; }
            .price-text { font-family: 'Courier New', Courier, monospace; font-size: 24px; }
            </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def header_component(market_status):
        """Affiche la barre de statut supérieure avec l'état du régime de marché."""
        cols = st.columns([2, 1, 1, 1])
        
        with cols[0]:
            st.title("⚡ QUANT MASTER v12.5")
            st.caption(f"Dernière synchronisation flux : {datetime.now().strftime('%H:%M:%S')}")
            
        with cols[1]:
            color = "#00FF41" if "BULLISH" in market_status['status'] else "#FF3131"
            st.metric("RÉGIME MARCHÉ", market_status['status'], 
                      delta=f"{market_status['dist_ema_200']}% (EMA200)",
                      delta_color="normal")
            
        with cols[2]:
            st.metric("VOLATILITÉ RÉALISÉE", f"{market_status['volatility']}%", 
                      delta="STABLE" if market_status['volatility'] < 22 else "STRESS",
                      delta_color="inverse")
            
        with cols[3]:
            st.metric("ALLOCATION MAX", f"{int(market_status['multiplier'] * 100)}%", help="Basé sur le filtre de régime macro")

    @staticmethod
    def create_candlestick_chart(df, ticker_name):
        """
        Génère un graphique en chandeliers avec indicateurs techniques (EMA, Bandes de Bollinger).
        """
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, subplot_titles=(f'Cours {ticker_name}', 'RSI (14)'), 
                           row_width=[0.3, 0.7])

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Prix'
        ), row=1, col=1)

        # Moyennes Mobiles
        if 'EMA20' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='#00FFFF', width=1), name='EMA 20'), row=1, col=1)
        if 'EMA200' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='#FFD700', width=2), name='EMA 200'), row=1, col=1)

        # Bandes de Bollinger
        if 'BB_High' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(dash='dash', color='rgba(255,255,255,0.2)'), name='BB High'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(dash='dash', color='rgba(255,255,255,0.2)'), fill='tonexty', name='BB Low'), row=1, col=1)

        # RSI
        if 'RSI' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#ADFF2F', width=2), name='RSI'), row=2, col=1)
            # Lignes de seuils RSI
            fig.add_hline(y=70, line_dash="dot", row=2, col=1, line_color="red")
            fig.add_hline(y=30, line_dash="dot", row=2, col=1, line_color="green")

        fig.update_layout(
            height=600,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig

    @staticmethod
    def signal_card(ticker, price, change, rsi, signal_type):
        """Affiche une carte de signal d'achat/vente stylisée."""
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                st.subheader(ticker)
                
            with col2:
                color = "#00FF41" if signal_type == "ACHAT" else "#FF3131"
                st.markdown(f"<h2 style='color: {color}; margin:0;'>{signal_type}</h2>", unsafe_allow_html=True)
                st.caption(f"RSI: {rsi:.2f} | Prix: {price:.2f}€")
                
            with col3:
                st.metric("Var.", f"{change:.2f}%")

    @staticmethod
    def performance_dashboard(metrics):
        """Affiche le résumé du backtest sous forme de tableau de bord financier."""
        cols = st.columns(4)
        cols[0].metric("Rendement Total", f"{metrics['TotalReturn']:.2%}")
        cols[1].metric("Ratio de Sharpe", f"{metrics['SharpeRatio']:.2f}")
        cols[2].metric("Max Drawdown", f"{metrics['MaxDrawdown']:.2%}", delta_color="inverse")
        cols[3].metric("Valeur Finale", f"{metrics['FinalValue']:.2f} €")
