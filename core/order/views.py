from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import Order, Cart


class OrderRateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Orders'],
        operation_id='orders_rate',
        operation_description="Оценить доставленный заказ",
        request_body=OrderRatingSerializer,
        manual_parameters=[
            openapi.Parameter(
                name='pk',
                in_=openapi.IN_PATH,
                description='ID заказа',
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(description="Оценка успешно добавлена"),
            400: openapi.Response(description="Ошибка валидации или заказ не доставлен"),
            404: openapi.Response(description="Заказ не найден"),
            401: openapi.Response(description="Требуется аутентификация")
        }
    )
    def post(self, request, pk):
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Заказ не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, что заказ можно оценить
        if order.status != 'delivered':
            return Response({
                "error": "Можно оценить только доставленные заказы"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что заказ еще не оценен
        if order.rating:
            return Response({
                "error": "Заказ уже оценен"
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderRatingSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "Рейтинг выставлен",
                "rating": order.rating
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserOrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Orders'],
        operation_id='orders_history_list',
        operation_description="Получить историю заказов пользователя",
        responses={
            200: openapi.Response(
                description="История заказов",
                schema=UserOrderHistorySerializer(many=True)
            ),
            401: openapi.Response(description="Требуется аутентификация")
        }
    )
    def get(self, request):
        cache_key = f'user_{request.user.id}_order_history'
        data = cache.get(cache_key)

        if data:
            return Response(data, status=status.HTTP_200_OK)

        orders = Order.objects.filter(user=request.user, status='delivered').order_by('-created_at')
        serializer = UserOrderHistorySerializer(orders, many=True)
        cache.set(cache_key, serializer.data, 60*5)

        return Response(serializer.data, status=status.HTTP_200_OK)


class CourierAvailableOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Courier'],
        operation_id='courier_orders_list',
        operation_description="Получить список всех заказов для курьера",
        responses={
            200: openapi.Response(
                description="Список заказов",
                schema=OrderSerializer(many=True)
            ),
            403: openapi.Response(description="Доступ запрещен - не курьер"),
            401: openapi.Response(description="Требуется аутентификация")
        }
    )
    def get(self, request):
        if request.user.role != 'courier':
            return Response({
                "error": "Недостаточно прав. Только курьеры могут просматривать заказы"
            }, status=status.HTTP_403_FORBIDDEN)

        available_orders = Order.objects.filter(assigned_courier__isnull=True, status='new').order_by('-created_at')
        serializer = OrderSerializer(available_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CourierCompletedOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Courier'],
        operation_id='courier_completed_orders_list',
        operation_description="Получить список заказов, которые были выполнены курьером",
        responses={
            200: openapi.Response(
                description="Список выполненных заказов",
                schema=OrderSerializer(many=True)
            ),
            403: openapi.Response(description="Доступ запрещен - не курьер"),
        }
    )
    def get(self, request):
        if request.user.role != 'courier':
            return Response({
                "error": "Недостаточно прав. Только курьеры могут просматривать заказы"
            }, status=status.HTTP_403_FORBIDDEN)
        orders = Order.objects.filter(assigned_courier=request.user, status='delivered').order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Orders'],
        operation_id='orders_create',
        operation_description="Создать заказ из корзины с информацией о доставке",
        request_body=CreateOrderSerializer,
        responses={
            201: openapi.Response(
                description="Заказ успешно создан",
                schema=OrderSerializer
            ),
            400: openapi.Response(description="Ошибка валидации или пустая корзина"),
            401: openapi.Response(description="Требуется аутентификация"),
            404: openapi.Response(description="Корзина не найдена")
        }
    )
    def post(self, request):
        try:
            cart = Cart.objects.get(user=request.user, is_active=True)
            if not cart.items.exists():
                return Response({
                    'error': 'Корзина пуста'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Cart.DoesNotExist:
            return Response({
                'error': 'Корзина не найдена'
            }, status=status.HTTP_404_NOT_FOUND)

        cart_total_price = sum(item.total_price for item in cart.items.all())


        if request.user.balance < cart_total_price:
            return Response({'error': 'Недостаточно средств на счету. Попробуйте еще раз.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CreateOrderSerializer(data=request.data)
        if serializer.is_valid():
            # Создаем заказ
            order = Order.objects.create(
                user=request.user,
                total_price=sum(item.total_price for item in cart.items.all()),
                status='new'
            )

            # Переносим товары из корзины в заказ
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity
                )

            request.user.balance -= cart_total_price
            request.user.save()

            is_free_delivery = True if cart_total_price <= 1000 else False
            # Создаем информацию о доставке

            delivery_data = serializer.validated_data
            Delivery.objects.create(
                order=order,
                delivery_type=delivery_data['delivery_type'],
                receiver_name=delivery_data['receiver_name'],
                receiver_phone_number=delivery_data['receiver_phone_number'],
                delivery_address=delivery_data.get('delivery_address', ''),
                description=delivery_data.get('description', ''),
                is_free_delivery=is_free_delivery
            )


            cart.items.all().delete()
            cart.is_active = False
            cart.save()

            order_serializer = OrderSerializer(order)
            cache.delete(f'user_{request.user.id}_order_history')

            return Response(order_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderHistoryDetailView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=['Orders'],
        operation_id='orders_history_detail',
        operation_description='Получить подробную информацию о заказе текущего пользователя по идентификатору.',
        manual_parameters=[
            openapi.Parameter(
                name='pk',
                in_=openapi.IN_PATH,
                description='ID заказа',
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description='Детали заказа',
                schema=UserOrderHistoryDetailSerializer
            ),
            401: openapi.Response(description='Неавторизован'),
            404: openapi.Response(description='Заказ не найден'),
        }
    )


    def get(self, request, pk):
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserOrderHistoryDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderAcceptView(UpdateAPIView):
    queryset = Order.objects.filter(assigned_courier__isnull=True, status='new')
    serializer_class = OrderUpdateStatusSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if request.user.role != 'courier':
            return Response({'error': 'Only couriers can accept orders'}, status=status.HTTP_403_FORBIDDEN)


        try:
            order = self.get_object()
        except Order.DoesNotExist:
            return Response({'error': 'Order not found or already assigned'}, status=status.HTTP_404_NOT_FOUND)


        order.assigned_courier = request.user
        order.status = 'assigned'
        order.save()


        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderInProgressView(UpdateAPIView):
    queryset = Order.objects.filter(status='assigned')
    serializer_class = OrderUpdateStatusSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if request.user.role != 'courier':
            return Response({'error': 'Only couriers can accept orders'}, status=status.HTTP_403_FORBIDDEN)

        try:
            order = self.get_object()
        except Order.DoesNotExist:
            return Response({'error': 'Order not found or already assigned'}, status=status.HTTP_404_NOT_FOUND)


        order.status = 'in_progress'
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDeliveredView(UpdateAPIView):
    queryset = Order.objects.filter(status='in_progress')
    serializer_class = OrderUpdateStatusSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if request.user.role != 'courier':
            return Response({'error': 'Only couriers can accept orders'}, status=status.HTTP_403_FORBIDDEN)


        try:
            order = self.get_object()
        except Order.DoesNotExist:
            return Response({'error': 'Order not found or already assigned'}, status=status.HTTP_404_NOT_FOUND)

        order.status = 'delivered'
        order.save()


        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
