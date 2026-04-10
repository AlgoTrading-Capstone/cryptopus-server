import uuid
from django.db import models
from apps.authentication.models import User


class Alert(models.Model):

    class AlertType(models.TextChoices):
        TRADE_EXECUTED = "TRADE_EXECUTED", "Trade Executed"
        SYSTEM_WARNING = "SYSTEM_WARNING", "System Warning"
        RISK_ALERT = "RISK_ALERT", "Risk Alert"
        INFO = "INFO", "Info"

    class Severity(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alerts")
    type = models.CharField(max_length=20, choices=AlertType.choices)
    title = models.TextField()
    message = models.TextField()
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.INFO,
    )
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "alerts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.type} - {self.title}"