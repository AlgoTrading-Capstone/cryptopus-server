import os


# Database
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5433"))
DB_NAME = os.environ.get("DB_NAME", "cryptopus")
DB_USER = os.environ.get("DB_USER", "cryptopus")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "cryptopus123")

# Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

# Tick engine
GLOBAL_TICK = os.environ.get("GLOBAL_TICK", "1m")
MAX_STRATEGY_RUNTIME = int(os.environ.get("MAX_STRATEGY_RUNTIME", "5"))

# Shared package constants (imported at runtime from metadata.json)
# These are defaults — always override from metadata.json in production
DATA_TIMEFRAME = os.environ.get("DATA_TIMEFRAME", "15m")
LOOKBACK_CANDLES = int(os.environ.get("LOOKBACK_CANDLES", "200"))

# Exchange
EXCHANGE_NAME = os.environ.get("EXCHANGE_NAME", "kraken")
TRADING_PAIR = os.environ.get("TRADING_PAIR", "XBT/USD")

# Environment
ENV = os.environ.get("ENV", "development")
DEBUG = ENV == "development"