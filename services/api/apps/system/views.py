from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.db import connection


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """GET /api/health"""
        redis_status = "UP"
        try:
            cache.set("health_check", "ok", timeout=5)
            cache.get("health_check")
        except Exception:
            redis_status = "DOWN"

        db_status = "UP"
        try:
            connection.ensure_connection()
        except Exception:
            db_status = "DOWN"

        overall = "UP" if db_status == "UP" and redis_status == "UP" else "DEGRADED"

        return Response(
            {
                "status": "success",
                "data": {
                    "api": "UP",
                    "database": db_status,
                    "redis": redis_status,
                    "overall": overall,
                },
            },
            status=status.HTTP_200_OK if overall == "UP" else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class VersionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """GET /api/version"""
        return Response(
            {
                "status": "success",
                "data": {
                    "version": "1.0.0",
                    "service": "cryptopus-api",
                },
            },
            status=status.HTTP_200_OK,
        )