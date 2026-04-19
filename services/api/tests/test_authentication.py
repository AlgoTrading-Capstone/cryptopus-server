import pytest
from django.core.cache import cache
from apps.authentication.models import User
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
class TestRegister:

    def test_register_success(self, api_client):
        """New user can register with valid data."""
        response = api_client.post("/api/auth/register", {
            "email": "new@cryptopus.com",
            "password": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
            "date_of_birth": "1995-01-15",
            "phone_number": "+15551234567",
            "address": "123 Main St",
            "city": "Tel Aviv",
            "country": "Israel",
            "postal_code": "6100000",
        }, format="json")

        assert response.status_code == 201
        assert response.data["status"] == "success"
        assert response.data["data"]["email"] == "new@cryptopus.com"
        assert User.objects.filter(email="new@cryptopus.com").exists()

    def test_register_duplicate_email(self, api_client, verified_user):
        """Cannot register with an already existing email."""
        response = api_client.post("/api/auth/register", {
            "email": verified_user.email,
            "password": "StrongPass123!",
            "first_name": "Test",
            "last_name": "User",
            "date_of_birth": "1995-01-15",
            "phone_number": "+15551234567",
            "address": "123 Main St",
            "city": "Tel Aviv",
            "country": "Israel",
            "postal_code": "6100000",
        }, format="json")

        assert response.status_code == 400
        assert "error" in response.data

    def test_register_missing_fields(self, api_client):
        """Registration fails when required fields are missing."""
        response = api_client.post("/api/auth/register", {
            "email": "new@cryptopus.com",
        }, format="json")

        assert response.status_code == 400

    def test_register_invalid_email(self, api_client):
        """Registration fails with invalid email format."""
        response = api_client.post("/api/auth/register", {
            "email": "not-an-email",
            "password": "StrongPass123!",
            "first_name": "Test",
            "last_name": "User",
        }, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestVerifyEmail:

    def test_verify_email_success(self, api_client, create_user):
        """User can verify email with correct code."""
        user = create_user(email_verified=False, otp_enabled=False)
        code = "ABC123"
        cache.set(f"email_verification:{user.id}", code, timeout=600)

        response = api_client.post("/api/auth/verify-email", {
            "email": user.email,
            "verification_code": code,
        }, format="json")

        assert response.status_code == 200
        assert response.data["data"]["email_verified"] is True
        user.refresh_from_db()
        assert user.email_verified is True

    def test_verify_email_wrong_code(self, api_client, create_user):
        """Verification fails with wrong code."""
        user = create_user(email_verified=False, otp_enabled=False)
        cache.set(f"email_verification:{user.id}", "CORRECT", timeout=600)

        response = api_client.post("/api/auth/verify-email", {
            "email": user.email,
            "verification_code": "WRONGG",
        }, format="json")

        assert response.status_code == 400
        assert "error" in response.data

    def test_verify_email_expired_code(self, api_client, create_user):
        """Verification fails when code is expired (not in cache)."""
        user = create_user(email_verified=False, otp_enabled=False)

        response = api_client.post("/api/auth/verify-email", {
            "email": user.email,
            "verification_code": "ABC123",
        }, format="json")

        assert response.status_code == 400
        assert response.data["error"] == "Verification code expired"

    def test_verify_email_already_verified(self, api_client, verified_user):
        """Cannot verify an already verified email."""
        response = api_client.post("/api/auth/verify-email", {
            "email": verified_user.email,
            "verification_code": "ABC123",
        }, format="json")

        assert response.status_code == 400
        assert response.data["error"] == "Email already verified"


@pytest.mark.django_db
class TestLogin:

    def test_login_success(self, api_client, verified_user):
        """User can login with correct credentials."""
        response = api_client.post("/api/auth/login", {
            "email": verified_user.email,
            "password": "StrongPass123!",
        }, format="json")

        assert response.status_code == 200
        assert "temporary_session_id" in response.data["data"]
        assert response.data["data"]["otp_required"] is True

    def test_login_wrong_password(self, api_client, verified_user):
        """Login fails with wrong password."""
        response = api_client.post("/api/auth/login", {
            "email": verified_user.email,
            "password": "WrongPassword!",
        }, format="json")

        assert response.status_code == 400
        assert "error" in response.data

    def test_login_nonexistent_user(self, api_client):
        """Login fails for non-existent user."""
        response = api_client.post("/api/auth/login", {
            "email": "nobody@cryptopus.com",
            "password": "StrongPass123!",
        }, format="json")

        assert response.status_code == 400

    def test_login_unverified_email(self, api_client, create_user):
        """Login fails if email is not verified."""
        user = create_user(email_verified=False)

        response = api_client.post("/api/auth/login", {
            "email": user.email,
            "password": "StrongPass123!",
        }, format="json")

        assert response.status_code == 400
        assert response.data["error"] == "Email not verified"


@pytest.mark.django_db
class TestLogout:

    def test_logout_success(self, api_client, verified_user):
        """User can logout with valid refresh token."""
        refresh = RefreshToken.for_user(verified_user)

        response = api_client.post("/api/auth/logout", {
            "refresh_token": str(refresh),
        }, format="json")

        assert response.status_code == 200
        assert response.data["data"]["message"] == "Logged out successfully."

    def test_logout_invalid_token(self, api_client):
        """Logout fails with invalid token."""
        response = api_client.post("/api/auth/logout", {
            "refresh_token": "invalid.token.here",
        }, format="json")

        assert response.status_code == 400