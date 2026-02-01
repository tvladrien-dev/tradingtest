import json
import os
from .pea_stocks import PEA_UNIVERSE
from .cryptos import CRYPTO_UNIVERSE
from .commodities import COMMODITIES_UNIVERSE

class Settings:
    def __init__(self):
        # 1. Chargement du JSON pour les paramètres numériques
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(self.base_path, 'settings.json'), 'r') as f:
            self.params = json.load(f)

        # 2. Extraction des Tickers seuls (pour yfinance)
        self.TICKERS_PEA = [item['ticker'] for item in PEA_UNIVERSE]
        self.TICKERS_CRYPTO = [item['ticker'] for item in CRYPTO_UNIVERSE]
        self.TICKERS_COMMODITIES = [item['ticker'] for item in COMMODITIES_UNIVERSE]

        # 3. Mappings Nom/Secteur (pour l'affichage UI)
        self.METADATA = {item['ticker']: {"nom": item['nom'], "sector": item['sector']} 
                         for item in PEA_UNIVERSE + CRYPTO_UNIVERSE + COMMODITIES_UNIVERSE}

        # 4. Paramètres de trading
        self.CAPITAL_TOTAL = self.params.get("capital", 100000)
        self.RISK_PER_TRADE = self.params.get("risk_max", 0.05)

# Instance globale pour import facile
settings = Settings()
