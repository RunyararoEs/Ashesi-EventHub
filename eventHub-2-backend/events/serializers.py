from rest_framework import serializers
from events.models import Event, EventRegistration
from users.serializers import ClubSerializer, UserSerializer


class EventSerializer(serializers.ModelSerializer):
    club               = ClubSerializer(read_only=True)
    club_id            = serializers.UUIDField(write_only=True)
    registration_count = serializers.SerializerMethodField()
    waitlist_count     = serializers.SerializerMethodField()
    spots_remaining    = serializers.SerializerMethodField()
    user_registration  = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'club', 'club_id', 'title', 'slug', 'description',
            'location', 'starts_at', 'ends_at', 'capacity',
            'spots_remaining', 'is_cancelled', 'created_at', 'updated_at',
            'registration_count', 'waitlist_count', 'user_registration',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_registration_count(self, obj):
        """Number of confirmed (non-waitlist, non-cancelled) registrations."""
        return obj.registrations.filter(
            status=EventRegistration.Status.REGISTERED
        ).count()

    def get_waitlist_count(self, obj):
        """Number of people currently on the waitlist."""
        return obj.registrations.filter(
            status=EventRegistration.Status.WAITLIST
        ).count()

    def get_spots_remaining(self, obj):
        """
        How many confirmed spots are still available.
        Returns null if the event has no capacity limit.
        """
        if obj.capacity is None:
            return None
        confirmed = obj.registrations.filter(
            status=EventRegistration.Status.REGISTERED
        ).count()
        return max(0, obj.capacity - confirmed)

    def get_user_registration(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reg = obj.registrations.filter(user=request.user).first()
            if reg:
                return reg.status
        return None


class EventRegistrationSerializer(serializers.ModelSerializer):
    user  = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)

    class Meta:
        model = EventRegistration
        fields = ['id', 'event', 'user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'event', 'created_at', 'updated_at']