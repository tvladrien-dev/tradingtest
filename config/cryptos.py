# config/cryptos.py

# Liste vérifiée des 150 cryptomonnaies majeures pour Yahoo Finance
# Format strict : TICKER-USD (ou ticker spécifique quand nécessaire)

CRYPTO_UNIVERSE = [
    # --- LES PILIERS ---
    {"ticker": "BTC-USD", "nom": "Bitcoin", "sector": "Store of Value"},
    {"ticker": "ETH-USD", "nom": "Ethereum", "sector": "Layer 1 - Smart Contracts"},

    # --- LAYER 1 & INFRASTRUCTURE ---
    {"ticker": "SOL-USD", "nom": "Solana", "sector": "Layer 1 - High Perf"},
    {"ticker": "BNB-USD", "nom": "Binance Coin", "sector": "Exchange / L1"},
    {"ticker": "ADA-USD", "nom": "Cardano", "sector": "Layer 1"},
    {"ticker": "AVAX-USD", "nom": "Avalanche", "sector": "Layer 1"},
    {"ticker": "DOT-USD", "nom": "Polkadot", "sector": "Interoperability"},
    {"ticker": "NEAR-USD", "nom": "Near Protocol", "sector": "Layer 1 - Sharding"},
    {"ticker": "APT-USD", "nom": "Aptos", "sector": "Layer 1 - Move"},
    {"ticker": "SUI-USD", "nom": "Sui", "sector": "Layer 1 - Move"},
    {"ticker": "KAS-USD", "nom": "Kaspa", "sector": "Layer 1 - PoW"},
    # Toncoin utilise un ticker spécifique sur Yahoo
    {"ticker": "TON11419-USD", "nom": "Toncoin", "sector": "Layer 1 - Telegram"},
    {"ticker": "SEI-USD", "nom": "Sei Network", "sector": "Layer 1 - Trading"},
    {"ticker": "ALGO-USD", "nom": "Algorand", "sector": "Layer 1"},
    {"ticker": "HBAR-USD", "nom": "Hedera Hashgraph", "sector": "Enterprise L1"},
    {"ticker": "STX-USD", "nom": "Stacks", "sector": "Bitcoin Layer 2"},
    {"ticker": "EGLD-USD", "nom": "MultiversX", "sector": "Layer 1"},
    {"ticker": "FTM-USD", "nom": "Fantom", "sector": "Layer 1"},
    {"ticker": "INJ-USD", "nom": "Injective", "sector": "Layer 1 - DeFi"},
    {"ticker": "TIA-USD", "nom": "Celestia", "sector": "Modular Data"},
    {"ticker": "MINA-USD", "nom": "Mina Protocol", "sector": "ZK - L1"},
    {"ticker": "CFX-USD", "nom": "Conflux", "sector": "Layer 1 - China"},

    # --- LAYER 2 ---
    {"ticker": "POL-USD", "nom": "Polygon (POL)", "sector": "Layer 2"},
    {"ticker": "OP-USD", "nom": "Optimism", "sector": "Layer 2 - Rollup"},
    {"ticker": "ARB-USD", "nom": "Arbitrum", "sector": "Layer 2 - Rollup"},
    {"ticker": "MNT-USD", "nom": "Mantle", "sector": "Layer 2"},
    {"ticker": "STRK-USD", "nom": "Starknet", "sector": "Layer 2 - ZK"},
    {"ticker": "METIS-USD", "nom": "Metis", "sector": "Layer 2"},
    {"ticker": "IMX-USD", "nom": "Immutable X", "sector": "Layer 2 - Gaming"},
    {"ticker": "LRC-USD", "nom": "Loopring", "sector": "Layer 2 DEX"},

    # --- IA & DEPIN ---
    {"ticker": "FET-USD", "nom": "ASI (ex-Fetch.ai)", "sector": "IA"},
    {"ticker": "RENDER-USD", "nom": "Render Network", "sector": "GPU Rendering"},
    {"ticker": "TAO-USD", "nom": "Bittensor", "sector": "IA - ML"},
    {"ticker": "AKT-USD", "nom": "Akash Network", "sector": "Cloud Computing"},
    {"ticker": "THETA-USD", "nom": "Theta", "sector": "Streaming / DePIN"},
    {"ticker": "AR-USD", "nom": "Arweave", "sector": "Decentralized Storage"},
    {"ticker": "FIL-USD", "nom": "Filecoin", "sector": "Decentralized Storage"},
    {"ticker": "LPT-USD", "nom": "Livepeer", "sector": "Video Infrastructure"},
    {"ticker": "HNT-USD", "nom": "Helium", "sector": "Wireless DePIN"},
    {"ticker": "GRT-USD", "nom": "The Graph", "sector": "Data Indexing"},
    {"ticker": "JASMY-USD", "nom": "JasmyCoin", "sector": "Data Privacy"},

    # --- ORACLES & INTEROPÉRABILITÉ ---
    {"ticker": "LINK-USD", "nom": "Chainlink", "sector": "Oracle"},
    {"ticker": "PYTH-USD", "nom": "Pyth Network", "sector": "Oracle"},
    {"ticker": "AXL-USD", "nom": "Axelar", "sector": "Interoperability"},
    {"ticker": "W-USD", "nom": "Wormhole", "sector": "Interoperability"},

    # --- DEFI & RWA ---
    {"ticker": "AAVE-USD", "nom": "Aave", "sector": "Lending"},
    {"ticker": "UNI-USD", "nom": "Uniswap", "sector": "DEX"},
    {"ticker": "MKR-USD", "nom": "Maker", "sector": "Stablecoin RWA"},
    {"ticker": "PENDLE-USD", "nom": "Pendle", "sector": "Yield Trading"},
    {"ticker": "ONDO-USD", "nom": "Ondo Finance", "sector": "RWA"},
    {"ticker": "JUP-USD", "nom": "Jupiter", "sector": "DEX Aggregator"},
    {"ticker": "LDO-USD", "nom": "Lido DAO", "sector": "Liquid Staking"},
    {"ticker": "ENA-USD", "nom": "Ethena", "sector": "Synthetic Dollar"},
    {"ticker": "RAY-USD", "nom": "Raydium", "sector": "Solana DeFi"},
    {"ticker": "SNX-USD", "nom": "Synthetix", "sector": "Derivatives"},
    {"ticker": "COMP-USD", "nom": "Compound", "sector": "Lending"},
    {"ticker": "CRV-USD", "nom": "Curve DAO", "sector": "Stablecoin DEX"},
    {"ticker": "GMX-USD", "nom": "GMX", "sector": "Perp DEX"},

    # --- GAMING & METAVERSE ---
    {"ticker": "BEAM-USD", "nom": "Beam", "sector": "Gaming Hub"},
    {"ticker": "SAND-USD", "nom": "The Sandbox", "sector": "Metaverse"},
    {"ticker": "MANA-USD", "nom": "Decentraland", "sector": "Metaverse"},
    {"ticker": "GALA-USD", "nom": "Gala Games", "sector": "Gaming"},
    {"ticker": "RON-USD", "nom": "Ronin", "sector": "Gaming L1"},
    {"ticker": "AXS-USD", "nom": "Axie Infinity", "sector": "Gaming"},

    # --- MEMECOINS ---
    {"ticker": "DOGE-USD", "nom": "Dogecoin", "sector": "Meme - PoW"},
    {"ticker": "SHIB-USD", "nom": "Shiba Inu", "sector": "Meme - Ecosystem"},
    {"ticker": "PEPE-USD", "nom": "Pepe", "sector": "Meme - Culture"},
    {"ticker": "WIF-USD", "nom": "dogwifhat", "sector": "Meme - Solana"},
    {"ticker": "FLOKI-USD", "nom": "Floki Inu", "sector": "Meme"},
    {"ticker": "BONK-USD", "nom": "Bonk", "sector": "Meme - Solana"},
    {"ticker": "POPCAT-USD", "nom": "Popcat", "sector": "Meme - Cat"},
    {"ticker": "BRETT-USD", "nom": "Brett", "sector": "Meme - Base"},

    # --- ECOSYSTÈME BITCOIN & PAIEMENTS ---
    {"ticker": "ORDI-USD", "nom": "ORDI", "sector": "Bitcoin Ordinals"},
    {"ticker": "XRP-USD", "nom": "Ripple", "sector": "Payments"},
    {"ticker": "LTC-USD", "nom": "Litecoin", "sector": "Payments - PoW"},
    {"ticker": "BCH-USD", "nom": "Bitcoin Cash", "sector": "Payments - PoW"},
    {"ticker": "XLM-USD", "nom": "Stellar", "sector": "Payments"},
    {"ticker": "VET-USD", "nom": "VeChain", "sector": "Supply Chain"},

    # --- TOP 100-150 COMPLÉMENTAIRE ---
    {"ticker": "QNT-USD", "nom": "Quant", "sector": "Enterprise Interop"},
    {"ticker": "ROSE-USD", "nom": "Oasis Network", "sector": "Privacy L1"},
    {"ticker": "KAVA-USD", "nom": "Kava", "sector": "DeFi Hub"},
    {"ticker": "WOO-USD", "nom": "WOO Network", "sector": "Exchange"},
    {"ticker": "GLMR-USD", "nom": "Moonbeam", "sector": "Polkadot EVM"},
    {"ticker": "ALT-USD", "nom": "AltLayer", "sector": "Rollups"},
    {"ticker": "DYM-USD", "nom": "Dymension", "sector": "Modular RollApps"},
    {"ticker": "ANKR-USD", "nom": "Ankr", "sector": "Infrastructure"},
    {"ticker": "ZIL-USD", "nom": "Zilliqa", "sector": "Sharding"},
    {"ticker": "FLOW-USD", "nom": "Flow", "sector": "NFT / Gaming"},
    {"ticker": "CHZ-USD", "nom": "Chiliz", "sector": "Sports"},
    {"ticker": "TRX-USD", "nom": "TRON", "sector": "Layer 1"},
    {"ticker": "XMR-USD", "nom": "Monero", "sector": "Privacy Coin"},
    {"ticker": "ZEC-USD", "nom": "Zcash", "sector": "Privacy Coin"},
    {"ticker": "BAT-USD", "nom": "Basic Attention Token", "sector": "AdTech"},
    {"ticker": "ENJ-USD", "nom": "Enjin Coin", "sector": "Gaming"},
    {"ticker": "SUSHI-USD", "nom": "SushiSwap", "sector": "DEX"},
    {"ticker": "1INCH-USD", "nom": "1inch Network", "sector": "Aggregator"},
    {"ticker": "CAKE-USD", "nom": "PancakeSwap", "sector": "DEX"},
    {"ticker": "ENS-USD", "nom": "ENS", "sector": "Identity"},
    {"ticker": "TWT-USD", "nom": "Trust Wallet", "sector": "Wallet"},
    {"ticker": "CELO-USD", "nom": "Celo", "sector": "Mobile L1"},
    {"ticker": "PAXG-USD", "nom": "PAX Gold", "sector": "Gold Backed"},
    {"ticker": "XDC-USD", "nom": "XDC Network", "sector": "Trade Finance"}
]
