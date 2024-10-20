import requests
from bs4 import BeautifulSoup
import mysql.connector

class NeptunScraper:
    def __init__(self, base_url, db_config):
        self.base_url = base_url
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

    def get_subcategories(self):
        """Fetch subcategory links from the main category page."""
        response = requests.get(self.base_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            subcategory_links = []
            subcategories = soup.select('a.sub-category-link')  # Adjust selector based on the website's HTML

            for subcategory in subcategories:
                link = subcategory['href']
                subcategory_links.append(link)
            return subcategory_links
        else:
            print(f"Failed to fetch subcategories: {response.status_code}")
            return []

    def get_products_from_subcategory(self, subcategory_url):
        """Fetch product details from the subcategory page."""
        response = requests.get(subcategory_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            product_items = soup.select('div.product-item')  # Adjust selector based on the website's HTML
            products = []

            for product in product_items:
                product_name = product.select_one('h2.product-name').text.strip()  # Adjust selector
                product_price = product.select_one('span.price').text.strip()  # Adjust selector
                product_url = product.select_one('a.product-link')['href']  # Adjust selector
                image_url = product.select_one('img.product-image')['src']  # Adjust selector
                products.append({
                    'name': product_name,
                    'price': product_price,
                    'url': product_url,
                    'image_url': image_url
                })
            return products
        else:
            print(f"Failed to fetch products: {response.status_code}")
            return []

    def save_to_db(self, products):
        """Insert the scraped product data into the MySQL database."""
        if not self.db_connection:
            print("No database connection. Cannot save data.")
            return

        cursor = self.db_connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS neptun_products (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            name VARCHAR(255),
                            price VARCHAR(50),
                            product_url VARCHAR(255),
                            image_url VARCHAR(255)
                        )''')

        insert_query = """
        INSERT INTO neptun_products (name, price, product_url, image_url)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        name = VALUES(name), price = VALUES(price), image_url = VALUES(image_url)
        """

        for product in products:
            try:
                cursor.execute(insert_query, (product['name'], product['price'], product['url'], product['image_url']))
            except mysql.connector.Error as err:
                print(f"Error inserting product {product['name']}: {err}")

        self.db_connection.commit()
        print(f"Inserted {len(products)} products into the database.")

    def scrape_all(self):
        """Scrape all subcategories and their products."""
        subcategories = self.get_subcategories()
        all_products = []

        for subcategory in subcategories:
            print(f"Scraping subcategory: {subcategory}")
            products = self.get_products_from_subcategory(subcategory)
            all_products.extend(products)

        self.save_to_db(all_products)

# Example usage
if __name__ == '__main__':
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'scrape'
    }

    scraper = NeptunScraper(base_url='https://www.neptun-ks.com/TV___Audio___Video.nspx', db_config=db_config)
    scraper.scrape_all()
