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