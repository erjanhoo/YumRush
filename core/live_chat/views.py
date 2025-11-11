from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Group, Message
from .serializers import MessageSerializer


class ChatMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Chat'],
        operation_id='chat_messages_list',
        operation_description="Получить историю сообщений чата (только для участников)",
        manual_parameters=[
            openapi.Parameter(
                name='group_id',
                in_=openapi.IN_PATH,
                description='ID группы чата',
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="История сообщений",
                schema=MessageSerializer(many=True)
            ),
            403: openapi.Response(description="Доступ запрещен"),
            404: openapi.Response(description="Группа не найдена"),
        }
    )
    def get(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({"error": "Группа чата не найдена"}, status=status.HTTP_404_NOT_FOUND)

        # Check if user has access to this chat group
        if hasattr(group, 'order') and group.order.exists():
            order = group.order.first()
            if request.user != order.user and request.user != order.assigned_courier:
                return Response({
                    "error": "У вас нет доступа к этому чату"
                }, status=status.HTTP_403_FORBIDDEN)

        # Get messages
        messages = Message.objects.filter(group=group).order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        
        return Response({
            'group_id': group.id,
            'group_name': group.name,
            'messages': serializer.data,
            'total_messages': messages.count()
        }, status=status.HTTP_200_OK)
