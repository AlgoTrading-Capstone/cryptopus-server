import numpy as np
import talib
from shared.constants import (
    LEVERAGE_LIMIT,
    SIGNAL_ONE_HOT,
    SignalType,
)
from shared.normalization import normalize_state


class PositionState:
    """Runtime position state that must be maintained per user across ticks."""

    def __init__(self):
        self.side = 0                  # -1 = short, 0 = flat, 1 = long
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.holdings_btc = 0.0
        self.bars_in_position = 0
        self.bars_since_stop = -1      # -1 sentinel = never stopped this session
        self.last_stopped_side = 0

    def reset(self):
        """Reset position state to flat."""
        self.side = 0
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.holdings_btc = 0.0
        self.bars_in_position = 0

    def to_dict(self) -> dict:
        return {
            "side": self.side,
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "holdings_btc": self.holdings_btc,
            "bars_in_position": self.bars_in_position,
            "bars_since_stop": self.bars_since_stop,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PositionState":
        ps = cls()
        ps.side = data.get("side", 0)
        ps.entry_price = data.get("entry_price", 0.0)
        ps.stop_price = data.get("stop_price", 0.0)
        ps.holdings_btc = data.get("holdings_btc", 0.0)
        ps.bars_in_position = data.get("bars_in_position", 0)
        ps.bars_since_stop = data.get("bars_since_stop", -1)
        return ps


def compute_indicators(df, indicators: list) -> np.ndarray:
    """
    Compute technical indicators from OHLCV dataframe.
    Order must match metadata.json["data"]["indicators"].

    Args:
        df: pandas DataFrame with columns [open, high, low, close, volume]
        indicators: ordered list of indicator names from metadata.json

    Returns:
        np.ndarray of shape (len(indicators),) with latest bar values
    """
    close = df["close"].values.astype(np.float64)
    high = df["high"].values.astype(np.float64)
    low = df["low"].values.astype(np.float64)

    results = []

    for indicator in indicators:
        if indicator == "macd":
            macd, _, _ = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            results.append(float(macd[-1]) if not np.isnan(macd[-1]) else 0.0)

        elif indicator == "boll_ub":
            upper, _, _ = talib.BBANDS(close, timeperiod=20)
            results.append(float(upper[-1]) if not np.isnan(upper[-1]) else float(close[-1]))

        elif indicator == "boll_lb":
            _, _, lower = talib.BBANDS(close, timeperiod=20)
            results.append(float(lower[-1]) if not np.isnan(lower[-1]) else float(close[-1]))

        elif indicator == "rsi_30":
            rsi = talib.RSI(close, timeperiod=30)
            results.append(float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0)

        elif indicator == "dx_30":
            dx = talib.DX(high, low, close, timeperiod=30)
            results.append(float(dx[-1]) if not np.isnan(dx[-1]) else 0.0)

        elif indicator == "close_30_sma":
            sma = talib.SMA(close, timeperiod=30)
            results.append(float(sma[-1]) if not np.isnan(sma[-1]) else float(close[-1]))

        elif indicator == "close_60_sma":
            sma = talib.SMA(close, timeperiod=60)
            results.append(float(sma[-1]) if not np.isnan(sma[-1]) else float(close[-1]))

        else:
            raise ValueError(f"Unknown indicator: {indicator}")

    return np.array(results, dtype=np.float32)


def compute_signal_vector(strategy_signals: dict, strategy_list: list) -> np.ndarray:
    """
    Convert strategy signals to one-hot encoded vector.
    Order must match metadata.json["strategies"]["strategy_list"].

    Args:
        strategy_signals: dict mapping strategy_name -> SignalType
        strategy_list: ordered list of strategy names from metadata.json

    Returns:
        np.ndarray of shape (4 * len(strategy_list),)
    """
    signal_blocks = []

    for strategy_name in strategy_list:
        signal = strategy_signals.get(strategy_name, SignalType.HOLD)
        one_hot = SIGNAL_ONE_HOT[signal]
        signal_blocks.extend(one_hot)

    return np.array(signal_blocks, dtype=np.float32)


def build_state_vector(
    balance: float,
    df,
    strategy_signals: dict,
    position_state: PositionState,
    indicators: list,
    strategy_list: list,
    turbulence: float = 0.0,
    enable_turbulence: bool = True,
    enable_vix: bool = False,
    vix: float = 0.0,
) -> np.ndarray:
    """
    Build the complete state vector for RL inference.
    This is the single source of truth for state construction.

    Args:
        balance: current USD balance
        df: OHLCV dataframe (must have enough history for indicators)
        strategy_signals: dict mapping strategy_name -> SignalType
        position_state: current position state for this user
        indicators: ordered indicator list from metadata.json
        strategy_list: ordered strategy list from metadata.json
        turbulence: current turbulence value
        enable_turbulence: from metadata.json
        enable_vix: from metadata.json
        vix: current VIX value (only used if enable_vix=True)

    Returns:
        np.ndarray of shape (state_dim,), dtype float32
    """
    latest = df.iloc[-1]
    close = float(latest["close"])

    price_vec = np.array([
        float(latest["open"]),
        float(latest["high"]),
        float(latest["low"]),
        float(latest["close"]),
        float(latest["volume"]),
    ], dtype=np.float32)

    tech_vec = compute_indicators(df, indicators)

    turb_list = []
    if enable_turbulence:
        turb_list.append(turbulence)
    if enable_vix:
        turb_list.append(vix)
    turbulence_vec = np.array(turb_list, dtype=np.float32)

    signal_vec = compute_signal_vector(strategy_signals, strategy_list)

    # Compute derived position context values
    if position_state.side != 0 and position_state.entry_price > 0 and close > 0:
        entry_price_rel = position_state.entry_price / close - 1.0
        unrealized_pnl_pct = position_state.side * (close / position_state.entry_price - 1.0)
    else:
        entry_price_rel = 0.0
        unrealized_pnl_pct = 0.0

    if position_state.stop_price > 0 and close > 0:
        stop_distance_pct = position_state.stop_price / close - 1.0
    else:
        stop_distance_pct = 0.0

    equity = balance + position_state.holdings_btc * close
    if equity > 0 and LEVERAGE_LIMIT > 0:
        exposure_norm = np.clip(
            position_state.holdings_btc * close / (LEVERAGE_LIMIT * equity),
            -1.0, 1.0
        )
    else:
        exposure_norm = 0.0

    return normalize_state(
        balance=balance,
        price_vec=price_vec,
        tech_vec=tech_vec,
        turbulence_vec=turbulence_vec,
        signal_vec=signal_vec,
        holdings=position_state.holdings_btc,
        position_side=position_state.side,
        exposure_norm=float(exposure_norm),
        entry_price_rel=entry_price_rel,
        unrealized_pnl_pct=unrealized_pnl_pct,
        stop_distance_pct=stop_distance_pct,
        bars_in_position=position_state.bars_in_position,
        bars_since_stop=position_state.bars_since_stop,
        enable_turbulence=enable_turbulence,
        enable_vix=enable_vix,
    )