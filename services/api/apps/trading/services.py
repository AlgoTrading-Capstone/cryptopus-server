from decimal import Decimal #use for precise financial calculations
from django.utils import timezone
from django.core.cache import cache
from apps.authentication.models import User
from apps.trading.models import TradingAccount


class TradingService:

    @staticmethod
    def _get_or_create_account(user: User) -> TradingAccount:
        """Get existing trading account or create one for the user."""
        account, created = TradingAccount.objects.get_or_create(user=user)
        return account

    @staticmethod
    def allocate(user: User, amount: float) -> TradingAccount:
        """Allocate USD amount for the RL agent to trade with."""
        amount = Decimal(str(amount))

        if amount <= 0: #TODO: defiene minimum allocation amount needed to start trading (e.g. $100) and enforce it here
            raise ValueError("Amount must be greater than 0")

        account = TradingService._get_or_create_account(user)
        account.allocated_usd += amount
        account.updated_at = timezone.now()
        account.save(update_fields=["allocated_usd", "updated_at"])

        # Sync state to Redis for fast engine access
        cache.set(
            f"trading:state:{user.id}",
            {
                "state": account.trading_state,
                "allocated_usd": str(account.allocated_usd),
                "changed_at": str(account.state_changed_at),
            },
            timeout=None,
        )

        return account

    @staticmethod
    def withdraw(user: User, amount: float) -> TradingAccount:
        """Withdraw USD amount from the allocated trading balance."""
        amount = Decimal(str(amount))

        if amount <= 0: #TODO: define minimum withdrawal amount (e.g. $50) and enforce it here
            raise ValueError("Amount must be greater than 0")

        account = TradingService._get_or_create_account(user)

        if amount > account.allocated_usd:
            raise ValueError("Insufficient allocated balance")

        account.allocated_usd -= amount
        account.save(update_fields=["allocated_usd", "updated_at"])

        # Sync state to Redis
        cache.set(
            f"trading:state:{user.id}",
            {
                "state": account.trading_state,
                "allocated_usd": str(account.allocated_usd),
                "changed_at": str(account.state_changed_at),
            },
            timeout=None,
        )

        return account

    @staticmethod
    def toggle(user: User, desired_state: str) -> TradingAccount:
        """Start or stop the RL trading agent for the user."""
        if desired_state not in ["START", "STOP"]:
            raise ValueError("desired_state must be START or STOP")

        account = TradingService._get_or_create_account(user)

        if desired_state == "START":
            if account.allocated_usd <= 0:
                raise ValueError("Cannot start trading with zero allocated balance")
            account.trading_state = TradingAccount.TradingState.RUNNING
        else:
            account.trading_state = TradingAccount.TradingState.STOPPED

        account.state_changed_at = timezone.now()
        account.save(update_fields=["trading_state", "state_changed_at", "updated_at"])

        # Sync state to Redis
        cache.set(
            f"trading:state:{user.id}",
            {
                "state": account.trading_state,
                "allocated_usd": str(account.allocated_usd),
                "changed_at": str(account.state_changed_at),
            },
            timeout=None,
        )

        return account

    @staticmethod
    def get_status(user: User) -> TradingAccount:
        """Get current trading status for the user."""
        account = TradingService._get_or_create_account(user)
        return account