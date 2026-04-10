from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class HelpOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/help/overview"""
        return Response(
            {
                "status": "success",
                "data": {
                    "title": "Cryptopus Overview",
                    "sections": [
                        "What is Cryptopus",
                        "How automated trading works",
                        "How to connect Kraken",
                        "How to start trading safely",
                    ],
                },
            },
            status=status.HTTP_200_OK,
        )


class HelpStrategiesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/help/strategies"""
        return Response(
            {
                "status": "success",
                "data": {
                    "strategies": [
                        {
                            "name": "Momentum",
                            "description": "Trades in the direction of recent price strength.",
                        },
                        {
                            "name": "Mean Reversion",
                            "description": "Assumes price may return to an average range.",
                        },
                        {
                            "name": "Volatility Breakout",
                            "description": "Enters trades when price breaks out of a range.",
                        },
                    ]
                },
            },
            status=status.HTTP_200_OK,
        )


class HelpRiskManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/help/risk-management"""
        return Response(
            {
                "status": "success",
                "data": {
                    "topics": [
                        "Position sizing",
                        "Diversification",
                        "Drawdown awareness",
                        "Allocation limits",
                    ]
                },
            },
            status=status.HTTP_200_OK,
        )


class HelpFaqView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/help/faq"""
        return Response(
            {
                "status": "success",
                "data": {
                    "items": [
                        {
                            "question": "Why can't I start trading?",
                            "answer": "Make sure your Kraken account is connected and validated.",
                        },
                        {
                            "question": "Why do I need OTP?",
                            "answer": "OTP adds an extra security layer for account access.",
                        },
                        {
                            "question": "How is my money protected?",
                            "answer": "Your funds stay in your Kraken account. We only trade on your behalf using API keys.",
                        },
                    ]
                },
            },
            status=status.HTTP_200_OK,
        )