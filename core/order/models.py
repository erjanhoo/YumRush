from django.contrib.auth import get_user_model
from django.core.signals import request_started
from django.db import models
from django.db.models import PositiveSmallIntegerField

from product.models import Product



user = get_user_model()


# ORDER RELATED MODELS
class Order(models.Model):
    assigned_courier = models.ForeignKey(user, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name='orders')
    chat_group = models.ForeignKey('live_chat.Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='order')
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    delivering_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('assigned', 'Назначено курьеру'),
        ('delivering', 'Доставляется'),
        ('delivered', 'Доставлено'),
        ('cancelled', 'Отменено'),
    ]
    status = models.CharField(max_length=50,choices=STATUS_CHOICES, default='new')  # e.g., Pending, Shipped, Delivered, Cancelled
    rating = PositiveSmallIntegerField(null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"Order {self.id} by {self.user.username} - Status: {self.status} - Total: ${self.total_price:.2f}"

    @property
    def calculated_total_price(self):
        return sum(item.total_price for item in self.items.all())


class Delivery(models.Model):
    DELIVERY_TYPE_CHOICES = [
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
    ]

    is_free_delivery = models.BooleanField(default=False)
    delivery_type = models.CharField(max_length=123, choices=DELIVERY_TYPE_CHOICES, default='pickup')
    receiver_name = models.CharField(max_length=123)
    receiver_phone_number = models.CharField(max_length=123)
    delivery_address = models.CharField(max_length=255, null=True, blank=True)  # Optional field for delivery address
    description = models.TextField(null=True, blank=True)  # Optional field for additional delivery information
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deliveries')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delivery for Order {self.order.id} - {'Delivery' if self.delivery_type else 'Pickup'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order: {self.order.id})"

    @property
    def total_price(self):
        return self.product.final_price * self.quantity


# CART MODELS
class Cart(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Cart for {self.user.username}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f'{self.product}({self.quantity})'

    @property
    def total_price(self):
        return self.product.final_price * self.quantity
