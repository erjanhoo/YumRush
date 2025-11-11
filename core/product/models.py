from django.contrib.auth import get_user_model
from django.db import models


user = get_user_model()

from django.db.models import ImageField
import os

class SVGAndImageField(ImageField):
    def validate(self, value, model_instance):
        if not value:
            return
        ext = os.path.splitext(value.name)[1].lower()
        if ext == '.svg':
            # Skip Pillow validation for SVGs
            return
        super().validate(value, model_instance)


#PRODUCT RELATED MODELS

class Company(models.Model):
    name = models.CharField(max_length=255)
    logo = models.FileField(upload_to='companies/', null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=123 ,null=True, blank=True)
    rating = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    image = SVGAndImageField(upload_to='categories/', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True, related_name='categories')
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='subcategories')
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.FileField(upload_to='products/', blank=True, null=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    ingredients = models.TextField(null=True, blank=True)
    rating = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    grams = models.PositiveSmallIntegerField(default=0)
    
    # Inventory management
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    is_available = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(default=15)  # in minutes
    
    # SEO and search
    tags = models.CharField(max_length=500, blank=True, null=True)  # comma-separated tags
    search_keywords = models.CharField(max_length=500, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        return self.discounted_price if self.discounted_price else self.original_price
    
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def is_out_of_stock(self):
        return self.stock_quantity == 0
    
    def reduce_stock(self, quantity):
        """Reduce stock quantity and check availability"""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            if self.stock_quantity == 0:
                self.is_available = False
            self.save(update_fields=['stock_quantity', 'is_available'])
            return True
        return False
    
    def add_stock(self, quantity):
        """Add stock quantity"""
        self.stock_quantity += quantity
        if not self.is_available and self.stock_quantity > 0:
            self.is_available = True
        self.save(update_fields=['stock_quantity', 'is_available'])


class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('user.MyUser', on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=255)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'user']  # One review per user per product
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.FileField(upload_to='products/images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.id}"
