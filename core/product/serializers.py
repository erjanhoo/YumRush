from rest_framework import serializers
from .models import *


class CategoryListSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    class Meta:
        model = Category
        fields = ['id', 'name', 'image']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'logo']


class ProductListSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    category = CategoryListSerializer()
    company = CompanySerializer()

    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'original_price', 'discounted_price', 'category', 'rating', 'company', 'grams']


class ProductDetailSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    class Meta:
        model = Product
        fields = ['id', 'name', 'original_price', 'discounted_price', 'category', 'rating', 'company', 'description', 'image', 'ingredients', 'grams']


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(default=1)


class CompanyListSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'name', 'logo', 'rating', 'description', 'phone_number', 'categories', 'product_count']

    def get_logo(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

    def get_categories(self, obj):
        # Get unique categories from all products of this company
        categories = Product.objects.filter(company=obj).values_list('category__name', flat=True).distinct()
        return list(categories)

    def get_product_count(self, obj):
        return Product.objects.filter(company=obj).count()
