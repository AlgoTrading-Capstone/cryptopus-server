from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.authentication.serializers import (
    RegisterSerializer,
    VerifyEmailSerializer,
    UserResponseSerializer,
    SetupOtpSerializer,
    SetupOtpResponseSerializer,
    VerifyOtpSetupSerializer,
    LoginSerializer,
    LoginResponseSerializer,
    VerifyOtpSerializer,
    TokenResponseSerializer,
    RefreshTokenSerializer,
    RefreshTokenResponseSerializer,
    LogoutSerializer,
)
from apps.authentication.services import AuthService
from rest_framework.permissions import AllowAny

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """POST /api/auth/register"""
        serializer = RegisterSerializer(data=request.data) # Validate incoming data using the RegisterSerializer
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = AuthService.register_user(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
                first_name=serializer.validated_data["first_name"],
                last_name=serializer.validated_data["last_name"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": "success",
                "data": UserResponseSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """POST /api/auth/verify-email"""
        serializer = VerifyEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = AuthService.verify_email(
                email=serializer.validated_data["email"],
                verification_code=serializer.validated_data["verification_code"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": "success",
                "data": {
                    "email_verified": user.email_verified,
                    "otp_setup_required": True,
                    "message": "Email verified successfully.",
                },
            },
            status=status.HTTP_200_OK,
        )
class SetupOtpView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """POST /api/auth/setup-otp"""
        serializer = SetupOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = AuthService.setup_otp(
                email=serializer.validated_data["email"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": "success",
                "data": SetupOtpResponseSerializer(data).data,
            },
            status=status.HTTP_200_OK,
        )

class VerifyOtpSetupView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """POST /api/auth/verify-otp-setup"""
        serializer = VerifyOtpSetupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = AuthService.verify_otp_setup(
                email=serializer.validated_data["email"],
                otp_code=serializer.validated_data["otp_code"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": "success",
                "data": {
                    "otp_enabled": user.otp_enabled,
                    "message": "OTP enabled successfully. You can now log in.",
                },
            },
            status=status.HTTP_200_OK,
        )
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """POST /api/auth/login"""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = AuthService.login(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": "success",
                "data": LoginResponseSerializer(data).data,
            },
            status=status.HTTP_200_OK,
        )

class VerifyOtpView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """POST /api/auth/verify-otp"""
        serializer = VerifyOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = AuthService.verify_otp(
                temporary_session_id=serializer.validated_data["temporary_session_id"],
                otp_code=serializer.validated_data["otp_code"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": "success",
                "data": TokenResponseSerializer(data).data,
            },
            status=status.HTTP_200_OK,
        )

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """POST /api/auth/refresh"""
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = AuthService.refresh_token(
                refresh_token=serializer.validated_data["refresh_token"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": "success",
                "data": RefreshTokenResponseSerializer(data).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """POST /api/auth/logout"""
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            AuthService.logout(
                refresh_token=serializer.validated_data["refresh_token"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": "success",
                "data": {"message": "Logged out successfully."},
            },
            status=status.HTTP_200_OK,
        )