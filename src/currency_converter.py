from forex_python.converter import CurrencyRates
import datetime

class CurrencyConverter:
    def __init__(self):
        self.c = CurrencyRates()
        # Fallback rates in case API fails (Approximate values)
        self.fallback_rates = {
            'TRY': 0.028,  # 1 TRY = 0.028 USD
            'EUR': 1.08,   # 1 EUR = 1.08 USD
            'GBP': 1.26,   # 1 GBP = 1.26 USD
            'SEK': 0.096,  # 1 SEK = 0.096 USD
            'USD': 1.0
        }

    def convert_to_usd(self, amount, currency):
        if currency == 'USD':
            return amount
        try:
            # Try live rate
            rate = self.c.get_rate(currency, 'USD')
            return amount * rate
        except:
            # Use fallback if offline
            return amount * self.fallback_rates.get(currency, 0)
