from django.core.cache import cache
from apps.authentication.models import User
from apps.alerts.models import Alert


class AlertService:

    @staticmethod
    def get_alerts(user: User, page: int = 1, page_size: int = 20,
                   unread_only: bool = False) -> dict:
        """Return paginated alerts for the user."""
        queryset = Alert.objects.filter(user=user)

        if unread_only:
            queryset = queryset.filter(read=False)

        total_items = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        alerts = queryset[start:end]

        return {
            "items": alerts,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
        }

    @staticmethod
    def mark_as_read(user: User, alert_id: str) -> Alert:
        """Mark a specific alert as read."""
        try:
            alert = Alert.objects.get(id=alert_id, user=user)
        except Alert.DoesNotExist:
            raise ValueError("Alert not found")

        alert.read = True
        alert.save(update_fields=["read"])
        return alert

    @staticmethod
    def get_preferences(user: User) -> dict:
        """Return user alert preferences from Redis."""
        cached = cache.get(f"alerts:preferences:{user.id}")
        if cached:
            return cached

        # Default preferences
        return {
            "email_notifications": True,
            "system_alerts": True,
            "trade_alerts": True,
            "risk_alerts": True,
        }

    @staticmethod
    def update_preferences(user: User, preferences: dict) -> dict:
        """Update user alert preferences in Redis."""
        cache.set(
            f"alerts:preferences:{user.id}",
            preferences,
            timeout=None,
        )
        return preferences

    @staticmethod
    def create_alert(user: User, alert_type: str, title: str,
                     message: str, severity: str = "INFO") -> Alert:
        """Create a new alert and publish to Redis Pub/Sub."""
        alert = Alert.objects.create(
            user=user,
            type=alert_type,
            title=title,
            message=message,
            severity=severity,
        )

        # Publish to Redis for WebSocket delivery
        cache.publish(
            f"events:alerts:{user.id}",
            {
                "event": "USER_ALERT",
                "data": {
                    "alert_id": str(alert.id),
                    "type": alert.type,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "read": alert.read,
                },
            }
        ) if hasattr(cache, 'publish') else None

        return alert