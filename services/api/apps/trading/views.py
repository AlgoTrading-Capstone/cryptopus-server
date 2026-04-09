from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.trading.serializers import (
    AllocateSerializer,
    WithdrawSerializer,
    ToggleSerializer,
    TradingAccountResponseSerializer,
)
from apps.trading.services import TradingService


class AllocateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """POST /api/trading/allocate"""
        serializer = AllocateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = TradingService.allocate(
                user=request.user,
                amount=serializer.validated_data["amount"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"status": "success", "data": TradingAccountResponseSerializer(account).data},
            status=status.HTTP_200_OK,
        )


class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """POST /api/trading/withdraw"""
        serializer = WithdrawSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = TradingService.withdraw(
                user=request.user,
                amount=serializer.validated_data["amount_usd"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"status": "success", "data": TradingAccountResponseSerializer(account).data},
            status=status.HTTP_200_OK,
        )


class ToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """POST /api/trading/toggle"""
        serializer = ToggleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = TradingService.toggle(
                user=request.user,
                desired_state=serializer.validated_data["desired_state"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"status": "success", "data": TradingAccountResponseSerializer(account).data},
            status=status.HTTP_200_OK,
        )


class TradingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/trading/status"""
        account = TradingService.get_status(user=request.user)

        return Response(
            {"status": "success", "data": TradingAccountResponseSerializer(account).data},
            status=status.HTTP_200_OK,
        )