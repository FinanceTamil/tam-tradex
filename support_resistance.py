from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _numeric_series(data: pd.DataFrame, column: str) -> pd.Series:
    if column not in data.columns:
        raise ValueError(f"Required column '{column}' was not found.")

    series = data[column]

    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]

    return pd.to_numeric(series.squeeze(), errors="coerce")


def _cluster_levels(
    levels: list[float],
    tolerance: float,
) -> list[float]:
    """
    Merge nearby price levels into representative clusters.
    """

    clean_levels = sorted(
        float(level)
        for level in levels
        if np.isfinite(level)
    )

    if not clean_levels:
        return []

    clusters: list[list[float]] = [[clean_levels[0]]]

    for level in clean_levels[1:]:
        current_cluster = clusters[-1]
        cluster_average = float(np.mean(current_cluster))

        if abs(level - cluster_average) <= tolerance:
            current_cluster.append(level)
        else:
            clusters.append([level])

    return [
        float(np.mean(cluster))
        for cluster in clusters
    ]


def calculate_support_resistance(
    data: pd.DataFrame,
    current_price: float | None = None,
    *,
    lookback: int = 120,
    pivot_window: int = 5,
    max_levels: int = 3,
) -> dict[str, Any]:
    """
    Detect nearby support and resistance levels from recent swing highs/lows.

    The method:
    1. Restricts analysis to a recent lookback window.
    2. Finds centred rolling swing highs and swing lows.
    3. Clusters nearby pivots using an ATR-derived tolerance.
    4. Selects the nearest levels below and above the current price.
    """

    if data is None or data.empty:
        raise ValueError("Market data is empty.")

    if pivot_window < 3 or pivot_window % 2 == 0:
        raise ValueError("pivot_window must be an odd integer of at least 3.")

    recent = data.tail(max(int(lookback), pivot_window + 2)).copy()

    high = _numeric_series(recent, "High")
    low = _numeric_series(recent, "Low")
    close = _numeric_series(recent, "Close")

    valid = pd.DataFrame(
        {
            "High": high,
            "Low": low,
            "Close": close,
        }
    ).dropna()

    if len(valid) < pivot_window:
        raise ValueError("Not enough valid data to detect price levels.")

    high = valid["High"]
    low = valid["Low"]
    close = valid["Close"]

    if current_price is None:
        current_price = float(close.iloc[-1])
    else:
        current_price = float(current_price)

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = float(true_range.rolling(14).mean().iloc[-1])

    if not np.isfinite(atr) or atr <= 0:
        atr = float((high - low).median())

    if not np.isfinite(atr) or atr <= 0:
        atr = max(current_price * 0.01, 0.01)

    tolerance = max(atr * 0.60, current_price * 0.003)

    rolling_high = high.rolling(
        window=pivot_window,
        center=True,
    ).max()

    rolling_low = low.rolling(
        window=pivot_window,
        center=True,
    ).min()

    pivot_highs = high[
        np.isclose(
            high.to_numpy(),
            rolling_high.to_numpy(),
            equal_nan=False,
        )
    ].tolist()

    pivot_lows = low[
        np.isclose(
            low.to_numpy(),
            rolling_low.to_numpy(),
            equal_nan=False,
        )
    ].tolist()

    clustered_resistance = _cluster_levels(
        pivot_highs,
        tolerance,
    )

    clustered_support = _cluster_levels(
        pivot_lows,
        tolerance,
    )

    supports = sorted(
        [
            level
            for level in clustered_support
            if level < current_price
        ],
        reverse=True,
    )[:max_levels]

    resistances = sorted(
        [
            level
            for level in clustered_resistance
            if level > current_price
        ]
    )[:max_levels]

    nearest_support = supports[0] if supports else None
    nearest_resistance = resistances[0] if resistances else None

    support_distance_percentage = (
        ((current_price - nearest_support) / current_price) * 100
        if nearest_support is not None and current_price > 0
        else None
    )

    resistance_distance_percentage = (
        ((nearest_resistance - current_price) / current_price) * 100
        if nearest_resistance is not None and current_price > 0
        else None
    )

    latest_close = float(close.iloc[-1])
    previous_close_value = (
        float(close.iloc[-2])
        if len(close) >= 2
        else latest_close
    )

    breakout_status = "RANGE-BOUND"

    if nearest_resistance is not None:
        if latest_close > nearest_resistance and previous_close_value <= nearest_resistance:
            breakout_status = "BULLISH BREAKOUT"

    if nearest_support is not None:
        if latest_close < nearest_support and previous_close_value >= nearest_support:
            breakout_status = "BEARISH BREAKDOWN"

    if breakout_status == "RANGE-BOUND":
        if nearest_resistance is None and nearest_support is not None:
            breakout_status = "ABOVE DETECTED SUPPORT"
        elif nearest_support is None and nearest_resistance is not None:
            breakout_status = "BELOW DETECTED RESISTANCE"
        elif nearest_support is None and nearest_resistance is None:
            breakout_status = "NO CLEAR LEVELS"

    return {
        "current_price": current_price,
        "supports": supports,
        "resistances": resistances,
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "support_distance_percentage": support_distance_percentage,
        "resistance_distance_percentage": resistance_distance_percentage,
        "breakout_status": breakout_status,
        "atr": atr,
        "tolerance": tolerance,
        "lookback": len(valid),
    }