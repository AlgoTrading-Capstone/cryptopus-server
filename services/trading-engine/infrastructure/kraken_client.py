import logging
import ccxt
from config import TRADING_PAIR

logger = logging.getLogger(__name__)


class KrakenClient:
    """
    CCXT Kraken wrapper for the trading engine.
    Handles both public (market data) and private (orders) endpoints.
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        self._exchange = ccxt.kraken({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot",
            },
        })

    def fetch_ohlcv(self, timeframe: str = "15m", limit: int = 200) -> list:
        """
        Fetch OHLCV candles for BTC/USD.
        Returns list of [timestamp, open, high, low, close, volume].
        """
        try:
            ohlcv = self._exchange.fetch_ohlcv(
                symbol=TRADING_PAIR,
                timeframe=timeframe,
                limit=limit,
            )
            return ohlcv
        except ccxt.BaseError as e:
            logger.error(f"Kraken fetch_ohlcv failed: {e}")
            return []

    def fetch_ticker(self) -> dict | None:
        """Fetch latest ticker price for BTC/USD."""
        try:
            ticker = self._exchange.fetch_ticker(TRADING_PAIR)
            return {
                "symbol": ticker["symbol"],
                "last": ticker["last"],
                "bid": ticker["bid"],
                "ask": ticker["ask"],
                "volume": ticker["baseVolume"],
                "timestamp": ticker["timestamp"],
            }
        except ccxt.BaseError as e:
            logger.error(f"Kraken fetch_ticker failed: {e}")
            return None

    def fetch_balance(self) -> dict | None:
        """Fetch account balance. Requires API key."""
        try:
            balance = self._exchange.fetch_balance()
            return {
                "usd": balance["USD"]["free"] if "USD" in balance else 0.0,
                "btc": balance["XBT"]["free"] if "XBT" in balance else 0.0,
            }
        except ccxt.BaseError as e:
            logger.error(f"Kraken fetch_balance failed: {e}")
            return None

    def create_market_order(self, side: str, amount_btc: float) -> dict | None:
        """
        Place a market order on Kraken.

        Args:
            side: 'buy' or 'sell'
            amount_btc: amount of BTC to buy or sell

        Returns:
            Order dict with id, side, amount, price, status
        """
        try:
            order = self._exchange.create_order(
                symbol=TRADING_PAIR,
                type="market",
                side=side,
                amount=amount_btc,
            )
            logger.info(f"Kraken order placed: {side} {amount_btc} BTC — order_id={order['id']}")
            return {
                "kraken_order_id": order["id"],
                "side": order["side"],
                "amount": order["amount"],
                "price": order.get("average") or order.get("price"),
                "status": order["status"],
                "timestamp": order["timestamp"],
            }
        except ccxt.InsufficientFunds as e:
            logger.error(f"Kraken insufficient funds: {e}")
            return None
        except ccxt.BaseError as e:
            logger.error(f"Kraken create_market_order failed: {e}")
            return None

    def set_stop_loss(self, side: str, amount_btc: float, stop_price: float) -> dict | None:
        """
        Place a stop-loss order on Kraken.

        Args:
            side: 'sell' for LONG stop, 'buy' for SHORT stop
            amount_btc: position size
            stop_price: trigger price
        """
        try:
            order = self._exchange.create_order(
                symbol=TRADING_PAIR,
                type="stop-loss",
                side=side,
                amount=amount_btc,
                price=stop_price,
            )
            logger.info(f"Kraken stop-loss set: {side} {amount_btc} BTC @ {stop_price}")
            return {
                "kraken_order_id": order["id"],
                "side": order["side"],
                "amount": order["amount"],
                "stop_price": stop_price,
                "status": order["status"],
            }
        except ccxt.BaseError as e:
            logger.error(f"Kraken set_stop_loss failed: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        try:
            self._exchange.cancel_order(order_id, TRADING_PAIR)
            logger.info(f"Kraken order cancelled: {order_id}")
            return True
        except ccxt.BaseError as e:
            logger.error(f"Kraken cancel_order failed: {e}")
            return False

    def validate_credentials(self) -> bool:
        """Validate API key by fetching balance."""
        try:
            self._exchange.fetch_balance()
            return True
        except ccxt.AuthenticationError:
            return False
        except ccxt.BaseError as e:
            logger.error(f"Kraken validate_credentials failed: {e}")
            return False