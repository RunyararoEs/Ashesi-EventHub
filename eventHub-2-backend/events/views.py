from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from events.models import Event, EventRegistration
from events.serializers import EventSerializer, EventRegistrationSerializer
from events.factory import RegistrationFactory


class IsClubAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if user.is_system_admin():
            return True
        if user.is_club_admin():
            return obj.club.admins.filter(user=user).exists()
        return False


class EventListView(generics.ListCreateAPIView):
    serializer_class = EventSerializer

    def get_queryset(self):
        qs = Event.objects.select_related('club').prefetch_related('registrations')
        club_slug = self.request.query_params.get('club')
        if club_slug:
            qs = qs.filter(club__slug=club_slug)
        upcoming = self.request.query_params.get('upcoming')
        if upcoming:
            from django.utils import timezone
            qs = qs.filter(starts_at__gte=timezone.now(), is_cancelled=False)
        return qs

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.select_related('club').prefetch_related('registrations')
    serializer_class = EventSerializer
    lookup_field = 'pk'
    permission_classes = [permissions.IsAuthenticated, IsClubAdminOrReadOnly]


class EventRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        if event.is_cancelled:
            return Response(
                {'detail': 'Event is cancelled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Factory Pattern — delegate the REGISTERED vs WAITLIST decision
        # to RegistrationFactory. The view no longer contains that logic.
        factory = RegistrationFactory(event)
        reg, created = factory.get_or_create(request.user)

        if not created:
            return Response(
                {'detail': 'Already registered.', 'status': reg.status},
                status=status.HTTP_200_OK,
            )

        serializer = EventRegistrationSerializer(reg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        reg = get_object_or_404(EventRegistration, event=event, user=request.user)
        reg.status = EventRegistration.Status.CANCELLED
        reg.save()
        return Response({'detail': 'Registration cancelled.'}, status=status.HTTP_200_OK)


class MyRegistrationsView(generics.ListAPIView):
    serializer_class = EventRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EventRegistration.objects.filter(
            user=self.request.user
        ).select_related('event__club').exclude(status=EventRegistration.Status.CANCELLED)


class EventCloneView(APIView):
    """
    Prototype Pattern — clone an existing event into a new one.

    POST /api/events/<id>/clone/

    The caller can optionally override title, starts_at, and ends_at
    for the new event. All other fields (description, location, capacity,
    club) are copied directly from the original via Event.clone().

    Only a club admin belonging to this event's club (or system admin)
    can clone an event.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        # Permission check — only the club's own admins or system admin
        user = request.user
        if not user.is_system_admin():
            if not user.is_club_admin():
                return Response(
                    {'detail': 'Only club admins can clone events.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not event.club.admins.filter(user=user).exists():
                return Response(
                    {'detail': 'You can only clone events belonging to your club.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Parse optional overrides from request body
        new_title     = request.data.get('title')
        new_starts_at = None
        new_ends_at   = None

        starts_raw = request.data.get('starts_at')
        ends_raw   = request.data.get('ends_at')

        if starts_raw:
            from django.utils.dateparse import parse_datetime
            new_starts_at = parse_datetime(starts_raw)
            if new_starts_at is None:
                return Response(
                    {'detail': 'Invalid starts_at format. Use ISO 8601.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if ends_raw:
            from django.utils.dateparse import parse_datetime
            new_ends_at = parse_datetime(ends_raw)
            if new_ends_at is None:
                return Response(
                    {'detail': 'Invalid ends_at format. Use ISO 8601.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Prototype — call clone() on the original event instance
        cloned_event = event.clone(
            new_title=new_title,
            new_starts_at=new_starts_at,
            new_ends_at=new_ends_at,
        )

        serializer = EventSerializer(cloned_event, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
