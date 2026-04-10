from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.portfolio.serializers import (
    TradeSerializer,
    TradesQuerySerializer,
    PerformanceQuerySerializer,
    EquityHistoryQuerySerializer,
)
from apps.portfolio.services import PortfolioService


class PortfolioSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/portfolio/summary"""
        data = PortfolioService.get_summary(user=request.user)
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class PortfolioTradesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/portfolio/trades"""
        serializer = TradesQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = PortfolioService.get_trades(
            user=request.user,
            page=serializer.validated_data["page"],
            page_size=serializer.validated_data["page_size"],
            symbol=serializer.validated_data.get("symbol"),
            from_date=serializer.validated_data.get("from_date"),
            to_date=serializer.validated_data.get("to_date"),
        )

        return Response(
            {
                "status": "success",
                "data": {
                    "items": TradeSerializer(result["items"], many=True).data,
                    "page": result["page"],
                    "page_size": result["page_size"],
                    "total_items": result["total_items"],
                },
            },
            status=status.HTTP_200_OK,
        )


class PortfolioPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/portfolio/performance"""
        serializer = PerformanceQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = PortfolioService.get_performance(
                user=request.user,
                range=serializer.validated_data["range"],
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class PortfolioEquityHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/portfolio/equity-history"""
        serializer = EquityHistoryQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = PortfolioService.get_equity_history(
            user=request.user,
            range=serializer.validated_data["range"],
            interval=serializer.validated_data["interval"],
        )

        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class PortfolioAllocationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/portfolio/allocations"""
        data = PortfolioService.get_allocations(user=request.user)
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)