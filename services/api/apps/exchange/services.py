from django.utils import timezone
from apps.authentication.models import User
from apps.exchange.models import ExchangeConnection
import ccxt

class ExchangeService:
    """Service class for managing exchange connections, specifically Kraken in this implementation.
    The flow: get_onboarding_info → connect → get_status → validate → disconnect"""
    @staticmethod
    def get_onboarding_info() -> dict:
        """Return Kraken connection instructions for the client."""
        return {
            "exchange": "KRAKEN",
            "required_permissions": [
                "Read Balance",
                "Read Trades",
                "Open/Close Positions",
            ],
            "instructions": "Create API key in Kraken dashboard and paste credentials.",
            "docs_url": "https://support.kraken.com",
        }

    @staticmethod
    def connect(user: User, api_key: str, api_secret: str) -> ExchangeConnection:
        """Store Kraken API credentials for the user."""
        existing = ExchangeConnection.objects.filter(
            user=user,
            deleted_at__isnull=True,
        ).first() #this checks if there is already an active connection for the user. If there is, it raises a ValueError to prevent multiple connections. If not, it creates a new ExchangeConnection object with the provided API credentials and marks it as connected.

        if existing:
            raise ValueError("Exchange already connected. Disconnect first.")

        connection = ExchangeConnection.objects.create(
            user=user,
            exchange=ExchangeConnection.Exchange.KRAKEN,
            api_key_encrypted=api_key,       # TODO: encrypt with AWS Secrets Manager
            api_secret_encrypted=api_secret, # TODO: encrypt with AWS Secrets Manager
            connected=True,
        )

        return connection

    @staticmethod
    def get_status(user: User) -> ExchangeConnection:
        """Return current connection status from DB."""
        connection = ExchangeConnection.objects.filter(
            user=user,
            deleted_at__isnull=True,
        ).first()

        if not connection:
            raise ValueError("No exchange connection found")

        return connection

    @staticmethod
    def validate(user: User, connection_id: str) -> ExchangeConnection:
        """Validate Kraken credentials by making a test API call."""
        try:
            connection = ExchangeConnection.objects.get(
                id=connection_id,
                user=user,
                deleted_at__isnull=True,
            )
        except ExchangeConnection.DoesNotExist:
            raise ValueError("Connection not found")

        try:
            kraken = ccxt.kraken({
                "apiKey": connection.api_key_encrypted,
                "secret": connection.api_secret_encrypted,
            })
            kraken.fetch_balance()  # Test call — throws if credentials are invalid

            connection.validated = True
            connection.last_checked_at = timezone.now()
            connection.save(update_fields=["validated", "last_checked_at"])

        except Exception:
            raise ValueError("Invalid Kraken credentials")

        return connection

    @staticmethod
    def disconnect(user: User, connection_id: str) -> None:
        """Soft delete the exchange connection.
        DB effect: Sets deleted_at=now() on the connection row. The row is NOT deleted from the DB.
        Why soft delete and not hard delete?
        The connection row is preserved for audit trail and historical traceability.
        After a soft delete, all queries that filter by deleted_at__isnull=True will ignore this row —
        effectively treating it as deleted without losing the data.
        No Kraken API call is made. If the user wants to fully revoke the API key,
        they do that manually from their Kraken dashboard.
        """
        try:
            connection = ExchangeConnection.objects.get(
                id=connection_id,
                user=user,
                deleted_at__isnull=True,
            )
        except ExchangeConnection.DoesNotExist:
            raise ValueError("Connection not found")

        connection.deleted_at = timezone.now()
        connection.save(update_fields=["deleted_at"])