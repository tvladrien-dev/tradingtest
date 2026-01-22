import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import urllib.parse

class NewsEngine:
    """
    Moteur d'agrégation et d'analyse de sentiment pour flux financiers.
    Scrape et traite les actualités d'Euronext et des sources majeures.
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.positive_keywords = ['hausse', 'profit', 'croissance', 'dividende', 'contrat', 'rachat', 'excédent', 'reprise', 'buy', 'outperform']
        self.negative_keywords = ['baisse', 'perte', 'alerte', 'déficit', 'chute', 'inflation', 'procès', 'amende', 'sell', 'underperform']

    def get_news_for_ticker(self, company_name):
        """
        Récupère les dernières actualités pour une entreprise spécifique via Boursier.com / Google News.
        """
        news_list = []
        try:
            # Encodage du nom pour l'URL
            query = urllib.parse.quote(f"{company_name} bourse")
            url = f"https://www.google.com/search?q={query}&tbm=nws"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction des blocs d'actualités (Sélecteurs génériques pour Google News)
            articles = soup.select('div.SoR63b') or soup.select('a.WlyYGe') or soup.select('div.n0vPhd')

            for art in articles[:5]: # Top 5 news
                title_elem = art.select_one('div[role="heading"]') or art.select_one('h3')
                link_elem = art.find('a', href=True)
                source_elem = art.select_one('div.OSrE9b') or art.select_one('span')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    link = link_elem['href']
                    source = source_elem.get_text() if source_elem else "Source inconnue"
                    
                    # Nettoyage des liens Google Redirect
                    if link.startswith('/url?q='):
                        link = link.split('/url?q=')[1].split('&')[0]

                    news_list.append({
                        "title": title,
                        "link": link,
                        "source": source,
                        "date": datetime.now().strftime("%H:%M")
                    })

            return news_list

        except Exception as e:
            logging.error(f"Erreur NewsEngine pour {company_name}: {e}")
            return []

    def analyze_sentiment(self, news_items):
        """
        Analyse simplifiée du sentiment basée sur un dictionnaire financier.
        Retourne un tag HTML stylisé pour l'affichage Streamlit.
        """
        if not news_items:
            return "⚪ NEUTRE"

        score = 0
        text_blob = " ".join([item['title'].lower() for item in news_items])

        for word in self.positive_keywords:
            if word in text_blob:
                score += 1
        
        for word in self.negative_keywords:
            if word in text_blob:
                score -= 1

        if score > 0:
            return "🟢 POSITIF"
        elif score < 0:
            return "🔴 NÉGATIF"
        else:
            return "⚪ NEUTRE"

    def get_macro_sentiment(self):
        """
        Analyse le sentiment global du marché (Europe/Euronext).
        """
        macro_news = self.get_news_for_ticker("CAC 40")
        return self.analyze_sentiment(macro_news)
