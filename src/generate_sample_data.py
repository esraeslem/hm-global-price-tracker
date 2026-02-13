"""
Generate realistic sample H&M data for demonstration.

This creates a complete dataset showing:
- Price differences across regions (purchasing power parity)
- Seasonal discounts
- Multi-region product availability
- Currency conversions
"""

import sqlite3
import random
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from database import Database
from currency_converter import CurrencyConverter


class SampleDataGenerator:
    """Generate realistic H&M sample data."""
    
    # Sample product names by category
    PRODUCTS = {
        'Dresses': [
            'Patterned Wrap Dress',
            'Ribbed Jersey Dress',
            'Lace-trimmed Dress',
            'Short Puff-sleeved Dress',
            'Long Sleeve Maxi Dress',
            'Tie-detail Mini Dress',
            'Smocked Cotton Dress',
            'Pleated Midi Dress',
            'Knit Sweater Dress',
            'Satin Slip Dress',
        ],
        'Tops': [
            'Oversized T-shirt',
            'Ribbed Tank Top',
            'Puff-sleeved Blouse',
            'Fitted Crop Top',
            'Cotton Shirt',
            'Silk Camisole',
            'Knit Cardigan',
            'Denim Jacket',
            'Hooded Sweatshirt',
            'Turtleneck Sweater',
        ],
        'Bottoms': [
            'Slim Fit Jeans',
            'Wide Leg Trousers',
            'Joggers',
            'Tailored Shorts',
            'Denim Skirt',
            'Pleated Midi Skirt',
            'Cargo Pants',
            'Leggings',
            'Straight Jeans',
            'Paper Bag Trousers',
        ],
        'Outerwear': [
            'Puffer Jacket',
            'Wool Blend Coat',
            'Faux Leather Jacket',
            'Trench Coat',
            'Teddy Bear Jacket',
            'Windbreaker',
            'Quilted Jacket',
            'Long Parka',
            'Blazer',
            'Varsity Jacket',
        ]
    }
    
    # Regional pricing multipliers (base = US)
    REGION_MULTIPLIERS = {
        'tr': 0.75,  # Turkey 25% cheaper (purchasing power adjustment)
        'us': 1.00,  # US baseline
        'uk': 1.08,  # UK 8% more (VAT included)
        'de': 1.12,  # Germany 12% more (VAT + market premium)
        'se': 1.15,  # Sweden 15% more (Nordic premium)
    }
    
    def __init__(self):
        """Initialize generator."""
        self.db = Database()
        self.db.create_tables()
        self.converter = CurrencyConverter()
        self.converter.fetch_rates()
        
        self.product_counter = 1000000  # H&M style product codes
        
    def generate_product_code(self):
        """Generate H&M-style product code."""
        code = f"{self.product_counter:07d}001"
        self.product_counter += 1
        return code
    
    def generate_base_price(self, category):
        """Generate base price in USD based on category."""
        price_ranges = {
            'Dresses': (29.99, 79.99),
            'Tops': (9.99, 39.99),
            'Bottoms': (24.99, 59.99),
            'Outerwear': (49.99, 149.99)
        }
        
        min_price, max_price = price_ranges.get(category, (19.99, 69.99))
        return round(random.uniform(min_price, max_price), 2)
    
    def generate_discount(self):
        """Generate realistic discount percentage."""
        # 60% chance of no discount
        if random.random() < 0.6:
            return 0
        
        # 40% chance of discount (10-50%)
        discount_tiers = [10, 15, 20, 25, 30, 40, 50]
        return random.choice(discount_tiers)
    
    def generate_dataset(self, products_per_region=40):
        """
        Generate complete dataset.
        
        Strategy:
        - 60% region-specific products (unique to that market)
        - 40% global products (available in multiple regions)
        """
        print("\n" + "="*70)
        print("GENERATING H&M SAMPLE DATA")
        print("="*70 + "\n")
        
        all_products = []
        
        # Create global products (40% - available in multiple regions)
        global_count = int(products_per_region * 0.4)
        print(f"Creating {global_count} global products (available in multiple regions)...")
        
        for i in range(global_count):
            category = random.choice(list(self.PRODUCTS.keys()))
            product_name = random.choice(self.PRODUCTS[category])
            product_code = self.generate_product_code()
            
            # This product will appear in 3-5 random regions
            num_regions = random.randint(3, 5)
            regions = random.sample(list(self.REGION_MULTIPLIERS.keys()), num_regions)
            
            all_products.append({
                'code': product_code,
                'name': product_name,
                'category': category,
                'regions': regions,
                'is_global': True
            })
        
        print(f"✓ Created {len(all_products)} global products\n")
        
        # Now populate each region
        total_saved = 0
        
        for region_code, multiplier in self.REGION_MULTIPLIERS.items():
            region_name = Database().get_region_id.__self__.REGIONS  # Get region name
            
            print(f"Populating {region_code.upper()}...")
            
            # Add global products for this region
            region_products = [p for p in all_products if region_code in p['regions']]
            
            # Add region-specific products (60%)
            local_count = products_per_region - len(region_products)
            for i in range(local_count):
                category = random.choice(list(self.PRODUCTS.keys()))
                product_name = random.choice(self.PRODUCTS[category])
                product_code = self.generate_product_code()
                
                region_products.append({
                    'code': product_code,
                    'name': product_name,
                    'category': category,
                    'regions': [region_code],
                    'is_global': False
                })
            
            # Save all products for this region
            saved_count = 0
            for product in region_products:
                try:
                    self.db.connect()
                    
                    # Insert product
                    product_id = self.db.insert_product(
                        product_code=product['code'],
                        product_name=product['name'],
                        category=product['category']
                    )
                    
                    # Generate price
                    base_price_usd = self.generate_base_price(product['category'])
                    regional_price_usd = base_price_usd * multiplier
                    
                    # Convert to local currency
                    local_currency = {
                        'tr': 'TRY', 'us': 'USD', 'uk': 'GBP', 
                        'de': 'EUR', 'se': 'SEK'
                    }[region_code]
                    
                    price_local = self.converter.convert(
                        regional_price_usd, 'USD', local_currency
                    )
                    
                    # Add discount
                    discount_pct = self.generate_discount()
                    if discount_pct > 0:
                        original_price = price_local
                        price_local = price_local * (1 - discount_pct / 100)
                    else:
                        original_price = None
                    
                    # Get region ID
                    region_id = self.db.get_region_id(region_code)
                    
                    # Insert price
                    self.db.insert_price(
                        product_id=product_id,
                        region_id=region_id,
                        price_local=round(price_local, 2),
                        currency=local_currency,
                        price_usd=round(regional_price_usd * (1 - discount_pct / 100), 2),
                        original_price_local=round(original_price, 2) if original_price else None,
                        discount_percentage=discount_pct,
                        in_stock=random.random() > 0.05  # 95% in stock
                    )
                    
                    self.db.close()
                    saved_count += 1
                    total_saved += 1
                    
                except Exception as e:
                    print(f"Error saving product: {e}")
                    continue
            
            print(f"  → Saved {saved_count} products ({len([p for p in region_products if p['is_global']])} global, {saved_count - len([p for p in region_products if p['is_global']])} local)")
        
        # Add some historical data (7 days ago) for trend analysis
        print(f"\nAdding historical data for price trends...")
        self._add_historical_data(days_ago=7)
        
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total products saved:     {total_saved}")
        print(f"Global products:          {len(all_products)} (in 3-5 regions each)")
        print(f"Products per region:      ~{products_per_region}")
        print(f"Database:                 {self.db.db_path.absolute()}")
        print("="*70 + "\n")
        
    def _add_historical_data(self, days_ago=7):
        """Add historical prices for trend analysis."""
        self.db.connect()
        
        # Get all current products
        self.db.cursor.execute("SELECT product_id, region_id FROM prices WHERE scraped_at > datetime('now', '-1 day')")
        current_prices = self.db.cursor.fetchall()
        
        # Add historical data
        for product_id, region_id in random.sample(current_prices, min(50, len(current_prices))):
            # Get current price
            self.db.cursor.execute("""
                SELECT price_local, currency, price_usd 
                FROM prices 
                WHERE product_id = ? AND region_id = ?
                ORDER BY scraped_at DESC LIMIT 1
            """, (product_id, region_id))
            
            result = self.db.cursor.fetchone()
            if not result:
                continue
                
            current_price, currency, price_usd = result
            
            # Historical price (5-10% different)
            variation = random.uniform(0.95, 1.05)
            historical_price = current_price * variation
            historical_usd = price_usd * variation
            
            # Insert historical record
            past_date = datetime.now() - timedelta(days=days_ago)
            self.db.cursor.execute("""
                INSERT INTO prices 
                (product_id, region_id, price_local, currency, price_usd, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, region_id, round(historical_price, 2), currency, 
                  round(historical_usd, 2), past_date))
        
        self.db.conn.commit()
        self.db.close()
        print(f"  → Added historical prices for 50 products")


if __name__ == "__main__":
    print("\n🎨 H&M Sample Data Generator")
    print("This creates realistic demo data for your portfolio\n")
    
    generator = SampleDataGenerator()
    generator.generate_dataset(products_per_region=40)
    
    print("✅ Sample data generated successfully!")
    print("\n📊 Next steps:")
    print("1. Run dashboard: streamlit run src/dashboard.py")
    print("2. Explore the data and find insights")
    print("3. Document findings in README.md")
    print("\n🎯 For interviews, explain:")
    print('   "H&M uses heavy JavaScript rendering, so I created')
    print('    sample data to demonstrate the complete analytics system.')
    print('    The framework is ready for sites with accessible data."\n')
