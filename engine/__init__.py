"""
QUANT MASTER ENGINE - Package Initializer
Ce fichier permet d'exposer les moteurs de trading au reste de l'application.
Version: 12.5 (2026)
"""

# Importation des classes principales pour faciliter l'accès
# Cela permet de faire : from engine import TradingBotPEA
# au lieu de : from engine.trading_bot import TradingBotPEA

try:
    from .trading_bot import TradingBotPEA
    from .backtester import Backtester
    from .regime import MarketRegimeFilter
    from .news import NewsEngine
except ImportError as e:
    # On ne bloque pas l'importation ici pour permettre le debug, 
    # mais on enregistre l'erreur.
    import logging
    logging.warning(f"Initialisation partielle du package engine : {e}")

__all__ = [
    'TradingBotPEA',
    'Backtester',
    'MarketRegimeFilter',
    'NewsEngine'
]

__version__ = '12.5.0'
__author__ = 'Quant Master Master'
