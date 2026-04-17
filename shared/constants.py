from enum import Enum


# Model and environment constants
# These must match training config exactly - changing them breaks the model
INITIAL_BALANCE = 100_000.0
MAX_POSITION_BTC = 4.0
LEVERAGE_LIMIT = 2.0
MIN_STOP_LOSS_PCT = 0.01
MAX_STOP_LOSS_PCT = 0.05
EXPOSURE_DEADZONE = 0.10
STOP_UPDATE_DEADZONE_PCT = 0.002
TRANSACTION_FEE = 0.0005
DATA_TIMEFRAME = "15m"
INDICATOR_WARMUP_CANDLES = 60


# Indicator list - order is load-bearing, normalization is index-based.
# At runtime always use metadata.json["data"]["indicators"] - this is the fallback default.
DEFAULT_INDICATORS = [
    "macd",
    "boll_ub",
    "boll_lb",
    "rsi_30",
    "dx_30",
    "close_30_sma",
    "close_60_sma",
]


# Strategy list - order is load-bearing, each strategy occupies 4 fixed one-hot columns.
# At runtime always load from metadata.json["strategies"]["strategy_list"].
# Never hardcode this in inference or trading-engine.
DEFAULT_STRATEGY_LIST = [
    "SupertrendStrategy",
    "PgQsdForNiftyFutureStrategy",
    "MonthlyReturnsInPinescriptStrategiesStrategy",
    "TrendPullbackMomentumSideAwareStrategy",
]


# Signal one-hot encoding.
# Order is [FLAT, LONG, SHORT, HOLD] - do not use alphabetical or any other order.
# This encoding is fixed regardless of number of strategies.
class SignalType(Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"


SIGNAL_ONE_HOT = {
    SignalType.FLAT:  [1, 0, 0, 0],
    SignalType.LONG:  [0, 1, 0, 0],
    SignalType.SHORT: [0, 0, 1, 0],
    SignalType.HOLD:  [0, 0, 0, 1],
}


# State vector dimensions.
# At runtime always use metadata.json["env_spec"]["state_dim"].
# Formula: 1 (balance) + 5 (price) + 7 (tech) + turb_dim + 4*N_strategies + 1 (holdings) + 7 (position context)
# DEFAULT_STATE_DIM matches the currently deployed model.
DEFAULT_STATE_DIM = 38
ACTION_DIM = 2
ACTION_BOUNDS = (-1.0, 1.0)


# Exchange config
EXCHANGE_NAME = "kraken"
TRADING_PAIR = "XBT/USD"
TRADING_PAIR_DISPLAY = "BTC/USD"