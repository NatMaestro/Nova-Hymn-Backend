"""
Custom authentication classes that allow anonymous access
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class OptionalJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that doesn't raise exceptions for anonymous users.
    Allows requests without tokens when AllowAny permission is set.
    """
    def authenticate(self, request):
        """
        Returns a two-tuple of (user, token) if authentication succeeds,
        or None if no token is provided (allowing anonymous access).
        """
        header = self.get_header(request)
        if header is None:
            # No token provided - allow anonymous access
            return None
        
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            # Invalid token format - allow anonymous access
            return None
        
        try:
            # Try to validate the token
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except AuthenticationFailed:
            # Invalid token - allow anonymous access instead of raising exception
            return None
        except Exception:
            # Any other error - allow anonymous access
            return None

