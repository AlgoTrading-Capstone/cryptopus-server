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