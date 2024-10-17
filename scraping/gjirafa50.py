import requests
from bs4 import BeautifulSoup
import mysql.connector

class GjirafaScraper:
    def __init__(self, base_url, headers, db_config):
        """
        Initialize the scraper with the base URL, HTTP headers, and database configuration.
        Establish a connection to the MySQL database.
        """
        self.base_url = base_url
        self.headers = headers
        self.total_pages = 0  # Initialize total pages
        self.db_config = db_config
        self.db_connection = self.connect_to_db()

    def connect_to_db(self):
        """Establish a connection to the MySQL database."""
        try:
            connection = mysql.connector.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            return connection
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None

    def get_json_data(self, page_number=1):
        """Fetch the JSON content from the search URL for a specific page."""
        url = f'{self.base_url}/product/search?pagenumber={page_number}&_=1729075655885'
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def parse_product_data(self, product_html):
        """Extract product details from the HTML content and return a list of products."""
        soup = BeautifulSoup(product_html, 'html.parser')
        product_items = soup.find_all('div', class_='item-box')
        products = []

        for product in product_items:
            product_item = product.find('div', class_='product-item')

            # Extracting product details
            product_id = product_item['data-productid'] if product_item and 'data-productid' in product_item.attrs else 'N/A'
            product_name = product_item['onclick'].split('`')[1] if product_item and 'onclick' in product_item.attrs else 'N/A'
            
            # Extract and clean price values
            product_price_tag = product.find('span', class_='price')
            product_price = self.clean_price(product_price_tag.text.strip()) if product_price_tag else None

            old_price_tag = product.find('span', class_='old-price')
            old_price = self.clean_price(old_price_tag.text.strip()) if old_price_tag else None

            product_url_tag = product.find('a')
            product_url = product_url_tag['href'] if product_url_tag else 'N/A'
            image_tag = product.find('img')
            image_url = image_tag['src'] if image_tag else 'N/A'

            # Append the extracted details to the list of products
            products.append([product_id, product_name, product_price, old_price, image_url, product_url])

        return products

    def clean_price(self, price_str):
        """Clean the price string and convert it to a decimal value."""
        if price_str:
            # Remove currency symbols and commas
            price_str = price_str.replace('€', '').replace(',', '').strip()
            try:
                return float(price_str)  # Convert to float (MySQL DECIMAL can accept floats)
            except ValueError:
                print(f"Error converting price: {price_str}")  # Log if conversion fails
                return None
        return None


    def save_to_db(self, products, chunk_size=1000):
        """Insert the scraped product data into the MySQL database in chunks."""
        if not self.db_connection:
            print("No database connection. Cannot save data.")
            return 0  # Return 0 if there's no connection

        cursor = self.db_connection.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS gjirafa50_products (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            name VARCHAR(255),
                            price DECIMAL(10, 2),
                            promo_price DECIMAL(10, 2),
                            image_url VARCHAR(255),
                            product_url VARCHAR(255),
                            product_id VARCHAR(100)
                        )''')
        
        cursor.execute('''TRUNCATE TABLE gjirafa50_products''')

        insert_query = """
        INSERT INTO gjirafa50_products (product_id, name, price, promo_price, image_url, product_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        name = VALUES(name), price = VALUES(price), promo_price = VALUES(promo_price),
        image_url = VALUES(image_url), product_url = VALUES(product_url)
        """

        count = 0  # Counter for number of rows inserted

        for product in products:
            try:
                cursor.execute(insert_query, tuple(product))
                count += 1
            except mysql.connector.Error as err:
                print(f"Error inserting product {product[0]}: {err}")

            # Commit after every `chunk_size` rows
            if count % chunk_size == 0:
                self.db_connection.commit()

        # Commit any remaining rows
        if count % chunk_size != 0:
            self.db_connection.commit()

        print(f"Inserted {count} products into the database.")
        return count  # Return the count of inserted products

    def scrape_page(self, page_number=1):
        """Scrape a specific page for products and return the parsed products."""
        json_data = self.get_json_data(page_number)

        if json_data:
            product_html = json_data.get('html', '')
            self.total_pages = json_data.get('totalpages', 0)  # Update total pages
            if product_html:
                products = self.parse_product_data(product_html)
                return products
        return []

    def scrape_all_pages(self):
        """Scrape all available pages and save the data to the database."""
        all_products = []
        for page in range(1, self.total_pages + 1):  # Loop through all pages
            print(f"Scraping page {page}")
            products = self.scrape_page(page)
            all_products.extend(products)

        if all_products:
            inserted_count = self.save_to_db(all_products)  # Save to DB and get inserted count
            print(f"Inserted {inserted_count} products into the database.")  # Print the number of products inserted

# Example usage:
if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'scrape'
    }

    scraper = GjirafaScraper(base_url='https://gjirafa50.com', headers=headers, db_config=db_config)
    
    # Scrape the first page to get the total number of pages
    initial_data = scraper.get_json_data(page_number=1)
    if initial_data:
        scraper.total_pages = initial_data.get('totalpages', 0)  # Update total pages
        print(f"Total pages to scrape: {scraper.total_pages}")  # Print total pages

    # Scrape all pages and save the data to the database
    scraper.scrape_all_pages()
