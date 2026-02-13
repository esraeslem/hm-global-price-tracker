import requests
from bs4 import BeautifulSoup

# Use a strong User-Agent to look like a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/'
}

url = 'https://www2.hm.com/tr_tr/kadin/urunler/elbiseler.html'

print(f"🕵️ Inspecting: {url}")
response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")

# Save the HTML so you can read it
with open("hm_debug.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("✅ Saved HTML to 'hm_debug.html'. Open this file in your browser or code editor!")

# Quick check for product elements
soup = BeautifulSoup(response.text, 'html.parser')
products = soup.select('article') # Try generic tag
print(f"Found {len(products)} 'article' tags.")

prices = soup.select('.price') # Try generic class
print(f"Found {len(prices)} items with class '.price'.")
