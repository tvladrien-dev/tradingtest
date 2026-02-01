# config/commodities.py

# Liste optimisée pour Yahoo Finance (Flux gratuit)
# Note : Certains métaux industriels LME sont instables sur Yahoo, 
# nous privilégions les contrats du COMEX/NYMEX.

COMMODITIES_UNIVERSE = [
    # --- MÉTAUX PRÉCIEUX ---
    {"ticker": "GC=F", "nom": "Or (Gold)", "sector": "Métaux Précieux"},
    {"ticker": "SI=F", "nom": "Argent (Silver)", "sector": "Métaux Précieux"},
    {"ticker": "PL=F", "nom": "Platine (Platinum)", "sector": "Métaux Précieux"},
    {"ticker": "PA=F", "nom": "Palladium", "sector": "Métaux Précieux"},

    # --- ÉNERGIE ---
    {"ticker": "CL=F", "nom": "Pétrole Crude (WTI)", "sector": "Énergie"},
    {"ticker": "BZ=F", "nom": "Pétrole Brent", "sector": "Énergie"},
    {"ticker": "NG=F", "nom": "Gaz Naturel", "sector": "Énergie"},
    {"ticker": "HO=F", "nom": "Fioul Domestique", "sector": "Énergie"},
    {"ticker": "RB=F", "nom": "Essence RBOB", "sector": "Énergie"},

    # --- MÉTAUX INDUSTRIELS ---
    {"ticker": "HG=F", "nom": "Cuivre (Copper)", "sector": "Métaux Industriels"},
    # L'Aluminium et le Nickel sont souvent absents en continu sur Yahoo. 
    # On utilise les proxies les plus proches si disponibles :
    {"ticker": "ALI=F", "nom": "Aluminium", "sector": "Métaux Industriels"}, 

    # --- AGRICULTURE ---
    {"ticker": "ZC=F", "nom": "Maïs (Corn)", "sector": "Agriculture"},
    {"ticker": "ZW=F", "nom": "Blé (Wheat)", "sector": "Agriculture"},
    {"ticker": "ZS=F", "nom": "Soja (Soybean)", "sector": "Agriculture"},
    {"ticker": "KC=F", "nom": "Café Arabica", "sector": "Agriculture"},
    {"ticker": "CC=F", "nom": "Cacao (Cocoa)", "sector": "Agriculture"},
    {"ticker": "CT=F", "nom": "Coton (Cotton)", "sector": "Agriculture"},
    {"ticker": "SB=F", "nom": "Sucre (Sugar)", "sector": "Agriculture"},
    {"ticker": "ZO=F", "nom": "Avoine (Oats)", "sector": "Agriculture"},
    {"ticker": "ZR=F", "nom": "Riz (Rough Rice)", "sector": "Agriculture"},

    # --- ÉLEVAGE ---
    {"ticker": "GF=F", "nom": "Bétail (Feeder Cattle)", "sector": "Élevage"},
    {"ticker": "LE=F", "nom": "Bétail Vivant (Live Cattle)", "sector": "Élevage"},
    {"ticker": "HE=F", "nom": "Porc Maigre (Lean Hogs)", "sector": "Élevage"},

    # --- BOIS & AUTRES ---
    # Le bois (LBS) a changé de contrat sur le CME, le ticker 'LBS=F' est souvent obsolète.
    # On utilise 'LUM=F' qui est le nouveau standard (Lumber).
    {"ticker": "LUM=F", "nom": "Bois de charpente", "sector": "Industrie"},
    {"ticker": "OJ=F", "nom": "Jus d'Orange", "sector": "Agriculture"}
]
