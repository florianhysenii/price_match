import requests
from bs4 import BeautifulSoup
import mysql.connector
import re  # Importing regex for extracting ID from the onclick attribute

class Product:
    """
    A class to represent a product with its attributes.
    """
    def __init__(self, name, price, old_price, promo_price, product_url, image_url, data_id):
        self.name = name
        self.price = price if isinstance(price, float) else None
        self.old_price = old_price if isinstance(old_price, float) else None
        self.promo_price = promo_price if isinstance(promo_price, float) else None
        self.product_url = product_url
        self.image_url = image_url
        self.data_id = data_id

    def __repr__(self):
        """Returns a string representation of the Product object for debugging purposes."""
        return (f'Product(name={self.name}, price={self.price}, old_price={self.old_price}, '
                f'promo_price={self.promo_price}, product_url={self.product_url}, '
                f'image_url={self.image_url}, data_id={self.data_id})')

class Scraper:
    """
    A class to scrape product data from a website and save it into a MySQL database.
    """
    def __init__(self, base_url, num_pages, db_config):
        self.base_url = base_url
        self.num_pages = num_pages
        self.products = []
        self.db_config = db_config  # Database configuration

    def fetch_page(self, page_url):
        """Fetches the HTML content of a given page URL."""
        response = requests.get(page_url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text

    def parse_product(self, product_html):
        """
        Extracts product details from the product HTML and returns a Product object.
        """
        soup = BeautifulSoup(product_html, 'html.parser')

        # Extract product details
        article_tag = soup.find('div', class_='art-name mt-2')

        # Extract data_id from the onclick attribute
        if article_tag and article_tag.find('a'):
            onclick_value = article_tag.find('a')['onclick']
            data_id_match = re.search(r"clickedObjectEvent\('(\d+)'\)", onclick_value)
            data_id = data_id_match.group(1) if data_id_match else "N/A"
        else:
            data_id = "N/A"

        # Extract product name
        name = article_tag.find('h2').get_text(strip=True) if article_tag else "N/A"

        # Extract and clean price values
        price = soup.find('span', class_='art-price art-price--offer')
        price = float(price.get_text(strip=True).replace('€', '').replace(',', '.')) if price else None

        # Extract old price
        old_price = soup.find('span', class_='art-oldprice')
        old_price = float(old_price.get_text(strip=True).replace('€', '').replace(',', '.')) if old_price else None

        # Extract promo price if different from regular price (in cases like the one you mentioned)
        promo_price_element = soup.find('span', class_='mr-2 art-price art-price--offer')  # Check if the promo price has a different class
        promo_price = float(promo_price_element.get_text(strip=True).replace('€', '').replace(',', '.')) if promo_price_element else price

        # Extract product URL
        product_url = article_tag.find('a')['href'] if article_tag and article_tag.find('a') else "N/A"
        product_url = f"https://gjirafamall.com{product_url}" if product_url != "N/A" else "N/A"

        # Extract image URL
        image_block = soup.find('div', class_='art-picture-block relative')
        image_url = image_block['data-preload'] if image_block and 'data-preload' in image_block.attrs else "N/A"

        return Product(name=name, price=price, old_price=old_price, promo_price=promo_price, product_url=product_url, image_url=image_url, data_id=data_id)


    def scrape(self):
        """Scrapes the products from all pages and stores them in the products list."""
        for page in range(1, self.num_pages + 1):
            page_url = f"{self.base_url}?s=72&i={page}"
            print(f"Scraping page: {page_url}")
            page_html = self.fetch_page(page_url)
            soup = BeautifulSoup(page_html, 'html.parser')

            product_elements = soup.find_all('div', class_='art-data-block text-align-start')

            for product_element in product_elements:
                product_html = str(product_element)
                product = self.parse_product(product_html)
                self.products.append(product)

    def save_to_mysql(self):
        """Saves the scraped products to the MySQL database."""
        # Establish a database connection
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()

        # Create the products table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS gjirafamall_products (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            name VARCHAR(255),
                            price DECIMAL(10, 2),
                            promo_price DECIMAL(10, 2),
                            image_url VARCHAR(255),
                            product_url VARCHAR(255),
                            product_id VARCHAR(100)
                        )''')
        
        cursor.execute('''TRUNCATE TABLE gjirafamall_products''')


        for product in self.products:
            cursor.execute('''INSERT INTO gjirafamall_products (name, price, promo_price, image_url, product_url, product_id)
                            VALUES (%s, %s, %s, %s, %s, %s)''',
                        (product.name, product.old_price, product.promo_price, product.image_url, product.product_url, product.data_id))


        conn.commit()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'scrape'
    }

    scraper = Scraper('https://gjirafamall.com/kozmetike-3', num_pages=307, db_config=db_config)  # Adjust num_pages if necessary
    scraper.scrape()

    # Save scraped products to MySQL database
    scraper.save_to_mysql()
