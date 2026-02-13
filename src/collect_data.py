import sqlite3
from hm_scraper import HMScraper
from currency_converter import CurrencyConverter
from database import DB_PATH, init_db

def save_data(data_list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    converter = CurrencyConverter()

    for item in data_list:
        # 1. Insert Product if not exists
        c.execute('''
            INSERT OR IGNORE INTO products (article_code, name, category)
            VALUES (?, ?, ?)
        ''', (item['article_code'], item['name'], 'Dresses'))

        # 2. Convert Price to USD
        usd_price = converter.convert_to_usd(item['price'], item['currency'])

        # 3. Insert Price Record
        c.execute('''
            INSERT INTO prices (article_code, region, price_original, currency, price_in_usd)
            VALUES (?, ?, ?, ?, ?)
        ''', (item['article_code'], item['region'], item['price'], item['currency'], usd_price))
    
    conn.commit()
    conn.close()
    print(f"✅ Saved {len(data_list)} items to database.")

def main():
    init_db()
    scraper = HMScraper()
    
    # Define which regions to scrape
    target_regions = ['tr', 'us', 'de', 'gb']
    
    for region in target_regions:
        data = scraper.scrape_region(region)
        if data:
            save_data(data)
        else:
            print(f"⚠️ No data found for {region}")

if __name__ == "__main__":
    main()
