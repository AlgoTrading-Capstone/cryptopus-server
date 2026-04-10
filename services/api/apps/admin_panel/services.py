from django.core.cache import cache
from apps.authentication.models import User
from apps.agent.models import Agent
from django.db.models import QuerySet
from apps.trading.models import TradingAccount
from apps.portfolio.models import Trade
from django.utils import timezone

class AdminService:

    @staticmethod
    def upload_agent(admin_user: User, name: str, version: str,
                     s3_model_path: str, s3_metadata_path: str,
                     normalization_profile: str, strategy_set_hash: str) -> Agent:
        """Upload a new trading agent."""
        existing = Agent.objects.filter(name=name, version=version).first()
        if existing:
            raise ValueError(f"Agent {name} v{version} already exists")

        agent = Agent.objects.create(
            name=name,
            version=version,
            s3_model_path=s3_model_path,
            s3_metadata_path=s3_metadata_path,
            normalization_profile=normalization_profile,
            strategy_set_hash=strategy_set_hash,
            status=Agent.Status.INACTIVE,
            uploaded_by=admin_user,
        )
        return agent

    @staticmethod
    def get_all_agents() -> QuerySet:
        """Return all uploaded agents."""
        return Agent.objects.all().order_by("-created_at")

    @staticmethod
    def get_agent(agent_id: str) -> Agent:
        """Return a specific agent by ID."""
        try:
            return Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist:
            raise ValueError("Agent not found")

    @staticmethod
    def activate_agent(agent_id: str) -> Agent:
        """Activate a trading agent — deactivates all others first."""
        try:
            agent = Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist:
            raise ValueError("Agent not found")

        if agent.status == Agent.Status.ACTIVE:
            raise ValueError("Agent is already active")

        # Deactivate all other agents
        Agent.objects.exclude(id=agent_id).update(status=Agent.Status.INACTIVE)

        # Activate this agent
        agent.status = Agent.Status.ACTIVE
        agent.activated_at = timezone.now()
        agent.save(update_fields=["status", "activated_at"])

        # Update Redis — rl-inference pod reads this on startup
        cache.set(
            "agent:active",
            {
                "agent_id": str(agent.id),
                "version": agent.version,
                "s3_model_path": agent.s3_model_path,
                "s3_metadata_path": agent.s3_metadata_path,
                "activated_at": str(agent.activated_at),
            },
            timeout=None,
        )

        return agent

    @staticmethod
    def deactivate_agent(agent_id: str) -> Agent:
        """Deactivate a trading agent."""
        try:
            agent = Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist:
            raise ValueError("Agent not found")

        if agent.status == Agent.Status.INACTIVE:
            raise ValueError("Agent is already inactive")

        agent.status = Agent.Status.INACTIVE
        agent.save(update_fields=["status"])

        # Remove from Redis
        cache.delete("agent:active")

        return agent

    @staticmethod
    def hot_swap(from_agent_id: str, to_agent_id: str) -> dict:
        """Switch active agent without platform restart."""
        try:
            from_agent = Agent.objects.get(id=from_agent_id)
            to_agent = Agent.objects.get(id=to_agent_id)
        except Agent.DoesNotExist:
            raise ValueError("One or both agents not found")

        if from_agent.status != Agent.Status.ACTIVE:
            raise ValueError("from_agent is not currently active")

        if to_agent.status == Agent.Status.ACTIVE:
            raise ValueError("to_agent is already active")

        # Deactivate old, activate new
        from_agent.status = Agent.Status.INACTIVE
        from_agent.save(update_fields=["status"])

        to_agent.status = Agent.Status.ACTIVE
        to_agent.activated_at = timezone.now()
        to_agent.save(update_fields=["status", "activated_at"])

        # Update Redis
        cache.set(
            "agent:active",
            {
                "agent_id": str(to_agent.id),
                "version": to_agent.version,
                "s3_model_path": to_agent.s3_model_path,
                "s3_metadata_path": to_agent.s3_metadata_path,
                "activated_at": str(to_agent.activated_at),
            },
            timeout=None,
        )

        return {
            "swapped": True,
            "previous_agent_id": str(from_agent.id),
            "active_agent_id": str(to_agent.id),
            "swapped_at": str(to_agent.activated_at),
        }

    @staticmethod
    def get_system_stats() -> dict:
        """Return aggregated platform statistics."""


        total_users = User.objects.filter(deleted_at__isnull=True).count()
        active_trading = TradingAccount.objects.filter(
            trading_state="RUNNING"
        ).count()

        today = timezone.now().date()
        trades_today = Trade.objects.filter(
            executed_at__date=today
        ).count()

        try:
            active_agent = Agent.objects.get(status=Agent.Status.ACTIVE)
            active_agent_id = str(active_agent.id)
        except Agent.DoesNotExist:
            active_agent_id = None

        return {
            "total_users": total_users,
            "active_trading_users": active_trading,
            "total_trades_today": trades_today,
            "active_agent_id": active_agent_id,
        }

    @staticmethod
    def get_system_health() -> dict:
        """Return health status of core platform services."""
        redis_status = "UP"
        try:
            cache.get("health_check")
        except Exception:
            redis_status = "DOWN"

        return {
            "api": "UP",
            "database": "UP",
            "redis": redis_status,
            "engine": "UNKNOWN",
            "exchange_connectivity": "UNKNOWN",
            "checked_at": str(timezone.now()),
        }

    @staticmethod
    def get_all_users() -> QuerySet:
        """Return all platform users."""
        return User.objects.filter(deleted_at__isnull=True).order_by("-created_at")

    @staticmethod
    def get_user(user_id: str) -> User:
        """Return a specific user by ID."""
        try:
            return User.objects.get(id=user_id, deleted_at__isnull=True)
        except User.DoesNotExist:
            raise ValueError("User not found")

    @staticmethod
    def update_user_status(user_id: str, account_status: str) -> User:
        """Update user account status."""
        valid_statuses = ["ACTIVE", "SUSPENDED", "PENDING_VERIFICATION"]
        if account_status not in valid_statuses:
            raise ValueError(f"Invalid status. Use: {', '.join(valid_statuses)}")

        try:
            user = User.objects.get(id=user_id, deleted_at__isnull=True)
        except User.DoesNotExist:
            raise ValueError("User not found")

        user.account_status = account_status
        user.save(update_fields=["account_status"])
        return user