from rest_framework import generics, permissions
from users.models import Club
from clubs.serializers import ClubSerializer, ClubDetailSerializer


class ClubListView(generics.ListCreateAPIView):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class ClubDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Club.objects.prefetch_related('admins__user').all()
    lookup_field = 'slug'

    def get_serializer_class(self):
        # Use the richer serializer (includes admins) only for GET detail
        if self.request.method in permissions.SAFE_METHODS:
            return ClubDetailSerializer
        return ClubSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
