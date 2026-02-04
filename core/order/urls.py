from django.urls import path
from .views import *

urlpatterns = [
    # Cart management
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/clear/', ClearCartView.as_view(), name='cart_clear'),
    
    # Order management
    path('create/', CreateOrderView.as_view(), name='create_order'),
    path('history/', UserOrderHistoryView.as_view(), name='user_order_history'),
    path('order_history_detail/<int:pk>/', OrderHistoryDetailView.as_view(), name='user_order_history_detail'),
    path('<int:pk>/rate/', OrderRateView.as_view(), name='rate_order'),
    path('<int:pk>/cancel/', OrderCancelView.as_view(), name='cancel_order'),
    path('<int:pk>/chat/', OrderChatGroupView.as_view(), name='order_chat_group'),

    # Courier orders
    path('courier/available_orders/', CourierAvailableOrdersView.as_view(), name='courier_orders'),
    path('courier/active_orders/', CourierActiveOrdersView.as_view(), name='courier_active_orders'),
    path('courier/completed_orders/', CourierCompletedOrdersView.as_view(), name='courier_completed_orders'),

    # Order's status
    path('courier/<int:pk>/accept/', OrderAcceptView.as_view(), name='order-accept'),
    path('courier/<int:pk>/in-progress/', OrderInProgressView.as_view(), name='order-in-progress'),
    path('courier/<int:pk>/delivered/', OrderDeliveredView.as_view(), name='order-delivered'),

]