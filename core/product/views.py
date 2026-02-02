from random import choice
import time

from django.core.cache import cache
from django.db.models import Q, Avg, Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from order.models import CartItem, Cart, Order
from order.serializers import CartSerializer
from user.models import MyUser
from .serializers import *
from .models import Product, Category, Company, ProductReview



class MainPageView(APIView):
    @swagger_auto_schema(
        tags=['main_page'],
        operation_description="Get main page data with categories, products and cart",
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY,
                              description="Filter products by category ID", type=openapi.TYPE_INTEGER)
        ],
        responses={
            200: openapi.Response(
                description="Main page data",
                examples={
                    "application/json": {
                        "categories": [
                            {"id": 1, "name": "Burgers", "image": "http://example.com/media/categories/burgers.jpg"}
                        ],
                        "products": [
                            {"id": 1, "name": "Cheeseburger", "image": "http://example.com/media/products/cheeseburger.jpg",
                             "original_price": 10.99, "discounted_price": 8.99,
                             "category": {"id": 1, "name": "Burgers", "image": "http://example.com/media/categories/burgers.jpg"},
                             "rating": 4.5,
                             "company": {"id": 1, "name": "Company Name", "logo": "http://example.com/media/companies/logo.png"},
                             "grams": 250}
                        ],
                        "cart": {
                            "id": 1,
                            "items": [
                                {"id": 1, "product": {"id": 1, "name": "Cheeseburger"}, "quantity": 2, "total_price": 17.98}
                            ],
                            "total_price": 17.98
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        categories = Category.objects.all()
        category_list_serializer = CategoryListSerializer(categories, many=True, context={'request': request})

        category_id = request.query_params.get('category', None)
        if category_id:
            try:
                products = Product.objects.filter(category_id=int(category_id))
            except ValueError:
                return Response({
                    'error': 'Неверный ID категории'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            products = Product.objects.all()

        products_list_serializer = ProductListSerializer(products, many=True, context={'request': request})

        cart = None

        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)

        cart_serializer = CartSerializer(cart) if cart else None

        data = {
            'categories': category_list_serializer.data,
            'products': products_list_serializer.data,
            'cart': cart_serializer.data if cart_serializer else None,
        }

        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['main_page'],
        operation_description="Add product to cart",
        request_body=AddToCartSerializer,
        responses={
            200: CartSerializer,
            400: "Bad request - invalid data",
            401: "Authentication required",
            404: "Product not found"
        }
    )
    def post(self, request):
        if not request.user.is_authenticated:

            return Response({
                'error': 'Требуется аутентификация'
            }, status=status.HTTP_401_UNAUTHORIZED)

        cart, created = Cart.objects.get_or_create(
            user=request.user,
            is_active=True
        )

        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        if not product_id:
            return Response({
                'error': 'ID продукта обязателен'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0 or quantity > 100:
                return Response({
                    'error': 'Количество должно быть от 0 до 100'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                'error': 'Неверное количество'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                'error': 'Продукт не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(
            product=product,
            cart=cart,
            defaults={'quantity': 0}
        )

        new_quantity = cart_item.quantity + quantity

        if new_quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = new_quantity
            cart_item.save()

        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data, status=status.HTTP_200_OK)


class ProductSearchView(ListAPIView):
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'company', 'is_available']
    search_fields = ['name', 'description', 'tags', 'search_keywords']
    ordering_fields = ['name', 'original_price', 'rating', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_available=True)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            try:
                queryset = queryset.filter(original_price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(original_price__lte=float(max_price))
            except ValueError:
                pass
        
        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except ValueError:
                pass
        
        # Filter by stock availability
        in_stock = self.request.query_params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)
        
        return queryset
    
    @swagger_auto_schema(
        tags=['product'],
        operation_description="Search and filter products",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY,
                            description="Search term", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY,
                            description="Filter by category ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('company', openapi.IN_QUERY,
                            description="Filter by company ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('min_price', openapi.IN_QUERY,
                            description="Minimum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY,
                            description="Maximum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('min_rating', openapi.IN_QUERY,
                            description="Minimum rating", type=openapi.TYPE_NUMBER),
            openapi.Parameter('in_stock', openapi.IN_QUERY,
                            description="Only show in-stock items", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('ordering', openapi.IN_QUERY,
                            description="Order by field", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductDetailView(APIView):
    @swagger_auto_schema(
        tags=['product'],
        operation_description="Get detailed information about a product",
        responses={
            200: ProductDetailSerializer,
            404: "Product not found",
            400: "Invalid product ID"
        }
    )
    def get(self, request, pk):
        cache_key = f'product_detail_{pk}'
        cached_product = cache.get(cache_key)
        if cached_product:
            return Response(cached_product, status=status.HTTP_200_OK)

        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({
                'error': 'Продукт не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({
                'error': 'Неверный ID продукта'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProductDetailSerializer(product, context={'request': request})
        cache.set(cache_key, serializer.data, timeout=10)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetOneRandomProductView(APIView):
    def get(self, request):

        products = Product.objects.all()
        product = choice(list(products))
        serializer = ProductDetailSerializer(product)

        return Response(serializer.data, status=status.HTTP_200_OK)


# class PerformanceComparisonView(APIView):
#     @swagger_auto_schema(
#         tags=['performance'],
#         operation_description="Compare performance with and without Redis caching",
#         responses={200: "Performance data"}
#     )
#     def get(self, request):
#         iterations = 50  # Increased iterations for more dramatic results
#
#         # Without caching - fetch all data fresh each time
#         start_time = time.time()
#         for _ in range(iterations):
#             # Fetch products with all related data
#             products = Product.objects.select_related('category', 'company').prefetch_related(
#                 'category__subcategories',
#                 'company__categories',
#                 'company__products'
#             ).all()
#
#             # Fetch categories with related data
#             categories = Category.objects.select_related('company', 'parent_category').prefetch_related(
#                 'subcategories',
#                 'products'
#             ).all()
#
#             # Fetch companies with all related data
#             companies = Company.objects.prefetch_related(
#                 'categories',
#                 'products',
#                 'myuser_set'  # All users belonging to this company
#             ).all()
#
#             # Fetch orders with related data
#             orders = Order.objects.select_related('user', 'assigned_courier').prefetch_related(
#                 'items__product',
#                 'items__product__category',
#                 'items__product__company'
#             ).all()[:100]  # Limit to 100 orders for performance
#
#             # Fetch users
#             users = MyUser.objects.select_related('company').all()[:100]  # Limit to 100 users
#
#             # Serialize all data (this is the expensive part)
#             product_data = ProductListSerializer(products, many=True, context={'request': request}).data
#             category_data = CategoryListSerializer(categories, many=True, context={'request': request}).data
#             company_data = CompanySerializer(companies, many=True, context={'request': request}).data
#             # Convert QuerySets to lists to serialize orders and users
#             order_list = list(orders)
#             user_list = list(users)
#
#         no_cache_time = (time.time() - start_time) / iterations
#
#         # With caching - check cache first
#         start_time = time.time()
#         for _ in range(iterations):
#             cached_data = cache.get('performance_test_data')
#             if not cached_data:
#                 # Fetch products with all related data
#                 products = Product.objects.select_related('category', 'company').prefetch_related(
#                     'category__subcategories',
#                     'company__categories',
#                     'company__products'
#                 ).all()
#
#                 # Fetch categories with related data
#                 categories = Category.objects.select_related('company', 'parent_category').prefetch_related(
#                     'subcategories',
#                     'products'
#                 ).all()
#
#                 # Fetch companies with all related data
#                 companies = Company.objects.prefetch_related(
#                     'categories',
#                     'products',
#                     'myuser_set'
#                 ).all()
#
#                 # Fetch orders with related data
#                 orders = Order.objects.select_related('user', 'assigned_courier').prefetch_related(
#                     'items__product',
#                     'items__product__category',
#                     'items__product__company'
#                 ).all()[:100]
#
#                 # Fetch users
#                 users = MyUser.objects.select_related('company').all()[:100]
#
#                 cached_data = {
#                     'products': ProductListSerializer(products, many=True, context={'request': request}).data,
#                     'categories': CategoryListSerializer(categories, many=True, context={'request': request}).data,
#                     'companies': CompanySerializer(companies, many=True, context={'request': request}).data,
#                     'total_orders': orders.count() if hasattr(orders, 'count') else len(list(orders)),
#                     'total_users': users.count() if hasattr(users, 'count') else len(list(users)),
#                 }
#                 cache.set('performance_test_data', cached_data, timeout=60)
#         cache_time = (time.time() - start_time) / iterations
#
#         # Calculate speedup
#         speedup = round(no_cache_time / cache_time, 2) if cache_time > 0 else 0
#
#         return Response({
#             'no_cache_time_ms': round(no_cache_time * 1000, 3),
#             'cache_time_ms': round(cache_time * 1000, 3),
#             'speedup': f'{speedup}x faster',
#             'time_saved_per_request_ms': round((no_cache_time - cache_time) * 1000, 3),
#             'iterations': iterations,
#             'cache_status': 'HIT' if cache.get('performance_test_data') else 'MISS',
#             'data_fetched': {
#                 'products_count': len(cached_data.get('products', [])) if 'cached_data' in locals() else 0,
#                 'categories_count': len(cached_data.get('categories', [])) if 'cached_data' in locals() else 0,
#                 'companies_count': len(cached_data.get('companies', [])) if 'cached_data' in locals() else 0,
#                 'orders_count': cached_data.get('total_orders', 0) if 'cached_data' in locals() else 0,
#                 'users_count': cached_data.get('total_users', 0) if 'cached_data' in locals() else 0,
#             },
#             'data': cached_data if 'cached_data' in locals() else cache.get('performance_test_data')
#         }, status=status.HTTP_200_OK)


class RestaurantListView(APIView):
    @swagger_auto_schema(
        tags=['restaurants'],
        operation_description="Get list of restaurants with filtering by category and search",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search restaurants by name",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="Filter restaurants that have products in this category",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of restaurants",
                examples={
                    "application/json": {
                        "restaurants": [
                            {
                                "id": 1,
                                "name": "McDonald's",
                                "logo": "https://example.com/media/companies/mcdonalds.jpg",
                                "rating": 4.5,
                                "description": "Fast food chain",
                                "phone_number": "+1234567890",
                                "categories": ["Burgers", "Chicken", "Drinks"],
                                "product_count": 12
                            }
                        ]
                    }
                }
            )
        }
    )
    def get(self, request):
        companies = Company.objects.all()
        
        # Search by restaurant name
        search = request.query_params.get('search', None)
        if search:
            companies = companies.filter(name__icontains=search)
        
        # Filter by category
        category = request.query_params.get('category', None)
        if category:
            # Find companies that have products in this category
            companies = companies.filter(product__category__name__iexact=category).distinct()
        
        # Order by rating (highest first)
        companies = companies.order_by('-rating', 'name')
        
        serializer = CompanyListSerializer(companies, many=True, context={'request': request})
        
        return Response({
            'restaurants': serializer.data
        }, status=status.HTTP_200_OK)
