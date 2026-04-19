import logging
from datetime import datetime, timezone
from decimal import Decimal
from shared.state_builder import PositionState
from shared.constants import (
    LEVERAGE_LIMIT,
    MIN_STOP_LOSS_PCT,
    MAX_STOP_LOSS_PCT,
    STOP_UPDATE_DEADZONE_PCT,
    MAX_POSITION_BTC,
)
from infrastructure.redis_client import RedisClient
from infrastructure.db_client import DBClient

logger = logging.getLogger(__name__)


class PositionManager:
    """
    Manages open positions per user.
    Reads/writes position state from Redis.
    Writes closed positions to PostgreSQL.
    """

    def __init__(self, redis_client: RedisClient, db_client: DBClient):
        self._redis = redis_client
        self._db = db_client

    def get_position(self, user_id: str) -> PositionState:
        """Load position state from Redis. Returns flat position if none exists."""
        data = self._redis.get_position_state(user_id)
        if data is None:
            return PositionState()
        return PositionState.from_dict(data)

    def save_position(self, user_id: str, position: PositionState) -> None:
        """Save position state to Redis."""
        self._redis.set_position_state(user_id, position.to_dict())

    def delete_position(self, user_id: str) -> None:
        """Remove position state from Redis when position is closed."""
        self._redis.delete_position_state(user_id)

    def open_position(
        self,
        user_id: str,
        side: int,
        entry_price: float,
        size_btc: float,
        stop_price: float,
        opened_at: datetime,
    ) -> PositionState:
        """Open a new position and save to Redis."""
        position = PositionState()
        position.side = side
        position.entry_price = entry_price
        position.holdings_btc = size_btc
        position.stop_price = stop_price
        position.bars_in_position = 0
        position.bars_since_stop = -1
        position.opened_at = str(opened_at)

        self.save_position(user_id, position)
        logger.info(f"Position opened for user {user_id}: side={side} size={size_btc} BTC @ {entry_price}")
        return position

    def close_position(
        self,
        user_id: str,
        position: PositionState,
        exit_price: float,
        closed_at: datetime,
    ) -> None:
        """Close a position — write to DB and clear from Redis."""
        opened_at = datetime.fromisoformat(position.opened_at) if hasattr(position, 'opened_at') else closed_at
        duration_seconds = int((closed_at - opened_at).total_seconds())

        side_str = "LONG" if position.side == 1 else "SHORT"

        # Calculate realized PnL
        if position.side == 1:
            pnl = (exit_price - position.entry_price) / position.entry_price * position.holdings_btc * position.entry_price
        else:
            pnl = (position.entry_price - exit_price) / position.entry_price * position.holdings_btc * position.entry_price

        self._db.write_position(
            user_id=user_id,
            symbol="BTC/USD",
            side=side_str,
            size_btc=Decimal(str(position.holdings_btc)),
            entry_price=Decimal(str(position.entry_price)),
            exit_price=Decimal(str(exit_price)),
            realized_pnl=Decimal(str(round(pnl, 2))),
            opened_at=opened_at,
            closed_at=closed_at,
            duration_seconds=duration_seconds,
        )

        self.delete_position(user_id)
        logger.info(f"Position closed for user {user_id}: exit={exit_price} pnl={pnl:.2f}")

    def compute_stop_price(self, side: int, entry_price: float, a_sl: float) -> float:
        """
        Compute stop price from RL action a_sl.
        a_sl is in [-1, 1] — maps to stop distance between MIN and MAX stop loss pct.
        """
        a_sl01 = 0.5 * (a_sl + 1)
        stop_pct = MIN_STOP_LOSS_PCT + a_sl01 * (MAX_STOP_LOSS_PCT - MIN_STOP_LOSS_PCT)

        if side == 1:
            return entry_price * (1 - stop_pct)
        else:
            return entry_price * (1 + stop_pct)

    def should_update_stop(self, current_stop: float, new_stop: float, current_price: float) -> bool:
        """Check if stop price change is significant enough to update."""
        change = abs(new_stop - current_stop)
        deadzone = STOP_UPDATE_DEADZONE_PCT * current_price
        return change > deadzone

    def compute_target_size(self, a_pos: float, equity: float, current_price: float) -> float:
        """
        Compute target BTC position size from RL action a_pos.
        a_pos in [-1, 1] maps to [-max_short, max_long] in BTC.
        """
        max_notional = LEVERAGE_LIMIT * equity
        target_notional = a_pos * max_notional
        target_btc = target_notional / current_price if current_price > 0 else 0.0
        return max(-MAX_POSITION_BTC, min(MAX_POSITION_BTC, target_btc))

    def is_stopped_out(self, position: PositionState, candle_open: float) -> bool:
        """
        Check if position was stopped out on candle open.
        LONG stops at min(open, stop_price), SHORT at max(open, stop_price).
        """
        if position.side == 0 or position.stop_price <= 0:
            return False

        if position.side == 1:
            return candle_open <= position.stop_price
        else:
            return candle_open >= position.stop_price