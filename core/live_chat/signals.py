from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Message
from .serializers import MessageSerializer

@receiver(post_save, sender=Message)
def message_created(sender, instance, created, **kwargs):
    if created:
        print(f"Signal triggered for message: {instance}")  # Debug log
        channel_layer = get_channel_layer()
        group_name = f'group__{instance.group.id}'
        print(f"Sending to group: {group_name}")  # Debug log
        
        # Serialize the message
        message_data = MessageSerializer(instance).data
        print(f"Serialized message data: {message_data}")  # Debug log
        
        # Send message to group
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )
        print(f"Message sent to group {group_name}")  # Debug log
