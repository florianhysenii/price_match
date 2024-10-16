import requests
import json
import re
import sqlite3

class FolejaScraper:
    def __init__(self):
        self.base_url = "https://www.foleja.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
        }
        self.db_connection = self.create_db_connection()

    def create_db_connection(self):
        """Create a database connection."""
        conn = sqlite3.connect("foleja_products.db")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_products (
                id TEXT PRIMARY KEY,
                name TEXT,
                price REAL,
                currency TEXT,
                valid_from TEXT,
                is_valid TEXT
            )
        ''')
        return conn

    def fetch_page(self, page_number):
        """Fetch the entire page content."""
        url = f"{self.base_url}/navigation/c2e892a77619420387908fc3721ca9f2?order=acris-score-desc&p={page_number}"
        print(f"Fetching URL: {url}")
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            return None

    def extract_json_data(self, page_content):
        """Extract JSON data from the page content."""
        # Print the entire page content for debugging
        print("Page Content:\n", page_content)  # Ensure you see the complete page content

        # Use regex to find the dataLayer JSON data
        match = re.search(r'dataLayer\s*=\s*(\[{.*?}\]|\{{.*?}\})', page_content, re.DOTALL)
        if match:
            json_data = match.group(1)

            # Debug: Print the extracted JSON string
            print(f"Extracted JSON data: {json_data}")

            # Try to load the JSON data
            try:
                # Make sure the JSON data has double quotes for keys
                json_data = json_data.replace("'", '"')
                data = json.loads(json_data)
                return data
            except json.JSONDecodeError as e:
                print(f"JSON decoding error: {e}")
                return None
        else:
            print("No dataLayer JSON found.")
            return None


    def save_to_db(self, products):
        """Insert products into the database."""
        cursor = self.db_connection.cursor()
        for product in products:
            cursor.execute('''
                INSERT OR REPLACE INTO test_products (id, name, price, currency, valid_from, is_valid) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                product.get('id'),
                product.get('name'),
                product.get('price'),
                product.get('currency'),  # Ensure currency is included correctly
                None,  # Set valid_from to None or current date
                None   # Set is_valid to None for new entries
            ))
        self.db_connection.commit()

    def scrape(self, page_number):
        """Main scrape method."""
        page_content = self.fetch_page(page_number)
        if page_content:
            json_data = self.extract_json_data(page_content)
            if json_data:
                products = json_data.get('productListing', {}).get('products', [])
                if products:
                    self.save_to_db(products)
                    for product in products:
                        print(f"Product ID: {product.get('id')}, Name: {product.get('name')}, Price: {product.get('price')}")

    def close_db_connection(self):
        """Close the database connection."""
        if self.db_connection:
            self.db_connection.close()

if __name__ == "__main__":
    foleja_scraper = FolejaScraper()
    try:
        foleja_scraper.scrape(page_number=3)  # Change the page number as needed
    finally:
        foleja_scraper.close_db_connection()
