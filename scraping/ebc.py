import requests
from bs4 import BeautifulSoup
import mysql.connector

class Product:
    """
    Represents a product with its details.

    Attributes:
        name (str): The name of the product.
        price (float): The current price of the product.
        promo_price (float or None): The promotional price of the product, if available.
        image_url (str): The URL of the product's image.
        product_url (str): The URL of the product's page.
        product_id (str or None): The unique identifier for the product.
    """

    def __init__(self, name, price, promo_price, image_url, product_url, product_id):
        """
        Initializes a Product instance.

        Args:
            name (str): The name of the product.
            price (float): The current price of the product.
            promo_price (float or None): The promotional price of the product, if available.
            image_url (str): The URL of the product's image.
            product_url (str): The URL of the product's page.
            product_id (str or None): The unique identifier for the product.
        """
        self.name = name
        self.price = price
        self.promo_price = promo_price
        self.image_url = image_url
        self.product_url = product_url
        self.product_id = product_id

    def __repr__(self):
        """Returns a string representation of the Product instance."""
        return (f'Product(name={self.name}, price={self.price}, promo_price={self.promo_price}, '
                f'image_url={self.image_url}, product_url={self.product_url}, product_id={self.product_id})')


class Scraper:
    """
    A class for scraping product information from a website and saving it to a MySQL database.

    Attributes:
        base_url (str): The base URL of the website to scrape.
        num_pages (int): The number of pages to scrape.
        products (list): A list to store Product instances.
        db_config (dict): Database configuration for MySQL connection.
    """

    def __init__(self, base_url, num_pages, db_config):
        """
        Initializes a Scraper instance.

        Args:
            base_url (str): The base URL of the website to scrape.
            num_pages (int): The number of pages to scrape.
            db_config (dict): Database configuration for MySQL connection.
        """
        self.base_url = base_url
        self.num_pages = num_pages
        self.products = []
        self.db_config = db_config  # Database configuration

    def fetch_page(self, page_url):
        """
        Fetches the HTML content of a page.

        Args:
            page_url (str): The URL of the page to fetch.

        Returns:
            str: The HTML content of the page.
        """
        response = requests.get(page_url)
        return response.text

    def parse_product(self, product_html):
        """
        Parses the HTML of a product to extract its details.

        Args:
            product_html (str): The HTML content of the product.

        Returns:
            Product: An instance of the Product class with extracted details.
        """
        soup = BeautifulSoup(product_html, 'html.parser')
        name = soup.find('h4', class_='product_name').get_text(strip=True)
        price = float(soup.find('span', class_='current_price').get_text(strip=True).replace('€', '').replace(',', '.'))
        promo_price_tag = soup.find('span', class_='discount_price')
        promo_price = float(promo_price_tag.get_text(strip=True).replace('€', '').replace(',', '.')) if promo_price_tag else None
        image_url = soup.find('div', class_='products-single-image')['style'].split("url('")[-1].split("')")[0]
        
        # Extracting the product_url and building product_id from it
        product_url = soup.find('a', class_='primary_img')['href']
        # Assuming product_id is the last segment of the product_url
        product_id = product_url.split('/')[-1]  # Change this logic based on actual URL structure

        return Product(name=name, price=price, promo_price=promo_price, image_url=image_url, product_url=product_url, product_id=product_id)


    def save_to_mysql(self):
        """
        Saves the scraped products to a MySQL database.
        Creates the products table if it doesn't exist and inserts each product into the database.
        """
        # Establish a database connection
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()

        # Create the products table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS ebc_products (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            name VARCHAR(255),
                            price DECIMAL(10, 2),
                            promo_price DECIMAL(10, 2),
                            image_url VARCHAR(255),
                            product_url VARCHAR(255),
                            product_id VARCHAR(100)
                        )''')
        
        cursor.execute('''TRUNCATE TABLE ebc_products''')

        # Insert products into the database
        for product in self.products:
            cursor.execute('''INSERT INTO ebc_products (name, price, promo_price, image_url, product_url, product_id)
                              VALUES (%s, %s, %s, %s, %s, %s)''',
                           (product.name, product.price, product.promo_price, product.image_url, product.product_url, product.product_id))

        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    def scrape(self):
        """
        Scrapes product information from multiple pages of the website.

        Iterates over the specified number of pages and extracts product details,
        storing them in the products list.
        """
        for page in range(1, self.num_pages + 1):
            page_url = f"{self.base_url}?page={page}"
            page_html = self.fetch_page(page_url)
            soup = BeautifulSoup(page_html, 'html.parser')

            product_elements = soup.find_all('article', class_='single_product')

            for product_element in product_elements:
                product_html = str(product_element)
                product = self.parse_product(product_html)
                self.products.append(product)

if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'scrape'
    }

    scraper = Scraper('https://ebc.shop/category/FRG', num_pages=26, db_config=db_config)
    scraper.scrape()
    scraper.save_to_mysql()  # Save products to MySQL
