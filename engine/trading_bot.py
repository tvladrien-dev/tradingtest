# Ajoute cette méthode à ta classe TradingBotPEA existante
def check_new_alerts(self):
    """Compare l'état actuel avec le dernier signal pour générer une alerte unique."""
    if self.signals.empty:
        return []
    
    last_state = self.get_last_state()
    alerts = []
    
    for _, row in last_state.iterrows():
        if row['Signal'] == 1:
            alerts.append({"type": "ACHAT", "nom": row['Nom'], "prix": row['Close'], "ticker": row['Ticker']})
        elif row['Signal'] == -1:
            alerts.append({"type": "VENTE", "nom": row['Nom'], "prix": row['Close'], "ticker": row['Ticker']})
            
    return alerts
