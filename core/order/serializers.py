from rest_framework import serializers
from product.models import Product
from product.serializers import ProductDetailSerializer, ProductListSerializer
from .models import *


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']

    def get_total_price(self, obj):
        return sum(item.total_price for item in obj.items.all())


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'created_at', 'status', 'total_price', 'user', 'chat_group']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'total_price']


class OrderRatingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ['id', 'rating']

    def validate(self, data):
        if self.instance.status != "delivered":
            raise serializers.ValidationError("Нельзя ставить рейтинг до завершения заказа.")
        return data


class UserOrderHistorySerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    deliveries = DeliverySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'created_at', 'status', 'total_price', 'items', 'deliveries', 'rating']


class UserOrderHistoryDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    deliveries = DeliverySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'created_at', 'delivered_at', 'status', 'total_price', 'items', 'deliveries', 'rating']


class CreateOrderSerializer(serializers.Serializer):
    delivery_type = serializers.ChoiceField(
        choices=[('pickup', 'Pickup'), ('delivery', 'Delivery')],
        required=True
    )
    receiver_name = serializers.CharField(max_length=123, required=True)
    receiver_phone_number = serializers.CharField(max_length=123, required=True)
    delivery_address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, data):
        if data['delivery_type'] == 'delivery' and not data.get('delivery_address'):
            raise serializers.ValidationError({
                'delivery_address':'Address can not be empty'
            })
        return data


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['id', 'delivery_type', 'receiver_name', 'receiver_phone_number',
                  'delivery_address', 'description', 'is_free_delivery', 'created_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    deliveries = DeliverySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'status', 'total_price', 'items', 'deliveries', 'chat_group']



# --- COURIER ---

class CourierOrderDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Order, Delivery
        fields = ['id', 'created_at', 'status', 'delivery_address', 'total_price']


class OrderUpdateStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']


