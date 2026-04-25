from rest_framework import serializers
from apps.authentication.models import User


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    dob = serializers.DateField()
    phone_number = serializers.CharField(max_length=20)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification."""
    email = serializers.EmailField()
    verification_code = serializers.CharField(min_length=6, max_length=6)


class UserResponseSerializer(serializers.ModelSerializer):
    """Serializer for user response data."""
    user_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = User
        fields = ["user_id", "email", "created_at"]

class SetupOtpSerializer(serializers.Serializer):
    """Serializer for OTP setup."""
    email = serializers.EmailField()


class SetupOtpResponseSerializer(serializers.Serializer):
    """Serializer for OTP setup response."""
    otp_secret = serializers.CharField()
    qr_code_url = serializers.CharField()
    message = serializers.CharField()

class VerifyOtpSetupSerializer(serializers.Serializer):
    """Serializer for verifying OTP setup."""
    email = serializers.EmailField()
    otp_code = serializers.CharField(min_length=6, max_length=6)

class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response."""
    email_verified = serializers.BooleanField()
    otp_verified = serializers.BooleanField()
    temporary_session_id = serializers.CharField(allow_null=True, required=False)
    message = serializers.CharField()


class ResendVerificationEmailSerializer(serializers.Serializer):
    """Serializer for resending the email verification code."""
    email = serializers.EmailField()


class ResendVerificationEmailResponseSerializer(serializers.Serializer):
    """Serializer for resend verification email response."""
    message = serializers.CharField()
    expires_in_seconds = serializers.IntegerField()
    cooldown_seconds = serializers.IntegerField()

class VerifyOtpSerializer(serializers.Serializer):
    """Serializer for verifying OTP during login."""
    temporary_session_id = serializers.CharField()
    otp_code = serializers.CharField(min_length=6, max_length=6)


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response after successful login."""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    expires_in = serializers.IntegerField()
    user_id = serializers.CharField()

class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for refreshing access token."""
    refresh_token = serializers.CharField()


class RefreshTokenResponseSerializer(serializers.Serializer):
    """Serializer for refresh token response."""
    access_token = serializers.CharField()
    expires_in = serializers.IntegerField()


class LogoutSerializer(serializers.Serializer):
    """Serializer for user logout."""
    refresh_token = serializers.CharField()