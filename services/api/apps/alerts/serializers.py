from rest_framework import serializers
from apps.alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        """Serializer for Alert model.(without this class DFR will not work)"""

        model = Alert
        fields = [
            "id",
            "type",
            "title",
            "message",
            "severity",
            "read",
            "created_at",
        ]


class AlertsQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)
    unread_only = serializers.BooleanField(default=False)


class AlertPreferencesSerializer(serializers.Serializer):
    email_notifications = serializers.BooleanField()
    system_alerts = serializers.BooleanField()
    trade_alerts = serializers.BooleanField()
    risk_alerts = serializers.BooleanField()