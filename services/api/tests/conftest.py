import pytest
import pyotp
from rest_framework.test import APIClient
from apps.authentication.models import User
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def create_user():
    """Factory fixture — creates a verified user with OTP enabled."""
    def _create_user(
        email="test@cryptopus.com",
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
        email_verified=True,
        otp_enabled=True,
        role=User.Role.USER,
    ):
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        user.email_verified = email_verified
        user.otp_enabled = otp_enabled
        user.otp_secret = pyotp.random_base32()
        user.role = role
        user.save()
        return user
    return _create_user


@pytest.fixture
def verified_user(create_user):
    """A ready-to-login user."""
    return create_user()


@pytest.fixture
def admin_user(create_user):
    """An admin user."""
    return create_user(
        email="admin@cryptopus.com",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def authenticated_client(api_client, verified_user):
    """An API client authenticated as a regular user."""
    refresh = RefreshToken.for_user(verified_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """An API client authenticated as an admin user."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client