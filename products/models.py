# products/models.py
from django.db import models

class Product(models.Model):
    product_id = models.CharField(max_length=100, unique=True)
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.CharField(max_length=50, null=True, blank=True)  # Added discount field
    product_url = models.URLField(max_length=500)
    image_url = models.URLField(max_length=500)
    execution_date = models.DateTimeField(auto_now_add=True)  # Date of scraping
    valid_from = models.DateTimeField(auto_now_add=True)  # Date of insertion
    is_valid = models.DateTimeField(null=True, blank=True)  # Last date the record was valid

    def __str__(self):
        return self.product_name
