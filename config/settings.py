"""
CONFIG SETTINGS - QUANT MASTER 2026
Centralisation des paramètres de trading, tickers et constantes UI.
"""

# 1. PARAMÈTRES GÉNÉRAUX DU BOT
BOT_NAME = "Alpha Quant PEA"
VERSION = "12.5.0"
DEBUG_MODE = False

# 2. LISTE DES ACTIFS (SÉLECTION PEA LIQUIDE - EURONEXT PARIS)
# Cette liste peut être étendue jusqu'à 200+ tickers
TICKERS_PEA = [
    # --- CAC 40 ---
    "AIR.PA", "AI.PA", "ALO.PA", "MT.PA", "CS.PA", "BNP.PA", "EN.PA", "CAP.PA",
    "CA.PA", "ACA.PA", "BN.PA", "DSY.PA", "EDF.PA", "ENGI.PA", "EL.PA", "RMS.PA",
    "KER.PA", "OR.PA", "LR.PA", "MC.PA", "ML.PA", "ORA.PA", "RI.PA", "PUB.PA",
    "SAF.PA", "SGO.PA", "SAN.PA", "SU.PA", "GLE.PA", "STLAP.PA", "STMPA.PA", 
    "TEP.PA", "HO.PA", "TTE.PA", "URW.PA", "VIE.PA", "DG.PA", "WLN.PA",
    
    # --- SBF 120 / MID CAPS ---
    "DIM.PA", "RNO.PA", "SART.PA", "UBI.PA", "VIV.PA", "SEB.PA", "CO.PA", 
    "KN.PA", "GET.PA", "GFC.PA", "ADP.PA", "SK.PA", "FDJ.PA"
]

# 3. SEUILS TECHNIQUES (STRATÉGIE QUANT)
STRATEGY_PARAMS = {
    "RSI_OVERSOLD": 32,          # Seuil d'achat (Survendu)
    "RSI_OVERBOUGHT": 70,        # Seuil de prudence (Suracheté)
    "EMA_TREND_SHORT": 20,       # Tendance rapide
    "EMA_TREND_LONG": 200,       # Tendance institutionnelle
    "MIN_VOLUME_STABILITY": 100000, # Volume min quotidien
    "ATR_MULTIPLIER_STOP": 2.0   # Distance du Stop Loss par rapport à la volatilité
}

# 4. GESTION DU RISQUE (MONEY MANAGEMENT)
RISK_MANAGEMENT = {
    "INITIAL_CAPITAL": 25000,    # Capital de départ en Euros
    "MAX_POSITION_SIZE": 0.10,   # Max 10% du capital par ligne
    "MAX_OPEN_POSITIONS": 8,     # Max 8 lignes simultanées
    "DEFAULT_FEE": 0.0035,       # Frais de courtage (0.35%)
    "RISK_FREE_RATE": 0.02       # Taux sans risque (2% pour le Sharpe)
}

# 5. CONFIGURATION TEMPS RÉEL
REFRESH_RATES = {
    "HIGH_VOLATILITY": 60,       # Scan toutes les minutes si marché nerveux
    "LOW_VOLATILITY": 300,       # Scan toutes les 5 min si marché calme
    "MARKET_OPEN": "09:00",
    "MARKET_CLOSE": "17:35"
}

# 6. ALERTES & NOTIFICATIONS
# Remplace par ton propre endpoint ntfy.sh pour recevoir les alertes mobiles
NOTIFICATIONS = {
    "ENABLED": True,
    "NTFY_TOPIC": "quant_pea_master_alert_2026",
    "ALERT_LEVEL": "SIGNALS_ONLY" # "ALL" pour avoir les infos macro aussi
}

# 7. DESIGN & UI (STREAMLIT)
UI_LAYOUT = {
    "THEME": "Dark",
    "PRIMARY_COLOR": "#00FF41",  # Vert Matrix / Terminal
    "CHART_THEME": "plotly_dark"
}
