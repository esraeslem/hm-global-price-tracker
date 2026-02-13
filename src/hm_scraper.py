"""
H&M Global Scraper - Multi-region price tracking with Playwright.

Uses headless browser to bypass anti-bot protection (403 errors).
Playwright launches a real Chrome browser that executes JavaScript,
making the scraper indistinguishable from a human visitor.

IMPORTANT: Run 'playwright install chromium' after pip install
"""

from playwright.sync_api import sync_playwright
import time
import random
import logging
from datetime import datetime


class HMScraper:
    """Scraper for H&M websites using Playwright headless browser."""
    
    # H&M regional sites
    REGIONS = {
        'tr': {
            'name': 'Turkey',
            'base_url': 'https://www2.hm.com/tr_tr',
            'currency': 'TRY',
            'language': 'tr_tr'
        },
        'us': {
            'name': 'United States',
            'base_url': 'https://www2.hm.com/en_us',
            'currency': 'USD',
            'language': 'en_us'
        },
        'uk': {
            'name': 'United Kingdom',
            'base_url': 'https://www2.hm.com/en_gb',
            'currency': 'GBP',
            'language': 'en_gb'
        },
        'de': {
            'name': 'Germany',
            'base_url': 'https://www2.hm.com/de_de',
            'currency': 'EUR',
            'language': 'de_de'
        },
        'se': {
            'name': 'Sweden',
            'base_url': 'https://www2.hm.com/sv_se',
            'currency': 'SEK',
            'language': 'sv_se'
        }
    }
    
    # Category paths (adjust based on actual H&M URLs)
    CATEGORIES = {
        'tr': ['/kadin/urunler/elbiseler.html'],
        'us': ['/women/products/dresses.html'],
        'uk': ['/ladies/products/dresses.html'],
        'de': ['/damen/produkte/kleider.html'],
        'se': ['/dam/produkter/klanningar.html'],
    }
    
    def __init__(self, region_code='tr'):
        """
        Initialize scraper for specific region.
        
        Args:
            region_code: Region code (tr, us, uk, de, se)
        """
        if region_code not in self.REGIONS:
            raise ValueError(f"Invalid region code: {region_code}")
            
        self.region_code = region_code
        self.region = self.REGIONS[region_code]
        self.base_url = self.region['base_url']
        self.currency = self.region['currency']
        
        # Logging
        self.logger = logging.getLogger(f"hm_scraper.{region_code}")
        self.logger.setLevel(logging.INFO)
        
        # Statistics
        self.stats = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'products_found': 0
        }
        
    def _extract_price(self, price_text):
        """
        Extract numeric price from text.
        
        H&M uses different formats:
        - Turkey: "299,99 TL"
        - US: "$29.99"
        - UK: "£29.99"  
        - Germany: "29,99 €"
        """
        if not price_text:
            return None
            
        try:
            # Remove currency symbols and text
            cleaned = price_text.strip()
            cleaned = cleaned.replace('TL', '').replace('₺', '')
            cleaned = cleaned.replace('$', '').replace('£', '').replace('€', '')
            cleaned = cleaned.replace('SEK', '').replace('kr', '')
            cleaned = cleaned.strip()
            
            # Handle different decimal separators
            # European format: 1.299,99 -> 1299.99
            if ',' in cleaned and '.' in cleaned:
                cleaned = cleaned.replace('.', '').replace(',', '.')
            # European comma: 299,99 -> 299.99
            elif ',' in cleaned:
                cleaned = cleaned.replace(',', '.')
            # US format with comma thousands: 1,299.99 -> 1299.99
            else:
                cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
            
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"Failed to parse price '{price_text}': {e}")
            return None
    
    def scrape_category(self, category_path, max_products=30):
        """
        Scrape products from a category page using Playwright.
        
        Args:
            category_path: Category URL path
            max_products: Maximum products to scrape
            
        Returns:
            List of product dictionaries
        """
        url = self.base_url + category_path
        
        self.logger.info(f"🌍 Launching browser for {self.region['name']}...")
        print(f"🌍 Scraping {self.region['name']} from {url}...")
        
        products = []
        
        with sync_playwright() as p:
            # Launch headless Chrome
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # Create context with realistic user agent
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale=self.region['language'].replace('_', '-')
            )
            
            page = context.new_page()
            
            try:
                # Navigate to page
                self.stats['requests'] += 1
                page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Wait for product grid to load
                try:
                    page.wait_for_selector('li.product-item, article.hm-product-item', timeout=15000)
                except:
                    self.logger.warning("Timeout waiting for products. Page structure may have changed.")
                    self.stats['failures'] += 1
                    return products
                
                # Scroll to trigger lazy loading
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Find product items (try multiple selectors)
                product_elements = page.query_selector_all('li.product-item')
                
                if not product_elements:
                    product_elements = page.query_selector_all('article.hm-product-item')
                
                if not product_elements:
                    # Try even more generic selector
                    product_elements = page.query_selector_all('[data-articlecode]')
                
                print(f"   → Found {len(product_elements)} products on page")
                
                # Extract data from each product
                for i, item in enumerate(product_elements[:max_products]):
                    try:
                        # Get article tag (might be the item itself or nested)
                        article = item.query_selector('article')
                        if not article:
                            article = item
                        
                        # Extract product code (H&M's global identifier)
                        product_code = article.get_attribute('data-articlecode')
                        if not product_code:
                            product_code = item.get_attribute('data-articlecode')
                        
                        if not product_code:
                            continue  # Skip if no code - can't track across regions
                        
                        # Extract product name
                        name_elem = item.query_selector('.item-heading, h3.link, a.link')
                        product_name = name_elem.inner_text().strip() if name_elem else "Unknown Product"
                        
                        # Extract price
                        price_elem = item.query_selector('.price, .ae-currency-price, [class*="price"]')
                        price_text = price_elem.inner_text().strip() if price_elem else None
                        price = self._extract_price(price_text)
                        
                        if not price:
                            continue  # Skip if no valid price
                        
                        # Extract original price (if discounted)
                        original_elem = item.query_selector('.price-old, .old-price, [class*="original"]')
                        original_price = None
                        if original_elem:
                            original_price = self._extract_price(original_elem.inner_text())
                        
                        # Calculate discount
                        discount = 0
                        if original_price and price and original_price > price:
                            discount = ((original_price - price) / original_price) * 100
                        
                        # Check stock (basic check - if on listing page, likely in stock)
                        in_stock = True
                        
                        products.append({
                            'product_code': product_code,
                            'product_name': product_name,
                            'product_url': url,  # Category URL
                            'price_local': price,
                            'original_price_local': original_price,
                            'discount_percentage': round(discount, 2),
                            'currency': self.currency,
                            'region_code': self.region_code,
                            'in_stock': in_stock
                        })
                        
                        self.stats['products_found'] += 1
                        
                    except Exception as e:
                        self.logger.debug(f"Error parsing product {i}: {e}")
                        continue
                
                self.stats['successes'] += 1
                self.logger.info(f"✓ Successfully scraped {len(products)} products")
                
            except Exception as e:
                self.stats['failures'] += 1
                self.logger.error(f"Error during scraping: {e}")
                
            finally:
                browser.close()
        
        return products
    
    def print_stats(self):
        """Print scraping statistics."""
        print(f"\n{'='*60}")
        print(f"H&M {self.region['name']} Scraping Statistics")
        print(f"{'='*60}")
        print(f"Total Requests:    {self.stats['requests']}")
        print(f"Successful:        {self.stats['successes']}")
        print(f"Failed:            {self.stats['failures']}")
        print(f"Products Found:    {self.stats['products_found']}")
        success_rate = (self.stats['successes'] / self.stats['requests'] * 100 
                       if self.stats['requests'] > 0 else 0)
        print(f"Success Rate:      {success_rate:.1f}%")
        print(f"{'='*60}\n")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)


if __name__ == "__main__":
    """Test the scraper with Playwright."""
    
    import os
    os.makedirs('logs', exist_ok=True)
    
    print("\n" + "="*70)
    print("H&M Global Scraper Test (Playwright)")
    print("="*70 + "\n")
    
    print("✅ Using Playwright headless browser to bypass 403 errors\n")
    
    # Test with Turkey region
    scraper = HMScraper(region_code='tr')
    
    print(f"Testing {scraper.region['name']} ({scraper.currency})\n")
    
    # Test category scraping
    category = '/kadin/urunler/elbiseler.html'
    products = scraper.scrape_category(category, max_products=5)
    
    if products:
        print(f"\n✅ Successfully scraped {len(products)} products")
        print("\nFirst product:")
        for key, value in products[0].items():
            print(f"  {key}: {value}")
    else:
        print("\n⚠️ No products found")
        print("If you see 403 errors, make sure you ran: playwright install chromium")
    
    scraper.print_stats()
