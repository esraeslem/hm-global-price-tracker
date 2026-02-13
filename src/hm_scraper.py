import requests
from bs4 import BeautifulSoup
import time
import random

class HMScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        # Define regional URLs
        self.regions = {
            'tr': {'url': 'https://www2.hm.com/tr_tr/kadin/urunler/elbiseler.html', 'currency': 'TRY'},
            'us': {'url': 'https://www2.hm.com/en_us/women/products/dresses.html', 'currency': 'USD'},
            'de': {'url': 'https://www2.hm.com/de_de/damen/produkte/kleider.html', 'currency': 'EUR'},
            'gb': {'url': 'https://www2.hm.com/en_gb/ladies/shop-by-product/dresses.html', 'currency': 'GBP'}
        }

    def scrape_region(self, region_code):
        if region_code not in self.regions:
            print(f"Region {region_code} not found.")
            return []

        url = self.regions[region_code]['url']
        print(f"🌍 Scraping {region_code.upper()} from {url}...")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = []
            # H&M usually uses 'article' tag for products. 
            # INSPECT ELEMENT ON WEBSITE TO VERIFY THESE CLASSES!
            items = soup.find_all('article', class_='hm-product-item')
            
            for item in items[:10]: # Limit to 10 for testing
                try:
                    name = item.find('h3', class_='item-heading').text.strip()
                    article_code = item.get('data-articlecode')
                    price_text = item.find('span', class_='price').text.strip()
                    
                    # Clean price (remove currency symbols)
                    price_val = float(''.join(filter(lambda x: x.isdigit() or x == '.' or x == ',', price_text)).replace(',', '.'))
                    
                    products.append({
                        'article_code': article_code,
                        'name': name,
                        'price': price_val,
                        'currency': self.regions[region_code]['currency'],
                        'region': region_code
                    })
                except AttributeError:
                    continue # Skip if info missing
                    
            return products
            
        except Exception as e:
            print(f"❌ Error scraping {region_code}: {e}")
            return []

if __name__ == "__main__":
    scraper = HMScraper()
    data = scraper.scrape_region('tr')
    print(f"Found {len(data)} items in Turkey.")
