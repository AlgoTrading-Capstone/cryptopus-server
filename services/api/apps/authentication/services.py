import pyotp
from django.core.cache import cache
from apps.authentication.models import User


class AuthService:

    @staticmethod
    def register_user(email: str, password: str, first_name: str, last_name: str) -> User:
        """Register a new user and send email verification code."""
        if User.objects.filter(email=email).exists():
            raise ValueError("Email already registered")

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Generate and cache email verification code (10 min TTL)
        verification_code = pyotp.random_base32()[:6].upper() # Generate a random 6-character verification code
        cache.set(f"email_verification:{user.id}", verification_code, timeout=600) #saved in cache with a key that includes the user's ID and a TTL of 10 minutes (redis will automatically delete the code after 10 minutes)

        # TODO: send verification email
        print(f"[DEV] Verification code for {email}: {verification_code}")

        return user

    @staticmethod
    def verify_email(email: str, verification_code: str) -> User:
        """Verify user email using the verification code."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("User not found")

        if user.email_verified:
            raise ValueError("Email already verified")

        cached_code = cache.get(f"email_verification:{user.id}")
        print(f"[DEV] user.id={user.id}")
        print(f"[DEV] Expected: {cached_code}, Got: {verification_code.upper()}")
        if cached_code is None:
            raise ValueError("Verification code expired")

        if cached_code != verification_code.upper():
            raise ValueError("Invalid verification code")

        user.email_verified = True
        user.save(update_fields=["email_verified"])

        cache.delete(f"email_verification:{user.id}")

        return user