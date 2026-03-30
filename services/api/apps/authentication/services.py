import pyotp
import uuid
import json
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from apps.authentication.models import User
from rest_framework_simplejwt.exceptions import TokenError


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

    @staticmethod
    def setup_otp(email: str) -> dict:
        """Generate OTP secret and return QR code URL for authenticator app."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("User not found")

        if not user.email_verified:
            raise ValueError("Email not verified")

        if user.otp_enabled:
            raise ValueError("OTP already configured")

        # Generate OTP secret and save to user
        otp_secret = pyotp.random_base32() # Generate a random base32 string to be used as the OTP secret key for the user. This secret will be shared between the server and the user's authenticator app (like Google Authenticator or Authy) to generate time-based one-time passwords (TOTPs).
        user.otp_secret = otp_secret
        user.save(update_fields=["otp_secret"]) #save the generated OTP secret to the user's record in the database, but only update the otp_secret field for efficiency

        # Generate QR code URL for Google Authenticator / Authy
        totp = pyotp.TOTP(otp_secret)
        qr_code_url = totp.provisioning_uri(
            name=user.email,
            issuer_name="Cryptopus"
        )

        return {
            "otp_secret": otp_secret,
            "qr_code_url": qr_code_url,
            "message": "OTP setup initialized successfully.",
        }

    @staticmethod
    def verify_otp_setup(email: str, otp_code: str) -> User:
        """Verify OTP code during setup and enable OTP for the user."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("User not found")

        if not user.otp_secret:
            raise ValueError("OTP setup not initialized")

        if user.otp_enabled:
            raise ValueError("OTP already enabled")

        # Verify the code against the secret
        totp = pyotp.TOTP(user.otp_secret)
        if not totp.verify(otp_code):
            raise ValueError("Invalid OTP code")

        user.otp_enabled = True
        user.save(update_fields=["otp_enabled"])

        return user

    @staticmethod
    def login(email: str, password: str) -> dict:
        """Validate credentials and return temporary session for OTP verification."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("Invalid credentials")

        if not user.check_password(password):
            raise ValueError("Invalid credentials")

        if not user.email_verified:
            raise ValueError("Email not verified")

        if user.account_status != User.AccountStatus.ACTIVE:
            raise ValueError("Account is suspended")

        # Create temporary session in Redis - valid for 5 minutes
        tmp_session_id = str(uuid.uuid4()) #128-character unique identifier for the temporary session, generated using UUID4 which creates a random UUID. This ID will be used as a key in Redis to store the temporary session data for OTP verification.
        cache.set(
            f"session:tmp:{tmp_session_id}",
            {"user_id": str(user.id), "email": user.email},
            timeout=300, #5 minutes (300 seconds)
        )

        return {
            "otp_required": True,
            "temporary_session_id": tmp_session_id,
            "message": "Password verified. OTP verification required.",
        }

    @staticmethod
    def verify_otp(temporary_session_id: str, otp_code: str) -> dict:
        """Verify OTP code and issue JWT tokens."""
        # Get temporary session from Redis
        session_data = cache.get(f"session:tmp:{temporary_session_id}")
        if session_data is None:
            raise ValueError("Session expired or invalid")

        # Get user
        try:
            user = User.objects.get(id=session_data["user_id"])
        except User.DoesNotExist:
            raise ValueError("User not found")

        # Verify OTP code
        totp = pyotp.TOTP(user.otp_secret)
        if not totp.verify(otp_code):
            raise ValueError("Invalid OTP code")

        # Delete temporary session — one time use
        cache.delete(f"session:tmp:{temporary_session_id}")

        # Issue JWT tokens
        refresh = RefreshToken.for_user(user) # Generate a new refresh token for the authenticated user. The RefreshToken class is part of the Simple JWT library and provides a convenient way to create JWT tokens for a user. The for_user method takes a user instance and generates a refresh token that can be used to obtain access tokens for authenticated API requests.
        access_token = str(refresh.access_token) # Generate an access token from the refresh token. The access token is a short-lived token that can be used to authenticate API requests. The access_token property of the RefreshToken instance generates a new access token based on the refresh token's payload and the user's information.
        refresh_token = str(refresh) # Convert the refresh token to a string. The RefreshToken instance can be directly converted to a string, which will give you the actual token value that can be sent to the client.

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,
            "user_id": str(user.id),
        }

    @staticmethod
    def refresh_token(refresh_token: str) -> dict:
        """Issue a new access token using a valid refresh token."""
        try:
            refresh = RefreshToken(refresh_token) # Create a RefreshToken instance from the provided refresh token string. This will validate the token and decode its payload. If the token is invalid or expired, it will raise a TokenError.
            new_access_token = str(refresh.access_token)
        except TokenError:
            raise ValueError("Invalid or expired refresh token")

        return {
            "access_token": new_access_token,
            "expires_in": 3600, #3600 seconds (1 hour)
        }

    @staticmethod
    def logout(refresh_token: str) -> None:
        """Blacklist the refresh token to invalidate the session."""

        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist() # The blacklist() method is used to add the refresh token to a blacklist, which is a mechanism provided by the Simple JWT library to invalidate tokens. When a token is blacklisted, it cannot be used to obtain new access tokens or refresh existing ones, effectively logging the user out and preventing further use of that token.
        except TokenError:
            raise ValueError("Invalid or expired refresh token")