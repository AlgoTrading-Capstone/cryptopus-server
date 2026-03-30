from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.authentication.serializers import (
    RegisterSerializer,
    VerifyEmailSerializer,
    UserResponseSerializer,
    SetupOtpSerializer,
    SetupOtpResponseSerializer,
    VerifyOtpSetupSerializer)
from apps.authentication.services import AuthService


class RegisterView(APIView):

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