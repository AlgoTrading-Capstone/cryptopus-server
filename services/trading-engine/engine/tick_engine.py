"""
Production tick engine — multi-user, Redis-driven.

Key differences from POC:
- Iterates over all active users per tick
- Fetches RL action from inference service via Redis
- Executes orders via OrderExecutor
- Market data fetched from Kraken (not Binance)
"""

import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import pandas as pd

from config import GLOBAL_TICK, MAX_STRATEGY_RUNTIME
from infrastructure.redis_client import RedisClient
from infrastructure.kraken_client import KrakenClient
from infrastructure.db_client import DBClient
from engine.position_manager import PositionManager
from engine.order_executor import OrderExecutor
from shared.constants import DEFAULT_STRATEGY_LIST, DEFAULT_INDICATORS, DATA_TIMEFRAME,SignalType
from shared.state_builder import build_state_vector

logger = logging.getLogger(__name__)


class TickEngine:
    """
    APScheduler-based tick engine.
    On every tick: runs strategies, builds state, gets RL action, executes orders.
    """

    def __init__(self):
        self._redis = RedisClient()
        self._db = DBClient()
        self._scheduler = None
        self._strategies = {} # loaded dynamically on first tick

    def _load_strategies(self, strategy_list: list) -> dict:
        """
        Dynamically load strategy instances from shared.strategies
        based on the strategy list from metadata.json.
        """
        import importlib
        strategies = {}
        for strategy_name in strategy_list:
            try:
                module = importlib.import_module(f"shared.strategies.{strategy_name.lower()}")
                cls = getattr(module, strategy_name)
                strategies[strategy_name] = cls()
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to load strategy {strategy_name}: {e}")
        return strategies

    def start(self):
        """Start the tick scheduler."""
        from utils.timeframes import timeframe_to_cron
        cron_args = timeframe_to_cron(GLOBAL_TICK)
        trigger = CronTrigger(**cron_args)

        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(self.run_tick_cycle, trigger)
        self._scheduler.start()

        # Update engine status in Redis
        self._redis.set_engine_status({
            "runtime_status": "RUNNING",
            "last_tick_processed": None,
            "decisions_per_minute": 0,
            "engine_latency_ms": 0,
        })

        logger.info(f"Tick engine started with cron: {cron_args}")

    def stop(self):
        """Stop the tick scheduler."""
        if self._scheduler:
            self._scheduler.shutdown()
            self._redis.set_engine_status({
                "runtime_status": "STOPPED",
                "last_tick_processed": None,
                "decisions_per_minute": 0,
                "engine_latency_ms": 0,
            })
        logger.info("Tick engine stopped")

    def run_tick_cycle(self):
        """
        Execute one full tick cycle:
        1. Get active users from Redis
        2. Fetch latest OHLCV from Kraken
        3. Run strategies
        4. Build state vector per user
        5. Get RL action from inference service
        6. Execute orders per user
        """
        now = datetime.now(timezone.utc)
        logger.info(f"Tick cycle starting at {now.strftime('%H:%M:%S UTC')}")

        try:
            # Step 1 — Get active users
            active_users = self._redis.get_active_users()
            if not active_users:
                logger.info("No active users — skipping tick")
                return

            logger.info(f"{len(active_users)} active users")

            # Step 2 — Fetch OHLCV (shared across all users)
            public_kraken = KrakenClient()
            ohlcv = public_kraken.fetch_ohlcv(timeframe=DATA_TIMEFRAME, limit=200)
            if not ohlcv:
                logger.error("Failed to fetch OHLCV — skipping tick")
                return

            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            df = df.set_index("timestamp")

            current_price = float(df["close"].iloc[-1])
            logger.info(f"BTC/USD close: {current_price}")

            # Step 3 — Run strategies (shared across all users)
            # Load strategies from active agent metadata
            agent_meta = self._redis.get_active_agent()
            strategy_list = agent_meta.get("strategy_list",DEFAULT_STRATEGY_LIST) if agent_meta else DEFAULT_STRATEGY_LIST
            if not self._strategies:
                self._strategies = self._load_strategies(strategy_list)
            strategy_signals = self._run_strategies(df, now)
            logger.info(f"Strategy signals: { {k: v.value for k, v in strategy_signals.items()} }")

            # Step 4-6 — Per user: build state, get action, execute
            with ThreadPoolExecutor(max_workers=min(len(active_users), 10)) as executor:
                futures = {
                    executor.submit(
                        self._process_user,
                        user_id, df, strategy_signals, current_price, now
                    ): user_id
                    for user_id in active_users
                }

                for future in as_completed(futures):
                    user_id = futures[future]
                    try:
                        future.result(timeout=MAX_STRATEGY_RUNTIME)
                    except Exception as e:
                        logger.error(f"Error processing user {user_id}: {e}")

            # Update engine status
            self._redis.set_engine_status({
                "runtime_status": "RUNNING",
                "last_tick_processed": str(now),
                "decisions_per_minute": len(active_users),
                "engine_latency_ms": 0,
            })

            logger.info("Tick cycle completed")

        except Exception as e:
            logger.error(f"Tick cycle failed: {e}")

    def _run_strategies(self, df: pd.DataFrame, now: datetime) -> dict:
        """
        Run all strategies and return signal dict.
        Missing strategies default to HOLD.
        """
        signals = {}
        for name, strategy in self._strategies.items():
            try:
                rec = strategy.run(df.reset_index(), now)
                signals[name] = rec.signal
            except Exception as e:
                logger.error(f"Strategy {name} failed: {e}")
                signals[name] = SignalType.HOLD
        return signals

    def _process_user(
        self,
        user_id: str,
        df: pd.DataFrame,
        strategy_signals: dict,
        current_price: float,
        now: datetime,
    ) -> None:
        """
        Full pipeline for a single user:
        1. Load position state
        2. Build state vector
        3. Get RL action from Redis (published by rl-inference)
        4. Execute order
        """
        try:
            # Load agent metadata from Redis
            agent_meta = self._redis.get_active_agent()
            if not agent_meta:
                logger.warning(f"No active agent — skipping user {user_id}")
                return

            strategy_list = agent_meta.get("strategy_list", DEFAULT_STRATEGY_LIST)
            indicators = agent_meta.get("indicators", DEFAULT_INDICATORS)
            enable_turbulence = agent_meta.get("enable_turbulence", True)
            enable_vix = agent_meta.get("enable_vix", False)

            # Load trading state
            trading_state = self._redis.get_trading_state(user_id)
            if not trading_state:
                return

            balance = float(trading_state.get("allocated_usd", 0))
            if balance <= 0:
                return

            # Load position state
            position = PositionManager(self._redis, self._db).get_position(user_id)
            holdings_btc = position.holdings_btc
            equity = balance + holdings_btc * current_price

            # Build state vector
            state = build_state_vector(
                balance=balance,
                df=df.reset_index(),
                strategy_signals=strategy_signals,
                position_state=position,
                indicators=indicators,
                strategy_list=strategy_list,
                enable_turbulence=enable_turbulence,
                enable_vix=enable_vix,
            )

            # Get RL action from inference service via Redis
            action_data = self._redis.get(f"inference:action:{user_id}")
            if not action_data:
                logger.warning(f"No RL action available for user {user_id} — skipping")
                return

            action = action_data.get("action", [0.0, 0.0])

            # Get user Kraken credentials and execute
            credentials = self._db.get_user_exchange_credentials(user_id)
            if not credentials:
                logger.warning(f"No exchange credentials for user {user_id}")
                return

            kraken = KrakenClient(
                api_key=credentials["api_key"],
                api_secret=credentials["api_secret"],
            )

            position_manager = PositionManager(self._redis, self._db)
            executor = OrderExecutor(kraken, position_manager, self._db, self._redis)
            executor.execute(
                user_id=user_id,
                action=action,
                current_price=current_price,
                equity=equity,
                balance=balance,
            )

            # Publish state to Redis for rl-inference to read next tick
            self._redis.set(f"inference:state:{user_id}", {
                "state": state.tolist(),
                "timestamp": str(now),
            })

        except Exception as e:
            logger.error(f"Error in _process_user for {user_id}: {e}")