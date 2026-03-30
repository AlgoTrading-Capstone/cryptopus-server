from rest_framework import serializers
from apps.authentication.models import User


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification."""
    email = serializers.EmailField()
    verification_code = serializers.CharField(min_length=6, max_length=6)


class UserResponseSerializer(serializers.ModelSerializer):
    """Serializer for user response data."""
    class Meta:
        model = User
        fields = ["id", "email", "created_at"]

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
    otp_required = serializers.BooleanField()
    temporary_session_id = serializers.CharField()
    message = serializers.CharField()

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