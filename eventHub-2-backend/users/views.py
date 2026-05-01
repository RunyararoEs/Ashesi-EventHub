from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from users.models import ClubAdmin, ClubAdminTransferRequest
from users.serializers import (
    RegisterSerializer,
    TransferRequestSerializer,
    UserListSerializer,
    UserSerializer,
)
from users.jwt_adapter import JWTAdapter, AuthenticationError, TokenRefreshError

User = get_user_model()


# ── Permissions ───────────────────────────────────────────────────────────────
class IsSystemAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_system_admin()


# ── Auth Views (Adapter Pattern) ──────────────────────────────────────────────
class LoginView(APIView):
    """
    Adapter Pattern — login endpoint backed by JWTAdapter.

    This view never imports from simplejwt directly. It delegates all
    token logic to JWTAdapter, which is the only place simplejwt is used.
    Swapping JWT libraries only requires changing jwt_adapter.py.

    POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    Returns: { "access": "...", "refresh": "..." }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email    = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {'detail': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tokens = JWTAdapter.login(email, password)
            return Response(tokens, status=status.HTTP_200_OK)
        except AuthenticationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class TokenRefreshAdapterView(APIView):
    """
    Adapter Pattern — token refresh endpoint backed by JWTAdapter.

    POST /api/auth/refresh/
    Body: { "refresh": "..." }
    Returns: { "access": "..." }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh', '')

        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tokens = JWTAdapter.refresh(refresh_token)
            return Response(tokens, status=status.HTTP_200_OK)
        except TokenRefreshError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


# ── User ──────────────────────────────────────────────────────────────────────
class RegisterView(generics.CreateAPIView):
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """System admin only — list all users."""
    queryset           = User.objects.all().order_by('role', 'username')
    serializer_class   = UserListSerializer
    permission_classes = [IsSystemAdmin]


# ── Transfer Requests ─────────────────────────────────────────────────────────
class TransferRequestCreateView(generics.CreateAPIView):
    """
    Any authenticated user can submit a transfer request.
    Validation in the model ensures only one pending request at a time.
    """
    serializer_class   = TransferRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)


class TransferRequestListView(generics.ListAPIView):
    """System admin only — view all transfer requests."""
    serializer_class   = TransferRequestSerializer
    permission_classes = [IsSystemAdmin]

    def get_queryset(self):
        status_filter = self.request.query_params.get('status', 'pending')
        return ClubAdminTransferRequest.objects.filter(
            status=status_filter
        ).select_related(
            'club', 'requester', 'admin_to_replace__user', 'admin_to_replace__club'
        ).order_by('-created_at')


class TransferRequestApproveView(APIView):
    """System admin approves a transfer request."""
    permission_classes = [IsSystemAdmin]

    def patch(self, request, pk):
        transfer = get_object_or_404(
            ClubAdminTransferRequest, pk=pk, status=ClubAdminTransferRequest.Status.PENDING
        )

        removed_admin_user = transfer.approve()

        # Transfer notifications don't involve events so we use direct creates.
        # The NotificationBuilder is for event-based notifications (Observer signals).
        self._notify(
            recipient = transfer.requester,
            kind      = 'registration_confirmed',
            title     = 'Transfer Request Approved',
            body      = (
                f'Your request to join {transfer.club.name} as a club admin '
                f'has been approved. Welcome aboard!'
            ),
            club      = transfer.club,
        )
        self._notify(
            recipient = removed_admin_user,
            kind      = 'registration_cancelled',
            title     = 'Club Admin Role Transferred',
            body      = (
                f'Your club admin role for {transfer.club.name} has been '
                f'transferred to {transfer.requester.username}.'
            ),
            club      = transfer.club,
        )

        return Response(
            {'detail': 'Transfer request approved successfully.'},
            status=status.HTTP_200_OK,
        )

    def _notify(self, recipient, kind, title, body, club):
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=recipient,
                kind=kind,
                title=title,
                body=body,
                club=club,
            )
        except Exception:
            pass


class TransferRequestRejectView(APIView):
    """System admin rejects a transfer request."""
    permission_classes = [IsSystemAdmin]

    def patch(self, request, pk):
        transfer = get_object_or_404(
            ClubAdminTransferRequest, pk=pk, status=ClubAdminTransferRequest.Status.PENDING
        )

        transfer.reject()

        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient = transfer.requester,
                kind      = 'registration_cancelled',
                title     = 'Transfer Request Rejected',
                body      = (
                    f'Your request to join {transfer.club.name} as a club admin '
                    f'has been rejected by the system admin.'
                ),
                club      = transfer.club,
            )
        except Exception:
            pass

        return Response(
            {'detail': 'Transfer request rejected.'},
            status=status.HTTP_200_OK,
        )


class AssignClubAdminView(APIView):
    """
    System admin only — assign a user as a club admin.

    POST /api/users/assign-club-admin/
    Body: { "user_id": "<uuid>", "club_id": "<uuid>", "position": "President" }

    - Changes the user's role to club_admin
    - Creates a ClubAdmin record (model enforces max 3 per club)
    """
    permission_classes = [IsSystemAdmin]

    def post(self, request):
        from users.models import Club, ClubAdmin
        from django.core.exceptions import ValidationError as DjangoValidationError

        user_id  = request.data.get('user_id')
        club_id  = request.data.get('club_id')
        position = request.data.get('position', '').strip()

        if not user_id or not club_id or not position:
            return Response(
                {'detail': 'user_id, club_id, and position are all required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_user = get_object_or_404(User, pk=user_id)
        club        = get_object_or_404(Club, pk=club_id)

        # If already a club admin for this club, return early
        if ClubAdmin.objects.filter(user=target_user, club=club).exists():
            return Response(
                {'detail': f'{target_user.username} is already an admin of {club.name}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # ClubAdmin.save() calls full_clean() which enforces the max-3 rule
            ClubAdmin.objects.create(
                user=target_user,
                club=club,
                position=position,
            )
        except DjangoValidationError as e:
            return Response(
                {'detail': ' '.join(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Promote role
        target_user.role = User.Role.CLUB_ADMIN
        target_user.save()

        return Response(
            {
                'detail': f'{target_user.username} has been assigned as {position} of {club.name}.',
                'user': target_user.username,
                'club': club.name,
                'position': position,
            },
            status=status.HTTP_201_CREATED,
        )
