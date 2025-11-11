from rest_framework import serializers

from live_chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_username', 'sender_email', 'sender_role', 'message', 'group', 'created_at']
        read_only_fields = ['id', 'created_at', 'sender_username', 'sender_email', 'sender_role']

