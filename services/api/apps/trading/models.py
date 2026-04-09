import uuid
from django.db import models
from apps.authentication.models import User


class TradingAccount(models.Model):

    class TradingState(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        STOPPED = "STOPPED", "Stopped"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name="trading_account")
    allocated_usd = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    trading_state = models.CharField(max_length=10, choices=TradingState.choices, default=TradingState.STOPPED)
    state_changed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "trading_accounts"

    def __str__(self):
        return f"{self.user} - {self.trading_state}"