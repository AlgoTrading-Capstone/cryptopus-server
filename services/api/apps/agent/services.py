from django.core.cache import cache
from apps.agent.models import Agent


class AgentService:

    @staticmethod
    def get_active_agent() -> Agent:
        """Return the currently active trading agent."""
        try:
            agent = Agent.objects.get(status=Agent.Status.ACTIVE)
        except Agent.DoesNotExist:
            raise ValueError("No active agent found")
        return agent

    @staticmethod
    def get_active_agent_metrics(range: str = "30d") -> dict:
        """Return performance metrics for the active agent."""
        valid_ranges = ["7d", "30d", "90d", "1y"]
        if range not in valid_ranges:
            raise ValueError(f"Invalid range. Use: {', '.join(valid_ranges)}")

        # TODO: calculate real metrics from trades table when trading engine is live
        return {
            "total_return_pct": 0.00,
            "sharpe_ratio": 0.00,
            "max_drawdown_pct": 0.00,
            "win_rate_pct": 0.00,
            "total_trades": 0,
            "profit_factor": 0.00,
        }

    @staticmethod
    def get_active_agent_plots(range: str = "30d") -> dict:
        """Return chart data for active agent performance visualization."""
        valid_ranges = ["7d", "30d", "90d", "1y"]
        if range not in valid_ranges:
            raise ValueError(f"Invalid range. Use: {', '.join(valid_ranges)}")

        # TODO: build real equity/drawdown curves from trades when trading engine is live
        return {
            "equity_curve": [],
            "drawdown_curve": [],
        }

    @staticmethod
    def get_active_agent_explanation() -> dict:
        """Return explanation and strategy details of the active agent."""
        return {
            "strategy_type": "Reinforcement Learning",
            "features": [
                "Momentum indicators",
                "Volatility signals",
                "Volume trends",
            ],
            "risk_management": "Dynamic position sizing",
            "trading_frequency": "Medium",
            "markets": ["BTC/USD"],
        }

    @staticmethod
    def get_agent_runtime_status() -> dict:
        """Return runtime status of the trading agent from Redis."""
        cached = cache.get("agent:runtime:status")
        if not cached:
            return {
                "agent_id": None,
                "runtime_status": "STOPPED",
                "last_tick_processed": None,
                "decisions_per_minute": 0,
                "engine_latency_ms": 0,
            }
        return cached