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
            "dob": "1995-01-15",
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
            "dob": "1995-01-15",
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
        """Fully-registered user logs in and receives a temporary OTP session."""
        response = api_client.post("/api/auth/login", {
            "email": verified_user.email,
            "password": "StrongPass123!",
        }, format="json")

        assert response.status_code == 200
        data = response.data["data"]
        assert data["email_verified"] is True
        assert data["otp_verified"] is True
        assert data["temporary_session_id"]
        assert "otp_required" not in data

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
        """Login succeeds but signals unverified email + no temp session."""
        user = create_user(email_verified=False, otp_enabled=False)

        response = api_client.post("/api/auth/login", {
            "email": user.email,
            "password": "StrongPass123!",
        }, format="json")

        assert response.status_code == 200
        data = response.data["data"]
        assert data["email_verified"] is False
        assert data["otp_verified"] is False
        assert data["temporary_session_id"] is None

    def test_login_email_verified_otp_not_setup(self, api_client, create_user):
        """Login succeeds but signals OTP setup incomplete + no temp session."""
        user = create_user(email_verified=True, otp_enabled=False)

        response = api_client.post("/api/auth/login", {
            "email": user.email,
            "password": "StrongPass123!",
        }, format="json")

        assert response.status_code == 200
        data = response.data["data"]
        assert data["email_verified"] is True
        assert data["otp_verified"] is False
        assert data["temporary_session_id"] is None


@pytest.mark.django_db
class TestResendVerificationEmail:

    def test_resend_success_invalidates_old_code(self, api_client, create_user):
        """Resend issues a new code and invalidates the previous one."""
        user = create_user(email_verified=False, otp_enabled=False)
        cache.set(f"email_verification:{user.id}", "OLDCOD", timeout=600)

        response = api_client.post("/api/auth/resend-verification-email", {
            "email": user.email,
        }, format="json")

        assert response.status_code == 200
        data = response.data["data"]
        assert data["message"] == "Verification code resent."
        assert data["expires_in_seconds"] == 600
        assert data["cooldown_seconds"] == 30

        new_code = cache.get(f"email_verification:{user.id}")
        assert new_code is not None
        assert new_code != "OLDCOD"
        assert len(new_code) == 6

    def test_resend_user_not_found(self, api_client):
        """Resend returns 404 when no user exists for the email."""
        response = api_client.post("/api/auth/resend-verification-email", {
            "email": "nobody@cryptopus.com",
        }, format="json")

        assert response.status_code == 404
        assert response.data["error"] == "No such pending registration."

    def test_resend_already_verified(self, api_client, verified_user):
        """Resend returns 409 when the email is already verified."""
        response = api_client.post("/api/auth/resend-verification-email", {
            "email": verified_user.email,
        }, format="json")

        assert response.status_code == 409
        assert response.data["error"] == "Email already verified."

    def test_resend_cooldown_active(self, api_client, create_user):
        """Second resend within the cooldown window returns 429."""
        user = create_user(email_verified=False, otp_enabled=False)

        first = api_client.post("/api/auth/resend-verification-email", {
            "email": user.email,
        }, format="json")
        assert first.status_code == 200

        second = api_client.post("/api/auth/resend-verification-email", {
            "email": user.email,
        }, format="json")

        assert second.status_code == 429
        assert "error" in second.data

    def test_resend_invalid_email(self, api_client):
        """Resend returns 400 for malformed email input."""
        response = api_client.post("/api/auth/resend-verification-email", {
            "email": "not-an-email",
        }, format="json")

        assert response.status_code == 400


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