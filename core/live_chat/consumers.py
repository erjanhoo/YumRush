from channels.generic.websocket import AsyncWebsocketConsumer
from djangochannelsrestframework.observer import model_observer
from asgiref.sync import sync_to_async
from .models import Message, Group
from .serializers import MessageSerializer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f'group__{self.group_id}'
        
        # Get user from scope
        self.user = self.scope.get('user')
        
        # Check authentication
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Verify user has access to this chat group
        has_access = await self.check_group_access()
        if not has_access:
            await self.close()
            return
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send message history when user connects
        messages = await self.get_message_history()
        await self.send(text_data=json.dumps({
            'action': 'message_history',
            'data': messages,
            'response_status': 200
        }))

    @sync_to_async
    def get_message_history(self):
        """Get all messages for this group"""
        try:
            messages = Message.objects.filter(group_id=self.group_id).order_by('created_at')
            serializer = MessageSerializer(messages, many=True)
            return serializer.data
        except Exception as e:
            print(f"Error fetching message history: {e}")
            return []

    @sync_to_async
    def check_group_access(self):
        """Check if the user has access to this chat group"""
        try:
            group = Group.objects.get(id=self.group_id)
            # Check if there's an order associated with this group
            if hasattr(group, 'order') and group.order.exists():
                order = group.order.first()
                # User must be either the customer or the assigned courier
                return self.user == order.user or self.user == order.assigned_courier
            # If no order associated, allow access (for general chat groups)
            return True
        except Group.DoesNotExist:
            return False

    @sync_to_async
    def create_message(self, message_data):
        """Sync function to create a message"""
        serializer = MessageSerializer(data=message_data)
        if serializer.is_valid():
            instance = serializer.save()
            return {'success': True, 'data': MessageSerializer(instance).data, 'errors': None}
        else:
            return {'success': False, 'data': None, 'errors': serializer.errors}

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'create':
                # Get data from the request
                message_data = data.get('data', {})
                print(f"Received message data: {message_data}")  # Debug log
                
                # Use sync_to_async to handle database operations
                result = await self.create_message(message_data)
                
                if result['success']:
                    print(f"Message saved successfully")  # Debug log
                    
                    # Broadcast message to ALL users in the group (including sender)
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'chat_message',
                            'message': {
                                'action': 'new_message',
                                'data': result['data'],
                                'response_status': 201
                            }
                        }
                    )
                else:
                    print(f"Serializer errors: {result['errors']}")  # Debug log
                    # Send error response back to sender
                    await self.send(text_data=json.dumps({
                        'action': 'create',
                        'errors': result['errors'],
                        'data': None,
                        'response_status': 400
                    }))
            else:
                await self.send(text_data=json.dumps({
                    'action': action,
                    'errors': ['Unknown action'],
                    'data': None,
                    'response_status': 400
                }))
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")  # Debug log
            await self.send(text_data=json.dumps({
                'action': 'error',
                'errors': ['Invalid JSON'],
                'data': None,
                'response_status': 400
            }))
        except Exception as e:
            print(f"Unexpected error in receive: {e}")  # Debug log
            await self.send(text_data=json.dumps({
                'action': 'error',
                'errors': [str(e)],
                'data': None,
                'response_status': 500
            }))
    # Handle messages from the group
    async def chat_message(self, event):
        print(f"chat_message called with event: {event}")  # Debug log
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['message']))
        print(f"Message sent to WebSocket: {event['message']}")  # Debug log
