import uuid
from django.db import models
from apps.authentication.models import User


class ExchangeConnection(models.Model):

    class Exchange(models.TextChoices):
        KRAKEN = "KRAKEN", "Kraken"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="exchange_connections")
    exchange = models.CharField(max_length=20, choices=Exchange.choices, default=Exchange.KRAKEN)
    api_key_encrypted = models.TextField()
    api_secret_encrypted = models.TextField()
    connected = models.BooleanField(default=False)
    validated = models.BooleanField(default=False)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "exchange_connections"

    def __str__(self):
        return f"{self.user} - {self.exchange}"