import yfinance as yf
import pandas as pd
import numpy as np
import ta
import logging
import time
from datetime import datetime

# CONFIGURATION DU LOGGING
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("TradingBotPEA")

class TradingBotPEA:
    def __init__(self):
        """Initialisation de l'univers 100% ELIGIBLE PEA."""
        self.universe_data = [
            # --- FRANCE : CAC 40 & SBF 120 ---
            {"ticker": "MC.PA", "nom": "LVMH", "sector": "Luxe"},
            {"ticker": "RMS.PA", "nom": "Hermès", "sector": "Luxe"},
            {"ticker": "KER.PA", "nom": "Kering", "sector": "Luxe"},
            {"ticker": "OR.PA", "nom": "L'Oréal", "sector": "Consommation"},
            {"ticker": "BN.PA", "nom": "Danone", "sector": "Consommation"},
            {"ticker": "CA.PA", "nom": "Carrefour", "sector": "Distribution"},
            {"ticker": "RI.PA", "nom": "Pernod Ricard", "sector": "Consommation"},
            {"ticker": "AIR.PA", "nom": "Airbus", "sector": "Aéronautique"},
            {"ticker": "SAF.PA", "nom": "Safran", "sector": "Aéronautique"},
            {"ticker": "HO.PA", "nom": "Thales", "sector": "Défense"},
            {"ticker": "AM.PA", "nom": "Dassault Aviation", "sector": "Défense"},
            {"ticker": "AI.PA", "nom": "Air Liquide", "sector": "Industrie"},
            {"ticker": "SU.PA", "nom": "Schneider Electric", "sector": "Industrie"},
            {"ticker": "LR.PA", "nom": "Legrand", "sector": "Industrie"},
            {"ticker": "DG.PA", "nom": "Vinci", "sector": "BTP"},
            {"ticker": "SGO.PA", "nom": "Saint-Gobain", "sector": "BTP"},
            {"ticker": "EN.PA", "nom": "Eiffage", "sector": "BTP"},
            {"ticker": "ML.PA", "nom": "Michelin", "sector": "Automobile"},
            {"ticker": "RNO.PA", "nom": "Renault", "sector": "Automobile"},
            {"ticker": "STLAP.PA", "nom": "Stellantis", "sector": "Automobile"},
            {"ticker": "SAN.PA", "nom": "Sanofi", "sector": "Santé"},
            {"ticker": "EL.PA", "nom": "EssilorLuxottica", "sector": "Santé"},
            {"ticker": "DIM.PA", "nom": "Sartorius Stedim", "sector": "Santé"},
            {"ticker": "BIM.PA", "nom": "BioMérieux", "sector": "Santé"},
            {"ticker": "IPS.PA", "nom": "Ipsen", "sector": "Santé"},
            {"ticker": "BNP.PA", "nom": "BNP Paribas", "sector": "Finance"},
            {"ticker": "GLE.PA", "nom": "Société Générale", "sector": "Finance"},
            {"ticker": "ACA.PA", "nom": "Crédit Agricole", "sector": "Finance"},
            {"ticker": "CS.PA", "nom": "AXA", "sector": "Finance"},
            {"ticker": "AMUN.PA", "nom": "Amundi", "sector": "Finance"},
            {"ticker": "TTE.PA", "nom": "TotalEnergies", "sector": "Énergie"},
            {"ticker": "ENGI.PA", "nom": "Engie", "sector": "Énergie"},
            {"ticker": "VIE.PA", "nom": "Veolia", "sector": "Services"},
            {"ticker": "ORA.PA", "nom": "Orange", "sector": "Télécoms"},
            {"ticker": "PUB.PA", "nom": "Publicis", "sector": "Médias"},
            {"ticker": "VIV.PA", "nom": "Vivendi", "sector": "Médias"},
            {"ticker": "URW.PA", "nom": "Unibail-Rodamco", "sector": "Immobilier"},
            {"ticker": "GFC.PA", "nom": "Gecina", "sector": "Immobilier"},
            {"ticker": "COV.PA", "nom": "Covivio", "sector": "Immobilier"},
            {"ticker": "DSY.PA", "nom": "Dassault Systèmes", "sector": "Technologie"},
            {"ticker": "CAP.PA", "nom": "Capgemini", "sector": "Technologie"},
            {"ticker": "SOP.PA", "nom": "Sopra Steria", "sector": "Technologie"},
            {"ticker": "ATE.PA", "nom": "Alten", "sector": "Technologie"},
            {"ticker": "SOI.PA", "nom": "Soitec", "sector": "Technologie"},
            {"ticker": "WLN.PA", "nom": "Worldline", "sector": "Technologie"},
            {"ticker": "OVH.PA", "nom": "OVHcloud", "sector": "Technologie"},
            {"ticker": "STMPA.PA", "nom": "STMicroelectronics", "sector": "Technologie"},
            {"ticker": "UBI.PA", "nom": "Ubisoft", "sector": "Technologie"},
            {"ticker": "VLA.PA", "nom": "Valneva", "sector": "Santé"},
            {"ticker": "VIRP.PA", "nom": "Virbac", "sector": "Santé"},
            {"ticker": "VETO.PA", "nom": "Vetoquinol", "sector": "Santé"},
            {"ticker": "LNA.PA", "nom": "LNA Santé", "sector": "Santé"},
            {"ticker": "EMEIS.PA", "nom": "Emeis", "sector": "Santé"},
            {"ticker": "RCO.PA", "nom": "Rémy Cointreau", "sector": "Consommation"},
            {"ticker": "ITP.PA", "nom": "Interparfums", "sector": "Consommation"},
            {"ticker": "SK.PA", "nom": "SEB", "sector": "Consommation"},
            {"ticker": "SMCP.PA", "nom": "SMCP", "sector": "Luxe"},
            {"ticker": "GET.PA", "nom": "Getlink", "sector": "Transport"},
            {"ticker": "IDL.PA", "nom": "ID Logistics", "sector": "Transport"},
            {"ticker": "SPIE.PA", "nom": "Spie", "sector": "Services"},
            {"ticker": "VK.PA", "nom": "Vallourec", "sector": "Industrie"},
            {"ticker": "NEX.PA", "nom": "Nexans", "sector": "Industrie"},
            {"ticker": "ERA.PA", "nom": "Eramet", "sector": "Mines"},
            {"ticker": "BOL.PA", "nom": "Bolloré", "sector": "Holding"},
            {"ticker": "MF.PA", "nom": "Wendel", "sector": "Finance"},
            {"ticker": "COFA.PA", "nom": "Coface", "sector": "Finance"},
            {"ticker": "SCR.PA", "nom": "SCOR", "sector": "Finance"},
            {"ticker": "TKO.PA", "nom": "Tikehau Capital", "sector": "Finance"},
            {"ticker": "LI.PA", "nom": "Klepierre", "sector": "Immobilier"},
            {"ticker": "DEC.PA", "nom": "JCDecaux", "sector": "Médias"},
            {"ticker": "TFI.PA", "nom": "TF1", "sector": "Médias"},
            {"ticker": "MMT.PA", "nom": "M6", "sector": "Médias"},
            {"ticker": "SESG.PA", "nom": "SES", "sector": "Télécoms"},
            {"ticker": "FDJ.PA", "nom": "Française des Jeux", "sector": "Loisirs"},
            {"ticker": "BEN.PA", "nom": "Bénéteau", "sector": "Loisirs"},
            {"ticker": "TRIA.PA", "nom": "Trigano", "sector": "Loisirs"},
            {"ticker": "EXO.PA", "nom": "Exel Industries", "sector": "Industrie"},
            {"ticker": "MERY.PA", "nom": "Mercialys", "sector": "Immobilier"},
            {"ticker": "NXI.PA", "nom": "Nexity", "sector": "Immobilier"},
            {"ticker": "SAP.DE", "nom": "SAP", "sector": "Technologie"},
            {"ticker": "SIE.DE", "nom": "Siemens", "sector": "Industrie"},
            {"ticker": "DTE.DE", "nom": "Deutsche Telekom", "sector": "Télécoms"},
            {"ticker": "ALV.DE", "nom": "Allianz", "sector": "Finance"},
            {"ticker": "MUV2.DE", "nom": "Munich Re", "sector": "Finance"},
            {"ticker": "BAS.DE", "nom": "BASF", "sector": "Chimie"},
            {"ticker": "BAYN.DE", "nom": "Bayer", "sector": "Santé"},
            {"ticker": "BMW.DE", "nom": "BMW", "sector": "Automobile"},
            {"ticker": "MBG.DE", "nom": "Mercedes-Benz", "sector": "Automobile"},
            {"ticker": "VOW3.DE", "nom": "Volkswagen", "sector": "Automobile"},
            {"ticker": "ADS.DE", "nom": "Adidas", "sector": "Consommation"},
            {"ticker": "IFX.DE", "nom": "Infineon", "sector": "Technologie"},
            {"ticker": "DHL.DE", "nom": "DHL Group", "sector": "Transport"},
            {"ticker": "RWE.DE", "nom": "RWE", "sector": "Énergie"},
            {"ticker": "EOAN.DE", "nom": "E.ON", "sector": "Énergie"},
            {"ticker": "DBK.DE", "nom": "Deutsche Bank", "sector": "Finance"},
            {"ticker": "CBK.DE", "nom": "Commerzbank", "sector": "Finance"},
            {"ticker": "HEI.DE", "nom": "Heidelberg Materials", "sector": "BTP"},
            {"ticker": "CON.DE", "nom": "Continental", "sector": "Automobile"},
            {"ticker": "RHM.DE", "nom": "Rheinmetall", "sector": "Défense"},
            {"ticker": "MTX.DE", "nom": "MTU Aero Engines", "sector": "Aéronautique"},
            {"ticker": "P911.DE", "nom": "Porsche AG", "sector": "Automobile"},
            {"ticker": "SY1.DE", "nom": "Symrise", "sector": "Chimie"},
            {"ticker": "BEI.DE", "nom": "Beiersdorf", "sector": "Consommation"},
            {"ticker": "HEN3.DE", "nom": "Henkel", "sector": "Consommation"},
            {"ticker": "ZAL.DE", "nom": "Zalando", "sector": "Consommation"},
            {"ticker": "HFG.DE", "nom": "HelloFresh", "sector": "Consommation"},
            {"ticker": "LEG.DE", "nom": "LEG Immobilien", "sector": "Immobilier"},
            {"ticker": "VNA.DE", "nom": "Vonovia", "sector": "Immobilier"},
            {"ticker": "FME.DE", "nom": "Fresenius Medical Care", "sector": "Santé"},
            {"ticker": "FRE.DE", "nom": "Fresenius SE", "sector": "Santé"},
            {"ticker": "QIA.DE", "nom": "Qiagen", "sector": "Santé"},
            {"ticker": "VAR1.DE", "nom": "Varta", "sector": "Industrie"},
            {"ticker": "SDF.DE", "nom": "K+S", "sector": "Chimie"},
            {"ticker": "ASML.AS", "nom": "ASML", "sector": "Technologie"},
            {"ticker": "ADYEN.AS", "nom": "Adyen", "sector": "Technologie"},
            {"ticker": "PRX.AS", "nom": "Prosus", "sector": "Technologie"},
            {"ticker": "INGA.AS", "nom": "ING Group", "sector": "Finance"},
            {"ticker": "KPN.AS", "nom": "KPN", "sector": "Télécoms"},
            {"ticker": "AD.AS", "nom": "Ahold Delhaize", "sector": "Distribution"},
            {"ticker": "HEIA.AS", "nom": "Heineken", "sector": "Consommation"},
            {"ticker": "UMG.AS", "nom": "Universal Music", "sector": "Médias"},
            {"ticker": "DSM.AS", "nom": "DSM-Firmenich", "sector": "Chimie"},
            {"ticker": "AKZA.AS", "nom": "Akzo Nobel", "sector": "Chimie"},
            {"ticker": "PHIA.AS", "nom": "Philips", "sector": "Santé"},
            {"ticker": "NN.AS", "nom": "NN Group", "sector": "Finance"},
            {"ticker": "REN.AS", "nom": "Reed Elsevier", "sector": "Médias"},
            {"ticker": "ISP.MI", "nom": "Intesa Sanpaolo", "sector": "Finance"},
            {"ticker": "UCG.MI", "nom": "Unicredit", "sector": "Finance"},
            {"ticker": "ENI.MI", "nom": "ENI", "sector": "Énergie"},
            {"ticker": "ENEL.MI", "nom": "Enel", "sector": "Énergie"},
            {"ticker": "RACE.MI", "nom": "Ferrari", "sector": "Luxe"},
            {"ticker": "MONC.MI", "nom": "Moncler", "sector": "Luxe"},
            {"ticker": "GEN.MI", "nom": "Generali", "sector": "Finance"},
            {"ticker": "PRY.MI", "nom": "Prysmian", "sector": "Industrie"},
            {"ticker": "STM.MI", "nom": "STMicroelectronics (Italy)", "sector": "Technologie"},
            {"ticker": "SRG.MI", "nom": "Snam", "sector": "Services"},
            {"ticker": "TRN.MI", "nom": "Terna", "sector": "Services"},
            {"ticker": "PIRC.MI", "nom": "Pirelli", "sector": "Automobile"},
            {"ticker": "LDO.MI", "nom": "Leonardo", "sector": "Défense"},
            {"ticker": "SAN.MC", "nom": "Santander", "sector": "Finance"},
            {"ticker": "BBVA.MC", "nom": "BBVA", "sector": "Finance"},
            {"ticker": "ITX.MC", "nom": "Inditex", "sector": "Luxe"},
            {"ticker": "IBE.MC", "nom": "Iberdrola", "sector": "Énergie"},
            {"ticker": "REP.MC", "nom": "Repsol", "sector": "Énergie"},
            {"ticker": "TEF.MC", "nom": "Telefonica", "sector": "Télécoms"},
            {"ticker": "AMS.MC", "nom": "Amadeus", "sector": "Technologie"},
            {"ticker": "FER.MC", "nom": "Ferrovial", "sector": "Industrie"},
            {"ticker": "GRF.MC", "nom": "Grifols", "sector": "Santé"},
            {"ticker": "IDR.MC", "nom": "Indra Sistemas", "sector": "Technologie"},
            {"ticker": "CABK.MC", "nom": "Caixabank", "sector": "Finance"},
            {"ticker": "ABI.BR", "nom": "AB InBev", "sector": "Consommation"},
            {"ticker": "KBC.BR", "nom": "KBC Group", "sector": "Finance"},
            {"ticker": "UCB.BR", "nom": "UCB", "sector": "Santé"},
            {"ticker": "SOLB.BR", "nom": "Solvay", "sector": "Chimie"},
            {"ticker": "UMIC.BR", "nom": "Umicore", "sector": "Chimie"},
            {"ticker": "ACKB.BR", "nom": "Ackermans", "sector": "Holding"},
            {"ticker": "WDP.BR", "nom": "WDP", "sector": "Immobilier"},
            {"ticker": "MT.AS", "nom": "ArcelorMittal", "sector": "Acier"},
            {"ticker": "NOKIA.HE", "nom": "Nokia (FI)", "sector": "Technologie"},
            {"ticker": "UPM.HE", "nom": "UPM-Kymmene (FI)", "sector": "Industrie"},
            {"ticker": "NESTE.HE", "nom": "Neste (FI)", "sector": "Énergie"},
            {"ticker": "SAMPO.HE", "nom": "Sampo (FI)", "sector": "Finance"},
            {"ticker": "VOLVB.ST", "nom": "Volvo Group (SE)", "sector": "Industrie"},
            {"ticker": "ERICB.ST", "nom": "Ericsson (SE)", "sector": "Technologie"},
            {"ticker": "HM-B.ST", "nom": "H&M (SE)", "sector": "Consommation"},
            {"ticker": "ASSAB.ST", "nom": "Assa Abloy (SE)", "sector": "Industrie"},
            {"ticker": "EPI-B.ST", "nom": "Epiroc (SE)", "sector": "Industrie"},
            {"ticker": "SAND.ST", "nom": "Sandvik (SE)", "sector": "Industrie"},
            {"ticker": "SKFB.ST", "nom": "SKF (SE)", "sector": "Industrie"},
            {"ticker": "ORSTED.CO", "nom": "Orsted (DK)", "sector": "Énergie"},
            {"ticker": "MAERSK-B.CO", "nom": "Maersk (DK)", "sector": "Transport"},
            {"ticker": "DSV.CO", "nom": "DSV (DK)", "sector": "Transport"},
            {"ticker": "NOVO-B.CO", "nom": "Novo Nordisk (DK)", "sector": "Santé"},
            {"ticker": "EDP.LS", "nom": "EDP", "sector": "Énergie"},
            {"ticker": "GALP.LS", "nom": "Galp Energia", "sector": "Énergie"},
            {"ticker": "JMT.LS", "nom": "Jerónimo Martins", "sector": "Distribution"},
            {"ticker": "EBS.VI", "nom": "Erste Group (AT)", "sector": "Finance"},
            {"ticker": "OMV.VI", "nom": "OMV (AT)", "sector": "Énergie"}
        ]
        self.data = {}
        self.signals = pd.DataFrame()

    def download_data(self, period="3y", interval="1d"):
        success_count = 0
        for item in self.universe_data:
            ticker = item["ticker"]
            try:
                df = yf.download(ticker, period=period, interval=interval, progress=False, timeout=15)
                if not df.empty and len(df) > 200:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    df['Final_Close'] = df['Adj Close'] if 'Adj Close' in df.columns else df['Close']
                    self.data[ticker] = df
                    success_count += 1
            except Exception as e:
                logger.error(f"Erreur {ticker}: {e}")
        logger.info(f"Synchronisation: {success_count} actifs.")

    def compute_indicators(self, df):
        if df.empty or len(df) < 200: return df
        df['EMA200'] = ta.trend.EMAIndicator(close=df['Final_Close'], window=200).ema_indicator()
        df['RSI'] = ta.momentum.RSIIndicator(close=df['Final_Close'], window=14).rsi()
        df['ATR'] = ta.volatility.AverageTrueRange(high=df['High'], low=df['Low'], close=df['Final_Close'], window=14).average_true_range()
        stoch = ta.momentum.StochasticOscillator(high=df['High'], low=df['Low'], close=df['Final_Close'], window=14)
        df['Stoch_K'] = stoch.stoch()
        df['Stoch_D'] = stoch.stoch_signal()
        df['Close'] = df['Final_Close']
        df['RSI_Prev'] = df['RSI'].shift(1)
        df['Stoch_K_Prev'] = df['Stoch_K'].shift(1)
        df['Stoch_D_Prev'] = df['Stoch_D'].shift(1)
        return df

    def generate_elite_signals(self):
        all_results = []
        for ticker in self.data:
            try:
                df_calc = self.compute_indicators(self.data[ticker].copy())
                meta = next((x for x in self.universe_data if x["ticker"] == ticker), None)
                df_calc['Signal'] = 0
                
                df_calc['Vol_Moy'] = df_calc['Volume'].rolling(window=20).mean()
                volume_ok = df_calc['Volume'] > (df_calc['Vol_Moy'] * 0.7)

                buy_cond = (
                    (df_calc['Close'] > df_calc['EMA200']) & (df_calc['RSI'] < 48) & 
                    (df_calc['Stoch_K'] > df_calc['Stoch_D']) & (df_calc['Stoch_K_Prev'] <= df_calc['Stoch_D_Prev']) &
                    (df_calc['Stoch_K'] < 35) & volume_ok
                )
                sell_cond = (df_calc['RSI'] > 78) | ((df_calc['Stoch_K'] < df_calc['Stoch_D']) & (df_calc['Stoch_K'] > 82))
                
                df_calc.loc[buy_cond, 'Signal'] = 1
                df_calc.loc[sell_cond, 'Signal'] = -1
                
                last_row = df_calc.iloc[-1]
                p_close = float(last_row['Close'])
                p_atr = float(last_row['ATR'])
                
                status_clr = "#00ff99" if last_row['Signal'] == 1 else ("#ff4b4b" if last_row['Signal'] == -1 else "#8b949e")
                status_txt = "🟢 BUY" if last_row['Signal'] == 1 else ("🔴 SELL" if last_row['Signal'] == -1 else "⚪ NEUTRE")

                html = f"""<div style='border-left:4px solid {status_clr}; padding-left:10px;'>
                <b>Prix:</b> {p_close:.2f}€ | <b>Cible:</b> {p_close*0.992:.2f}€<br>
                <b>RSI:</b> {last_row['RSI']:.1f} | <span style='color:{status_clr}'>{status_txt}</span></div>"""

                df_calc['Ticker'], df_calc['Nom'], df_calc['Alpha_HTML'] = ticker, meta['nom'], html
                all_results.append(df_calc.reset_index())
            except: continue
        if all_results: self.signals = pd.concat(all_results, ignore_index=True)
        return self.signals

    def get_last_state(self):
        return self.signals.sort_values('Date').groupby('Ticker').last().reset_index() if not self.signals.empty else pd.DataFrame()

    def get_market_thermometer(self):
        if self.signals.empty: return {"status": "Scan..."}
        last = self.get_last_state()
        ob = (len(last[last['RSI'] > 70]) / len(last)) * 100
        os = (len(last[last['RSI'] < 35]) / len(last)) * 100
        return {"overbought_pct": ob, "oversold_pct": os, "status": "🔥 CHAUD" if ob > 20 else "🟢 SAIN"}
