from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.authentication.serializers import RegisterSerializer, VerifyEmailSerializer, UserResponseSerializer
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