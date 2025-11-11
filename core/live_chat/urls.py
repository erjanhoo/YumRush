from django.urls import path
from .views import *

urlpatterns = [
    path('<int:group_id>/messages/', ChatMessagesView.as_view(), name='chat_messages'),
]

