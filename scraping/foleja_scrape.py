import requests
import sqlite3
from bs4 import BeautifulSoup

class FolejaScraper:
    def __init__(self):
        self.base_url = "https://www.foleja.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
        }
        self.db_connection = self.create_db_connection()

    def create_db_connection(self):
        """Create a database connection and the foleja_products table."""
        conn = sqlite3.connect("foleja_products.db")
        cursor = conn.cursor()

        # Create the products table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS foleja_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price DECIMAL(10, 2),
                promo_price DECIMAL(10, 2),
                image_url TEXT,
                product_url TEXT,
                product_id TEXT
            )
        ''')
        
        # Truncate the foleja_products table
        cursor.execute('DELETE FROM foleja_products')  # Use DELETE instead of TRUNCATE for SQLite

        conn.commit()  # Commit changes to the database
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

    def extract_product_data(self, page_content):
        """Extract product data using BeautifulSoup."""
        soup = BeautifulSoup(page_content, 'html.parser')

        product_info = []
        
        # Check the entire page content to find where product data is stored
        print(soup.prettify())  # This will print the entire HTML structure; you can search for product details in the output.

        # Loop over product containers and extract relevant data
        for product in soup.find_all('div', class_='product-item'):
            product_id = product.get('data-id')  # Adjust based on the actual structure
            product_name = product.find('span', class_='product-name').get_text(strip=True) if product.find('span', class_='product-name') else 'N/A'
            product_price = product.find('span', class_='product-price').get_text(strip=True).replace('€', '').replace(',', '.') if product.find('span', class_='product-price') else '0.00'
            promo_price = product.find('span', class_='product-promo-price').get_text(strip=True).replace('€', '').replace(',', '.') if product.find('span', class_='product-promo-price') else '0.00'
            image_url = product.find('img', class_='product-image')['src'] if product.find('img', class_='product-image') else 'N/A'
            product_url = product.find('a', class_='product-link')['href'] if product.find('a', class_='product-link') else 'N/A'

            # Append to product_info list
            product_info.append((product_name, float(product_price), float(promo_price), image_url, product_url, product_id))

        return product_info


    def insert_products(self, products):
        """Insert extracted product data into the database."""
        cursor = self.db_connection.cursor()
        cursor.executemany('''
            INSERT INTO foleja_products (name, price, promo_price, image_url, product_url, product_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', products)
        self.db_connection.commit()

    def run(self):
        """Run the scraper."""
        for page_number in range(1, 6):  # Adjust the range for the number of pages you want to scrape
            page_content = self.fetch_page(page_number)
            if page_content:
                products = self.extract_product_data(page_content)
                self.insert_products(products)

if __name__ == "__main__":
    scraper = FolejaScraper()
    scraper.run()
