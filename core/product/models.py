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

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        return self.discounted_price if self.discounted_price else self.original_price
