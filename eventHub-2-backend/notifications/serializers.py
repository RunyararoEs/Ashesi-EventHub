from rest_framework import serializers
from notifications.models import Notification
from users.serializers import UserSerializer, ClubSerializer
from events.serializers import EventSerializer


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'kind', 'title', 'body',
            'club', 'event', 'actor',
            'read_at', 'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']