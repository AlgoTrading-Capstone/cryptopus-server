import uuid
from django.db import models
from apps.authentication.models import User


class Trade(models.Model):

    class Side(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="trades")
    symbol = models.TextField(default="BTC/USD")
    side = models.CharField(max_length=5, choices=Side.choices)
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    price = models.DecimalField(max_digits=18, decimal_places=2)
    fee = models.DecimalField(max_digits=18, decimal_places=8, default=0.00)
    realized_pnl = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    executed_at = models.DateTimeField()
    kraken_order_id = models.TextField(null=True, blank=True, unique=True)

    class Meta:
        db_table = "trades"
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.user} - {self.side} {self.quantity} {self.symbol}"


class Position(models.Model):

    class Side(models.TextChoices):
        """In trades — side means the direction of the order: BUY or SELL
            In positions — side means the direction of the position: LONG or SHORT"""
        LONG = "LONG", "Long"
        SHORT = "SHORT", "Short"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="positions")
    symbol = models.TextField(default="BTC/USD")
    side = models.CharField(max_length=5, choices=Side.choices)
    size_btc = models.DecimalField(max_digits=18, decimal_places=8)
    entry_price = models.DecimalField(max_digits=18, decimal_places=2)
    exit_price = models.DecimalField(max_digits=18, decimal_places=2)
    realized_pnl = models.DecimalField(max_digits=18, decimal_places=2)
    opened_at = models.DateTimeField()
    closed_at = models.DateTimeField()
    duration_seconds = models.IntegerField()

    class Meta:
        db_table = "positions"
        ordering = ["-closed_at"]

    def __str__(self):
        return f"{self.user} - {self.side} {self.size_btc} {self.symbol}"