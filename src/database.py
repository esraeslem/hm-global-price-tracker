import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'hm_global.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Products Table (Global ID)
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            article_code TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            image_url TEXT
        )
    ''')
    
    # 2. Prices Table (Tracks history & region)
    c.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_code TEXT,
            region TEXT,       -- e.g., 'tr', 'us', 'de'
            price_original REAL,
            currency TEXT,
            price_in_usd REAL, -- Normalized price for comparison
            date_scraped DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(article_code) REFERENCES products(article_code)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
