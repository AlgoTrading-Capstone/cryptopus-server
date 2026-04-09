from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.exchange.serializers import (
    ConnectExchangeSerializer,
    ValidateExchangeSerializer,
    DisconnectExchangeSerializer,
    ExchangeConnectionResponseSerializer,
)
from apps.exchange.services import ExchangeService


class KrakenOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/exchange/kraken/onboarding"""
        data = ExchangeService.get_onboarding_info()
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class KrakenConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """POST /api/exchange/kraken/connect"""
        serializer = ConnectExchangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            connection = ExchangeService.connect(
                user=request.user,
                api_key=serializer.validated_data["api_key"],
                api_secret=serializer.validated_data["api_secret"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"status": "success", "data": ExchangeConnectionResponseSerializer(connection).data},
            status=status.HTTP_201_CREATED,
        )


class KrakenStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/exchange/kraken/status"""
        try:
            connection = ExchangeService.get_status(user=request.user)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"status": "success", "data": ExchangeConnectionResponseSerializer(connection).data},
            status=status.HTTP_200_OK,
        )


class KrakenValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """POST /api/exchange/kraken/validate"""
        serializer = ValidateExchangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            connection = ExchangeService.validate(
                user=request.user,
                connection_id=serializer.validated_data["connection_id"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"status": "success", "data": ExchangeConnectionResponseSerializer(connection).data},
            status=status.HTTP_200_OK,
        )


class KrakenDisconnectView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """DELETE /api/exchange/kraken/disconnect"""
        serializer = DisconnectExchangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            ExchangeService.disconnect(
                user=request.user,
                connection_id=serializer.validated_data["connection_id"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"status": "success", "data": {"disconnected": True, "message": "Kraken account disconnected successfully."}},
            status=status.HTTP_200_OK,
        )