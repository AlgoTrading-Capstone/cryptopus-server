import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
import psycopg2
import psycopg2.extras
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)


def get_connection():
    """Create a new PostgreSQL connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


class DBClient:
    """
    Raw SQL client for the trading engine.
    Bypasses Django ORM — writes directly to PostgreSQL.
    Used for trades, positions, and alerts.
    """

    def write_trade(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        realized_pnl: Decimal,
        executed_at: datetime,
        kraken_order_id: str = None,
    ) -> str | None:
        """
        Write a completed trade to the trades table.
        Returns the trade UUID on success.
        """
        trade_id = str(uuid.uuid4())
        sql = """
            INSERT INTO trades (
                id, user_id, symbol, side, quantity, price,
                fee, realized_pnl, executed_at, kraken_order_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (
                        trade_id, user_id, symbol, side,
                        quantity, price, fee, realized_pnl,
                        executed_at, kraken_order_id,
                    ))
                conn.commit()
            logger.info(f"Trade written: {trade_id} — {side} {quantity} {symbol} @ {price}")
            return trade_id
        except psycopg2.Error as e:
            logger.error(f"DB write_trade failed: {e}")
            return None

    def write_position(
        self,
        user_id: str,
        symbol: str,
        side: str,
        size_btc: Decimal,
        entry_price: Decimal,
        exit_price: Decimal,
        realized_pnl: Decimal,
        opened_at: datetime,
        closed_at: datetime,
        duration_seconds: int,
    ) -> str | None:
        """
        Write a closed position to the positions table.
        Returns the position UUID on success.
        """
        position_id = str(uuid.uuid4())
        sql = """
            INSERT INTO positions (
                id, user_id, symbol, side, size_btc, entry_price,
                exit_price, realized_pnl, opened_at, closed_at, duration_seconds
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (
                        position_id, user_id, symbol, side,
                        size_btc, entry_price, exit_price, realized_pnl,
                        opened_at, closed_at, duration_seconds,
                    ))
                conn.commit()
            logger.info(f"Position written: {position_id} — {side} {size_btc} BTC")
            return position_id
        except psycopg2.Error as e:
            logger.error(f"DB write_position failed: {e}")
            return None

    def write_alert(
        self,
        user_id: str,
        alert_type: str,
        title: str,
        message: str,
        severity: str = "INFO",
    ) -> str | None:
        """
        Write an alert to the alerts table.
        Returns the alert UUID on success.
        """
        alert_id = str(uuid.uuid4())
        sql = """
            INSERT INTO alerts (
                id, user_id, type, title, message, severity, read, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (
                        alert_id, user_id, alert_type, title,
                        message, severity, False,
                        datetime.now(timezone.utc),
                    ))
                conn.commit()
            logger.info(f"Alert written: {alert_id} — {alert_type} for user {user_id}")
            return alert_id
        except psycopg2.Error as e:
            logger.error(f"DB write_alert failed: {e}")
            return None

    def get_user_exchange_credentials(self, user_id: str) -> dict | None:
        """
        Fetch Kraken API credentials for a user.
        Returns dict with api_key and api_secret.
        """
        sql = """
            SELECT api_key, api_secret
            FROM exchange_connections
            WHERE user_id = %s
            AND exchange = 'KRAKEN'
            AND deleted_at IS NULL
            LIMIT 1
        """
        try:
            with get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute(sql, (user_id,))
                    row = cur.fetchone()
                    if row is None:
                        return None
                    return {
                        "api_key": row["api_key"],
                        "api_secret": row["api_secret"],
                    }
        except psycopg2.Error as e:
            logger.error(f"DB get_user_exchange_credentials failed: {e}")
            return None