import pyotp
import uuid
import random
import string
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from apps.authentication.models import User
from rest_framework_simplejwt.exceptions import TokenError
from django.core.mail import send_mail
from django.template.loader import render_to_string


class UserNotFoundError(Exception):
    """Raised when a lookup by email has no matching user."""


class AlreadyVerifiedError(Exception):
    """Raised when an action requires an unverified email but the user is already verified."""


class CooldownError(Exception):
    """Raised when an operation is rate-limited by an active cooldown."""


class AuthService:

    @staticmethod
    def register_user(email, password, first_name, last_name,
                      date_of_birth=None, phone_number=None,
                      address=None, city=None, country=None, postal_code=None):
        """Register a new user and send email verification code."""
        if User.objects.filter(email=email).exists():
            raise ValueError("Email already registered")

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        user.date_of_birth = date_of_birth
        user.phone_number = phone_number
        user.address = address
        user.city = city
        user.country = country
        user.postal_code = postal_code
        user.save(update_fields=[
            "date_of_birth", "phone_number", "address",
            "city", "country", "postal_code",
        ])

        verification_code = AuthService._generate_verification_code()
        cache.set(f"email_verification:{user.id}", verification_code, timeout=600)

        AuthService._send_verification_email(user.email, verification_code, first_name)
        return user

    @staticmethod
    def _send_verification_email(email: str, verification_code: str, first_name: str = ""):
        """Send verification email using HTML template."""


        html_message = render_to_string(
            "authentication/verify_email.html",
            {
                "first_name": first_name,
                "verification_code": verification_code,
            }
        )

        send_mail(
            subject="Verify your Cryptopus account",
            message=f"Your verification code is: {verification_code}",
            from_email="noreply@cryptopus.com",
            recipient_list=[email],
            html_message=html_message,
            fail_silently=True,
        )

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
    def _generate_verification_code() -> str:
        """Generate a 6-character alphanumeric verification code."""

        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

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
        """Validate credentials and branch on registration state.

        Returns email_verified and otp_verified flags so the client can resume
        registration at the correct step. A temporary_session_id is issued only
        when registration is fully complete.
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("Invalid credentials")

        if not user.check_password(password):
            raise ValueError("Invalid credentials")

        if user.account_status != User.AccountStatus.ACTIVE:
            raise ValueError("Account is suspended")

        if not user.email_verified:
            return {
                "email_verified": False,
                "otp_verified": False,
                "temporary_session_id": None,
                "message": "Email not verified. Please complete registration.",
            }

        if not user.otp_enabled:
            return {
                "email_verified": True,
                "otp_verified": False,
                "temporary_session_id": None,
                "message": "OTP setup not completed. Please finish registration.",
            }

        tmp_session_id = str(uuid.uuid4())
        cache.set(
            f"session:tmp:{tmp_session_id}",
            {"user_id": str(user.id), "email": user.email},
            timeout=300,
        )

        return {
            "email_verified": True,
            "otp_verified": True,
            "temporary_session_id": tmp_session_id,
            "message": "Password verified. OTP verification required.",
        }

    @staticmethod
    def resend_verification_email(email: str) -> dict:
        """Re-issue a fresh email verification code to a pending registration.

        Invalidates any previously issued code for this user. Rate-limited to
        one request per 30 seconds per email.
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise UserNotFoundError("No such pending registration.")

        if user.email_verified:
            raise AlreadyVerifiedError("Email already verified.")

        cooldown_key = f"resend_cooldown:{email.lower()}"
        if cache.get(cooldown_key) is not None:
            raise CooldownError("Too many requests. Please wait before requesting another code.")

        cache.delete(f"email_verification:{user.id}")

        verification_code = AuthService._generate_verification_code()
        cache.set(f"email_verification:{user.id}", verification_code, timeout=600)
        cache.set(cooldown_key, "1", timeout=30)

        AuthService._send_verification_email(user.email, verification_code, user.first_name)

        return {
            "message": "Verification code resent.",
            "expires_in_seconds": 600,
            "cooldown_seconds": 30,
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