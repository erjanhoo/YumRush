from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from drf_yasg import openapi
from common.permissions import IsCourier
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import Order, Cart
from .tasks import send_email_notification
from django.db import transaction
from live_chat.models import Group


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


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Orders'],
        operation_id='orders_cancel',
        operation_description="Отменить заказ (только если статус 'new' или 'assigned')",
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
            200: openapi.Response(description="Заказ успешно отменен"),
            400: openapi.Response(description="Заказ нельзя отменить"),
            404: openapi.Response(description="Заказ не найден"),
            401: openapi.Response(description="Требуется аутентификация")
        }
    )
    def post(self, request, pk):

        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Заказ не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Can only cancel if order is new or assigned
        if order.status not in ['new', 'assigned']:
            return Response({
                "error": f"Нельзя отменить заказ со статусом '{order.status}'"
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Refund the money
            order.user.balance += order.total_price
            order.user.save()

            # Update order status
            from django.utils import timezone
            order.status = 'cancelled'
            order.cancelled_at = timezone.now()
            order.save()

            # Notify courier if one was assigned
            if order.assigned_courier:
                send_email_notification.delay(
                    order.assigned_courier.email,
                    f'Заказ #{order.id} был отменен пользователем'
                )

        # Invalidate cache
        cache.delete(f'user_{request.user.id}_order_history')

        return Response({
            "status": "Заказ отменен",
            "refunded_amount": float(order.total_price)
        }, status=status.HTTP_200_OK)


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
    permission_classes = [IsAuthenticated, IsCourier]

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
    permission_classes = [IsAuthenticated, IsCourier]

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


class CourierActiveOrdersView(APIView):
    permission_classes = [IsAuthenticated, IsCourier]

    @swagger_auto_schema(
        tags=['Courier'],
        operation_id='courier_active_orders_list',
        operation_description="Получить список активных заказов курьера (принятые и доставляемые)",
        responses={
            200: openapi.Response(
                description="Список активных заказов",
                schema=OrderDetailSerializer(many=True)
            ),
            403: openapi.Response(description="Доступ запрещен - не курьер"),
        }
    )
    def get(self, request):
        if request.user.role != 'courier':
            return Response({
                "error": "Недостаточно прав. Только курьеры могут просматривать заказы"
            }, status=status.HTTP_403_FORBIDDEN)

        # Get orders that are assigned or being delivered by this courier
        orders = Order.objects.filter(
            assigned_courier=request.user,
            status__in=['assigned', 'delivering']
        ).order_by('-created_at')

        serializer = OrderDetailSerializer(orders, many=True)
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
        from django.db import transaction

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
            # Create order and deduct balance atomically
            with transaction.atomic():
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

                is_free_delivery = True if cart_total_price >= 1000 else False
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
    permission_classes = [IsAuthenticated, IsCourier]

    @swagger_auto_schema(
        tags=['Courier'],
        operation_id='courier_accept_order',
        operation_description="Принять заказ курьером",
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
                description="Заказ принят",
                schema=OrderUpdateStatusSerializer
            ),
            404: openapi.Response(description="Заказ недоступен или уже принят"),
            403: openapi.Response(description="Доступ запрещен - не курьер"),
            401: openapi.Response(description="Требуется аутентификация")
        }
    )
    def update(self, request, *args, **kwargs):

        # Use select_for_update to prevent race conditions
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(
                    pk=kwargs['pk'],
                    assigned_courier__isnull=True,
                    status='new'
                )
            except Order.DoesNotExist:
                return Response({
                    'error': 'Заказ недоступен или уже принят другим курьером'
                }, status=status.HTTP_404_NOT_FOUND)

            order.assigned_courier = request.user
            order.status = 'assigned'
            order.assigned_at = timezone.now()

            # Create chat group for user and courier
            chat_group = Group.objects.create(
                name=f"Order_{order.id}_User_{order.user.id}_Courier_{request.user.id}"
            )
            order.chat_group = chat_group
            order.save()

        send_email_notification.delay(order.user.email, 'Курьер назначен на ваш заказ!')

        # Invalidate user's order history cache
        cache.delete(f'user_{order.user.id}_order_history')

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderInProgressView(UpdateAPIView):
    queryset = Order.objects.filter(status='assigned')
    serializer_class = OrderUpdateStatusSerializer
    permission_classes = [IsAuthenticated, IsCourier]

    @swagger_auto_schema(
        tags=['Courier'],
        operation_id='courier_start_delivery',
        operation_description="Начать доставку заказа",
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
                description="Доставка началась",
                schema=OrderUpdateStatusSerializer
            ),
            404: openapi.Response(description="Заказ не найден"),
            403: openapi.Response(description="Вы не можете обновить этот заказ"),
            401: openapi.Response(description="Требуется аутентификация")
        }
    )
    def update(self, request, *args, **kwargs):
        from django.utils import timezone

        order = self.get_object()

        # Verify the courier is the one assigned to this order
        if order.assigned_courier != request.user:
            return Response({
                'error': 'Вы не можете обновить этот заказ'
            }, status=status.HTTP_403_FORBIDDEN)

        order.status = 'delivering'
        order.delivering_at = timezone.now()
        order.save()
        send_email_notification.delay(order.user.email, 'Курьер в пути с вашим заказом!')

        # Invalidate user's order history cache
        cache.delete(f'user_{order.user.id}_order_history')

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDeliveredView(UpdateAPIView):
    queryset = Order.objects.filter(status='delivering')
    serializer_class = OrderUpdateStatusSerializer
    permission_classes = [IsAuthenticated, IsCourier]

    @swagger_auto_schema(
        tags=['Courier'],
        operation_id='courier_complete_delivery',
        operation_description="Завершить доставку заказа",
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
                description="Заказ доставлен",
                schema=OrderUpdateStatusSerializer
            ),
            404: openapi.Response(description="Заказ не найден"),
            403: openapi.Response(description="Вы не можете обновить этот заказ"),
            401: openapi.Response(description="Требуется аутентификация")
        }
    )
    def update(self, request, *args, **kwargs):
        from django.utils import timezone

        order = self.get_object()

        # Verify the courier is the one assigned to this order
        if order.assigned_courier != request.user:
            return Response({
                'error': 'Вы не можете обновить этот заказ'
            }, status=status.HTTP_403_FORBIDDEN)

        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.save()
        send_email_notification.delay(order.user.email, 'Ваш заказ доставлен! Спасибо, что выбрали нас!')

        # Invalidate user's order history cache
        cache.delete(f'user_{order.user.id}_order_history')

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderChatGroupView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Orders'],
        operation_id='order_chat_group',
        operation_description="Получить ID группы чата для заказа (только для пользователя или назначенного курьера)",
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
                description="ID группы чата",
                examples={
                    "application/json": {
                        "chat_group_id": 123,
                        "order_id": 456,
                        "status": "assigned"
                    }
                }
            ),
            403: openapi.Response(description="Доступ запрещен"),
            404: openapi.Response(description="Заказ не найден или чат не создан"),
            401: openapi.Response(description="Требуется аутентификация")
        }
    )
    def get(self, request, pk):
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({"error": "Заказ не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is either the customer or the assigned courier
        if order.user != request.user and order.assigned_courier != request.user:
            return Response({
                "error": "У вас нет доступа к этому чату"
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if chat group exists
        if not order.chat_group:
            return Response({
                "error": "Чат еще не создан. Ожидайте назначения курьера."
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "chat_group_id": order.chat_group.id,
            "order_id": order.id,
            "status": order.status,
            "user_id": order.user.id,
            "courier_id": order.assigned_courier.id if order.assigned_courier else None
        }, status=status.HTTP_200_OK)

