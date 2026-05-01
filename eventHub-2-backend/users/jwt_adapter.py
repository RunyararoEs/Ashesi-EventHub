"""
users/jwt_adapter.py

Adapter Pattern — JWT Authentication Wrapper
---------------------------------------------
The Adapter pattern converts the interface of a class (or library) into
another interface that callers expect. It lets incompatible interfaces
work together without modifying the original class.

Here, the Subject (the thing being adapted) is djangorestframework-simplejwt.
simplejwt has its own API: RefreshToken, AccessToken, TokenError, etc.
The rest of EventHub's code should never import from simplejwt directly —
if the library ever needs to be swapped out (e.g. for PyJWT, or a custom
implementation), only this file changes.

The Adapter exposes a clean, library-agnostic interface:
    JWTAdapter.login(email, password)   → {'access': str, 'refresh': str}
    JWTAdapter.refresh(refresh_token)   → {'access': str}
    JWTAdapter.get_user(access_token)   → User instance

All callers (views, tests) talk to JWTAdapter — none of them import
from rest_framework_simplejwt directly.
"""

from django.contrib.auth import authenticate, get_user_model

# All simplejwt imports are isolated here in the adapter.
# Nothing outside this file should import from rest_framework_simplejwt.
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

User = get_user_model()


class AuthenticationError(Exception):
    """Raised when credentials are invalid. Library-agnostic."""
    pass


class TokenRefreshError(Exception):
    """Raised when a refresh token is invalid or expired. Library-agnostic."""
    pass


class JWTAdapter:
    """
    Adapter that wraps djangorestframework-simplejwt behind a stable,
    library-agnostic interface.

    All methods are static — the adapter has no instance state.
    """

    @staticmethod
    def login(email, password):
        """
        Authenticate a user with email and password.

        Returns:
            dict: {'access': <access_token_str>, 'refresh': <refresh_token_str>}

        Raises:
            AuthenticationError: if credentials are invalid or user is inactive.
        """
        user = authenticate(username=email, password=password)

        if user is None:
            raise AuthenticationError('Invalid email or password.')

        if not user.is_active:
            raise AuthenticationError('This account has been deactivated.')

        # simplejwt detail: RefreshToken.for_user() generates both tokens
        refresh = RefreshToken.for_user(user)

        return {
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        }

    @staticmethod
    def refresh(refresh_token_str):
        """
        Generate a new access token from a valid refresh token.

        Args:
            refresh_token_str (str): The raw refresh token string.

        Returns:
            dict: {'access': <new_access_token_str>}

        Raises:
            TokenRefreshError: if the refresh token is invalid or expired.
        """
        try:
            # simplejwt detail: instantiating RefreshToken validates it
            refresh = RefreshToken(refresh_token_str)
            return {
                'access': str(refresh.access_token),
            }
        except (TokenError, InvalidToken) as e:
            raise TokenRefreshError(str(e))

    @staticmethod
    def get_user_from_token(access_token_str):
        """
        Decode an access token and return the corresponding User.

        Args:
            access_token_str (str): The raw access token string.

        Returns:
            User: the authenticated user.

        Raises:
            TokenRefreshError: if the token is invalid, expired, or the
                               user no longer exists.
        """
        try:
            token = AccessToken(access_token_str)
            user_id = token['user_id']
            user = User.objects.get(pk=user_id)
            return user
        except (TokenError, InvalidToken, User.DoesNotExist) as e:
            raise TokenRefreshError(str(e))
