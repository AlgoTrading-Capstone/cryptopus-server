from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.alerts.serializers import (
    AlertSerializer,
    AlertsQuerySerializer,
    AlertPreferencesSerializer,
)
from apps.alerts.services import AlertService


class AlertsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/alerts"""
        serializer = AlertsQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = AlertService.get_alerts(
            user=request.user,
            page=serializer.validated_data["page"],
            page_size=serializer.validated_data["page_size"],
            unread_only=serializer.validated_data["unread_only"],
        )

        return Response(
            {
                "status": "success",
                "data": {
                    "items": AlertSerializer(result["items"], many=True).data,
                    "page": result["page"],
                    "page_size": result["page_size"],
                    "total_items": result["total_items"],
                },
            },
            status=status.HTTP_200_OK,
        )


class AlertMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, alert_id):
        """PATCH /api/alerts/{alert_id}/read"""
        try:
            alert = AlertService.mark_as_read(
                user=request.user,
                alert_id=alert_id,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "status": "success",
                "data": AlertSerializer(alert).data,
            },
            status=status.HTTP_200_OK,
        )


class AlertPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/alerts/preferences"""
        data = AlertService.get_preferences(user=request.user)
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)

    def put(self, request):
        """PUT /api/alerts/preferences"""
        serializer = AlertPreferencesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = AlertService.update_preferences(
            user=request.user,
            preferences=serializer.validated_data,
        )

        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)