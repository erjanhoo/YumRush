from django.urls import path
from .views import *


urlpatterns = [
    path('main_page/', MainPageView.as_view(), name='main_page'),
    path('restaurants/', RestaurantListView.as_view(), name='restaurant_list'),
    path('search/', ProductSearchView.as_view(), name='product_search'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('get_random_product/', GetOneRandomProductView.as_view(), name='get_random_product'),
    # path('performance_comparison/', PerformanceComparisonView.as_view(), name='performance_comparison'),
]