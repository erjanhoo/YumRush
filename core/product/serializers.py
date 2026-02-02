from rest_framework import serializers
from .models import *


class CategoryListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'image']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class CompanySerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'logo']
    
    def get_logo(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


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
        # Get unique categories from company's products
        from product.models import Product
        categories = Product.objects.filter(company=obj).values_list('category__name', flat=True).distinct()
        return list(categories)
    
    def get_product_count(self, obj):
        return obj.product_set.count()


class ProductListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    category = CategoryListSerializer()
    company = CompanySerializer()

    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'original_price', 'discounted_price', 'category', 'rating', 'company', 'grams']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    company = CompanySerializer()
    class Meta:
        model = Product
        fields = ['id', 'name', 'original_price', 'discounted_price', 'category', 'rating', 'company', 'description', 'image', 'ingredients', 'grams']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(default=1)
