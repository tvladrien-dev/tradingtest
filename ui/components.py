import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

class UIComponents:
    """
    Bibliothèque de composants graphiques pour le Terminal Quant.
    Gère le rendu visuel, les graphiques techniques et les styles CSS.
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
            color = "normal" if "BULLISH" in market_status['status'] else "inverse"
            st.metric("RÉGIME MARCHÉ", market_status['status'], 
                      delta=f"{market_status['dist_ema_200']}% / EMA200",
                      delta_color=color)
            
        with cols[2]:
            st.metric("VOLATILITÉ", f"{market_status['volatility']}%", 
                      delta="RISQUE ÉLEVÉ" if market_status['volatility'] > 22 else "STABLE",
                      delta_color="inverse")
            
        with cols[3]:
            st.metric("LEVIER CONSEILLÉ", f"x{market_status['multiplier']}")

    @staticmethod
    def create_candlestick_chart(df, ticker_name):
        """
        Génère un graphique technique professionnel.
        Sécurisé contre les colonnes manquantes ou mal nommées.
        """
        if df is None or df.empty:
            st.warning(f"Données graphiques indisponibles pour {ticker_name}")
            return None

        # --- NORMALISATION DES COLONNES ---
        # On force la première lettre en majuscule pour correspondre aux attentes de Plotly
        df.columns = [str(c).capitalize() for c in df.columns]

        # Création de la figure avec 2 lignes (Prix + RSI)
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05, 
            subplot_titles=(f'Analyse Technique : {ticker_name}', 'RSI (14)'),
            row_heights=[0.7, 0.3]
        )

        # 1. TRACÉ DES CHANDELIERS (OU COURBE DE CLÔTURE)
        ohlc_cols = ['Open', 'High', 'Low', 'Close']
        if all(col in df.columns for col in ohlc_cols):
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name='OHLC'
            ), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#1F6FEB'), name='Prix Clôture'), row=1, col=1)

        # 2. MOYENNE MOBILE 200 (EMA200)
        if 'Ema200' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Ema200'], 
                line=dict(color='#FFD700', width=1.5), 
                name='Moyenne 200J'
            ), row=1, col=1)

        # 3. RSI
        if 'Rsi' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Rsi'], 
                line=dict(color='#ADFF2F', width=2), 
                name='RSI'
            ), row=2, col=1)
            # Seuils RSI
            fig.add_hline(y=70, line_dash="dot", row=2, col=1, line_color="#FF3131")
            fig.add_hline(y=30, line_dash="dot", row=2, col=1, line_color="#00FF41")

        # Mise en forme Cosmétique
        fig.update_layout(
            height=600,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=50, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig

    @staticmethod
    def signal_card(ticker, price, change, rsi, signal_type):
        """Affiche une alerte de trading stylisée."""
        color = "#00FF41" if signal_type == "ACHAT" else "#FF3131"
        
        st.markdown(f"""
            <div style="border: 1px solid #30363D; border-radius: 10px; padding: 15px; margin-bottom: 10px; background-color: #161B22;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 20px; font-weight: bold; color: white;">{ticker}</span><br>
                        <span style="color: #8B949E;">Prix: {price}€</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: {color}; font-size: 22px; font-weight: bold;">{signal_type}</span><br>
                        <span style="color: {'#00FF41' if change >= 0 else '#FF3131'};">{change}%</span>
                    </div>
                </div>
                <div style="margin-top: 10px; font-size: 12px; color: #8B949E; border-top: 1px solid #30363D; padding-top: 5px;">
                    RSI: {rsi} | Indicateur: Alpha Convergence v12
                </div>
            </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def performance_dashboard(metrics):
        """Panneau de statistiques de backtest."""
        cols = st.columns(4)
        cols[0].metric("Performance", f"{metrics['TotalReturn']:.2%}")
        cols[1].metric("Ratio Sharpe", f"{metrics['SharpeRatio']:.2f}")
        cols[2].metric("Drawdown Max", f"{metrics['MaxDrawdown']:.2%}", delta_color="inverse")
        cols[3].metric("Capital Final", f"{metrics['FinalValue']:.0f} €")
