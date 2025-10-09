from random import choice
import time

from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from order.models import CartItem, Cart, Order
from order.serializers import CartSerializer
from user.models import MyUser
from .serializers import *



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
