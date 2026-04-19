import logging
from datetime import datetime, timezone
from decimal import Decimal
from shared.constants import EXPOSURE_DEADZONE
from infrastructure.kraken_client import KrakenClient
from infrastructure.db_client import DBClient
from infrastructure.redis_client import RedisClient
from engine.position_manager import PositionManager
from shared.state_builder import PositionState

logger = logging.getLogger(__name__)


class OrderExecutor:
    """
    Converts RL model actions into Kraken orders.
    Handles position opening, closing, and stop-loss management.
    """

    def __init__(
        self,
        kraken_client: KrakenClient,
        position_manager: PositionManager,
        db_client: DBClient,
        redis_client: RedisClient,
    ):
        self._kraken = kraken_client
        self._position_manager = position_manager
        self._db = db_client
        self._redis = redis_client

    def execute(
        self,
        user_id: str,
        action: list,
        current_price: float,
        equity: float,
        balance: float,
    ) -> None:
        """
        Execute RL action for a user.

        Args:
            user_id: user to execute for
            action: [a_pos, a_sl] from RL model — both in [-1, 1]
            current_price: latest BTC close price
            equity: total equity (balance + unrealized PnL)
            balance: available USD balance
        """
        a_pos = float(action[0])
        a_sl = float(action[1])

        position = self._position_manager.get_position(user_id)
        now = datetime.now(timezone.utc)

        # Check if stopped out on this candle open
        if self._position_manager.is_stopped_out(position, current_price):
            logger.info(f"User {user_id} stopped out at {current_price}")
            self._close_position(user_id, position, current_price, now, stopped_out=True)
            position = PositionState()

        # Compute target exposure
        target_btc = self._position_manager.compute_target_size(a_pos, equity, current_price)
        current_btc = position.holdings_btc * position.side if position.side != 0 else 0.0
        exposure_change = abs(target_btc - current_btc) / (equity / current_price) if equity > 0 and current_price > 0 else 0.0

        # Skip if change is within deadzone
        if exposure_change < EXPOSURE_DEADZONE:
            logger.debug(f"User {user_id} exposure change {exposure_change:.3f} within deadzone — skipping")
            self._update_stop_if_needed(user_id, position, a_sl, current_price)
            return

        # Determine action
        target_side = 1 if target_btc > 0 else (-1 if target_btc < 0 else 0)

        if position.side != 0 and target_side != position.side:
            # Close existing position
            self._close_position(user_id, position, current_price, now)
            position = PositionState()

        if target_side != 0:
            # Open new position
            self._open_position(user_id, target_side, target_btc, a_sl, current_price, now)
        else:
            # Go flat
            if position.side != 0:
                self._close_position(user_id, position, current_price, now)

    def _open_position(
        self,
        user_id: str,
        side: int,
        size_btc: float,
        a_sl: float,
        current_price: float,
        now: datetime,
    ) -> None:
        """Place market order and open position."""
        order_side = "buy" if side == 1 else "sell"
        abs_size = abs(size_btc)

        order = self._kraken.create_market_order(order_side, abs_size)
        if order is None:
            logger.error(f"Failed to place order for user {user_id}")
            return

        fill_price = order.get("price") or current_price
        stop_price = self._position_manager.compute_stop_price(side, fill_price, a_sl)

        position = self._position_manager.open_position(
            user_id=user_id,
            side=side,
            entry_price=fill_price,
            size_btc=abs_size,
            stop_price=stop_price,
            opened_at=now,
        )

        # Write trade to DB
        self._db.write_trade(
            user_id=user_id,
            symbol="BTC/USD",
            side="BUY" if side == 1 else "SELL",
            quantity=Decimal(str(abs_size)),
            price=Decimal(str(fill_price)),
            fee=Decimal("0"),
            realized_pnl=Decimal("0"),
            executed_at=now,
            kraken_order_id=order.get("kraken_order_id"),
        )

        # Publish alert
        self._redis.publish_alert(user_id, {
            "event": "TRADE_EXECUTED",
            "data": {
                "side": order_side.upper(),
                "size_btc": abs_size,
                "price": fill_price,
                "stop_price": stop_price,
            }
        })

    def _close_position(
        self,
        user_id: str,
        position: PositionState,
        current_price: float,
        now: datetime,
        stopped_out: bool = False,
    ) -> None:
        """Place closing market order and archive position."""
        close_side = "sell" if position.side == 1 else "buy"

        order = self._kraken.create_market_order(close_side, position.holdings_btc)
        fill_price = order.get("price") if order else current_price

        self._position_manager.close_position(
            user_id=user_id,
            position=position,
            exit_price=fill_price,
            closed_at=now,
        )

        # Write closing trade to DB
        if order:
            self._db.write_trade(
                user_id=user_id,
                symbol="BTC/USD",
                side=close_side.upper(),
                quantity=Decimal(str(position.holdings_btc)),
                price=Decimal(str(fill_price)),
                fee=Decimal("0"),
                realized_pnl=Decimal("0"),
                executed_at=now,
                kraken_order_id=order.get("kraken_order_id"),
            )

        reason = "STOP_LOSS" if stopped_out else "SIGNAL"
        self._redis.publish_alert(user_id, {
            "event": "TRADE_EXECUTED",
            "data": {
                "side": close_side.upper(),
                "size_btc": position.holdings_btc,
                "price": fill_price,
                "reason": reason,
            }
        })

    def _update_stop_if_needed(
        self,
        user_id: str,
        position: PositionState,
        a_sl: float,
        current_price: float,
    ) -> None:
        """Update stop price if change exceeds deadzone."""
        if position.side == 0:
            return

        new_stop = self._position_manager.compute_stop_price(
            position.side, position.entry_price, a_sl
        )

        if self._position_manager.should_update_stop(
            position.stop_price, new_stop, current_price
        ):
            position.stop_price = new_stop
            self._position_manager.save_position(user_id, position)
            logger.debug(f"Stop updated for user {user_id}: {new_stop:.2f}")