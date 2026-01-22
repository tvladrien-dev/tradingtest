import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime

class NewsEngine:
    """
    Moteur de communication et d'intelligence externe.
    Gère les notifications push via ntfy.sh et le flux d'actualités Yahoo Finance.
    """
    
    def __init__(self):
        """Initialise les paramètres de connexion et headers."""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.base_url = "https://finance.yahoo.com/quote/"

    def get_news_for_ticker(self, ticker):
        """
        Scrape les dernières actualités pour un ticker spécifique sur Yahoo Finance.
        """
        news_list = []
        try:
            # Nettoyage du format ticker pour l'URL
            clean_ticker = ticker.strip().upper()
            url = f"{self.base_url}{clean_ticker}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logging.warning(f"Impossible de récupérer les news pour {ticker} (Code: {response.status_code})")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ciblage des éléments de flux d'actualités Yahoo
            articles = soup.find_all('li', {'class': 'stream-item'})
            
            for item in articles[:5]:
                title_tag = item.find('h3')
                link_tag = item.find('a')
                
                if title_tag and link_tag:
                    link = link_tag['href']
                    full_link = link if link.startswith('http') else f"https://finance.yahoo.com{link}"
                    
                    news_list.append({
                        "title": title_tag.text.strip(),
                        "link": full_link,
                        "source": "Yahoo Finance",
                        "date": datetime.now().strftime("%H:%M")
                    })
            
            return news_list

        except Exception as e:
            logging.error(f"Erreur lors du scraping des news pour {ticker} : {e}")
            return []

    def send_ntfy_alert(self, signal_data, topic):
        """
        Envoie une notification push ultra-détaillée via ntfy.sh.
        Inclus : Prix d'achat, Objectifs de vente, Stop Loss et Justification technique.
        """
        if not topic:
            logging.error("Échec notification : NTFY_TOPIC n'est pas configuré.")
            return False

        try:
            # Extraction sécurisée des données du signal
            ticker = signal_data.get('Ticker', 'Inconnu')
            price = signal_data.get('Close', 0.0)
            rsi = signal_data.get('RSI', 0.0)
            ema200 = signal_data.get('EMA200', 0.0)
            
            # --- CALCUL DES OBJECTIFS DE TRADING (GESTION DU RISQUE) ---
            # Objectif de gain (Take Profit) : +15%
            # Protection (Stop Loss) : -5%
            take_profit = round(price * 1.15, 2)
            stop_loss = round(price * 0.95, 2)
            potential_gain = "15.0%"

            # --- MISE EN FORME DU MESSAGE NTFY ---
            title = f"🎯 SIGNAL ALPHA DÉTECTÉ : {ticker}"
            
            message = (
                f"📊 ANALYSE QUANTITATIVE TERMINÉE\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔹 ACTIF : {ticker}\n"
                f"🔹 PRIX D'ENTRÉE : {price} €\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 OBJECTIFS DE SORTIE :\n"
                f"  └ 🚀 VENTE (Target) : {take_profit} €\n"
                f"  └ 📉 STOP LOSS : {stop_loss} €\n"
                f"  └ 📈 GAIN ESTIMÉ : +{potential_gain}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔍 INDICATEURS CLÉS :\n"
                f"  • RSI(14) : {round(rsi, 2)} (Zone Rebond)\n"
                f"  • Support EMA200 : {round(ema200, 2)} €\n"
                f"  • Tendance : BULLISH CONFIRMÉE\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"⏰ {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}"
            )

            # --- ENVOI DE LA REQUÊTE HTTP POST ---
            url = f"https://ntfy.sh/{topic}"
            
            response = requests.post(
                url,
                data=message.encode('utf-8'),
                headers={
                    "Title": title,
                    "Priority": "5", # Priorité Urgente (déclenche sonnerie/vibreur)
                    "Tags": "rocket,money_with_wings,chart_with_upwards_trend",
                    "Click": f"https://finance.yahoo.com/quote/{ticker}" # Ouvre la fiche action au clic
                },
                timeout=10
            )

            if response.status_code == 200:
                logging.info(f"Notification ntfy envoyée avec succès pour {ticker}.")
                return True
            else:
                logging.error(f"Erreur ntfy (Status: {response.status_code})")
                return False

        except Exception as e:
            logging.error(f"Erreur critique lors de l'envoi de l'alerte ntfy : {e}")
            return False
