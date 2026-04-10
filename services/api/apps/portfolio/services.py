from django.core.cache import cache
from apps.authentication.models import User
from apps.portfolio.models import Trade
from django.db.models import Sum, Max, Min
from datetime import datetime, timedelta, timezone

class PortfolioService:

    @staticmethod
    def get_summary(user: User) -> dict:
        """Return high-level portfolio summary. Reads from Redis cache first."""
        cached = cache.get(f"portfolio:summary:{user.id}")
        if cached:
            return cached

        # Fallback if cache is empty — return zeros
        return {
            "total_equity": 0.00,
            "available_balance": 0.00,
            "allocated_balance": 0.00,
            "unrealized_pnl": 0.00,
            "realized_pnl": 0.00,
            "daily_return_pct": 0.00,
            "open_positions": 0,
            "last_updated": None,
        }

    @staticmethod
    def get_trades(user: User, page: int = 1, page_size: int = 20,
                   symbol: str = None, from_date: str = None, to_date: str = None) -> dict:
        """Return paginated trade history with optional filters."""
        queryset = Trade.objects.filter(user=user)

        if symbol:
            queryset = queryset.filter(symbol=symbol)
        if from_date:
            queryset = queryset.filter(executed_at__gte=from_date)
        if to_date:
            queryset = queryset.filter(executed_at__lte=to_date)

        total_items = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        trades = queryset[start:end]

        return {
            "items": trades,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
        }

    @staticmethod
    def get_performance(user: User, range: str = "30d") -> dict:
        """Return aggregated performance metrics for the selected time range."""
        range_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365,
        }

        if range not in range_map:
            raise ValueError("Invalid range. Use: 7d, 30d, 90d, 1y")

        days = range_map[range]
        from_date = datetime.now(timezone.utc) - timedelta(days=days)

        trades = Trade.objects.filter(user=user, executed_at__gte=from_date)

        total_trades = trades.count()
        if total_trades == 0:
            return {
                "range": range,
                "total_return_pct": 0.00,
                "sharpe_ratio": 0.00,
                "max_drawdown_pct": 0.00,
                "win_rate_pct": 0.00,
                "total_trades": 0,
                "best_trade_pnl": 0.00,
                "worst_trade_pnl": 0.00,
            }

        aggregates = trades.aggregate(
            total_pnl=Sum("realized_pnl"),
            best_trade=Max("realized_pnl"),
            worst_trade=Min("realized_pnl"),
        )

        winning_trades = trades.filter(realized_pnl__gt=0).count()
        win_rate = (winning_trades / total_trades) * 100

        return {
            "range": range,
            "total_return_pct": float(aggregates["total_pnl"] or 0),
            "sharpe_ratio": 0.00,
            "max_drawdown_pct": 0.00,
            "win_rate_pct": round(win_rate, 2),
            "total_trades": total_trades,
            "best_trade_pnl": float(aggregates["best_trade"] or 0),
            "worst_trade_pnl": float(aggregates["worst_trade"] or 0),
        }

    @staticmethod
    def get_equity_history(user: User, range: str = "7d", interval: str = "1h") -> list:
        """Return time-series equity data from Redis cache."""
        cached = cache.get(f"portfolio:equity_history:{user.id}:{range}:{interval}")
        if cached:
            return cached
        return []

    @staticmethod
    def get_allocations(user: User) -> list:
        """Return asset allocation breakdown."""
        cached = cache.get(f"portfolio:summary:{user.id}")
        if not cached:
            return []

        return [
            {
                "asset": "BTC",
                "allocation_pct": 100.0,
                "market_value": cached.get("allocated_balance", 0.00),
            }
        ]