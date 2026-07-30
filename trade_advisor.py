import math

import pandas as pd


def _safe_float(value) -> float:
    """
    Convert pandas or Python numeric values into a float.
    """

    try:
        if isinstance(value, pd.Series):
            value = value.dropna()

            if value.empty:
                return 0.0

            value = value.iloc[-1]

        if isinstance(value, pd.DataFrame):
            value = value.iloc[:, 0]
            value = value.dropna()

            if value.empty:
                return 0.0

            value = value.iloc[-1]

        if hasattr(value, "item"):
            return float(value.item())

        return float(value)

    except (
        TypeError,
        ValueError,
        IndexError,
    ):
        return 0.0


def _flatten_columns(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert yfinance MultiIndex columns into normal columns.

    Example:
    ("Close", "AAPL") becomes "Close"
    """

    cleaned_data = data.copy()

    if isinstance(
        cleaned_data.columns,
        pd.MultiIndex,
    ):
        cleaned_data.columns = [
            column[0]
            if isinstance(
                column,
                tuple,
            )
            else column
            for column in cleaned_data.columns
        ]

    cleaned_data.columns = [
        str(column)
        for column in cleaned_data.columns
    ]

    cleaned_data = cleaned_data.loc[
        :,
        ~cleaned_data.columns.duplicated(
            keep="first"
        ),
    ]

    return cleaned_data


def _get_numeric_series(
    data: pd.DataFrame,
    column_name: str,
) -> pd.Series:
    """
    Extract a single clean numeric Series.
    """

    cleaned_data = _flatten_columns(
        data
    )

    if column_name not in cleaned_data.columns:
        return pd.Series(
            dtype="float64"
        )

    column_data = cleaned_data[
        column_name
    ]

    if isinstance(
        column_data,
        pd.DataFrame,
    ):
        column_data = column_data.iloc[
            :,
            0,
        ]

    column_data = column_data.squeeze()

    column_data = pd.to_numeric(
        column_data,
        errors="coerce",
    )

    return column_data


def _calculate_atr(
    data: pd.DataFrame,
    period: int = 14,
) -> float:
    """
    Calculate the latest Average True Range.
    """

    high = _get_numeric_series(
        data,
        "High",
    )

    low = _get_numeric_series(
        data,
        "Low",
    )

    close = _get_numeric_series(
        data,
        "Close",
    )

    if (
        high.empty
        or low.empty
        or close.empty
    ):
        return 0.0

    previous_close = close.shift(1)

    true_range_dataframe = pd.DataFrame(
        {
            "high_low": (
                high - low
            ),
            "high_previous_close": (
                high
                - previous_close
            ).abs(),
            "low_previous_close": (
                low
                - previous_close
            ).abs(),
        }
    )

    true_range = (
        true_range_dataframe
        .max(axis=1)
    )

    atr_series = (
        true_range
        .rolling(
            window=period,
            min_periods=period,
        )
        .mean()
        .dropna()
    )

    if atr_series.empty:
        return 0.0

    return _safe_float(
        atr_series.iloc[-1]
    )


def _calculate_annualised_volatility(
    data: pd.DataFrame,
    trading_days: int = 252,
) -> float:
    """
    Calculate annualised historical volatility.
    """

    close = _get_numeric_series(
        data,
        "Close",
    )

    if close.empty:
        return 0.0

    returns = (
        close
        .pct_change(
            fill_method=None
        )
        .dropna()
    )

    if returns.empty:
        return 0.0

    standard_deviation = (
        returns.std()
    )

    if (
        pd.isna(
            standard_deviation
        )
        or standard_deviation == 0
    ):
        return 0.0

    volatility = (
        standard_deviation
        * math.sqrt(
            trading_days
        )
        * 100
    )

    return _safe_float(
        volatility
    )


def generate_trade_advice(
    data: pd.DataFrame,
    ticker: str,
    latest_price: float,
    short_average: float,
    long_average: float,
    rsi: float,
    rule_signal: str,
    available_cash: float,
    owned_quantity: float = 0.0,
    risk_profile: str = "Balanced",
) -> dict:
    """
    Generate a structured risk-aware trade recommendation.
    """

    cleaned_data = _flatten_columns(
        data
    )

    latest_price = _safe_float(
        latest_price
    )

    short_average = _safe_float(
        short_average
    )

    long_average = _safe_float(
        long_average
    )

    rsi = _safe_float(
        rsi
    )

    available_cash = max(
        _safe_float(
            available_cash
        ),
        0.0,
    )

    owned_quantity = max(
        _safe_float(
            owned_quantity
        ),
        0.0,
    )

    if latest_price <= 0:
        raise ValueError(
            "Latest price must be greater than zero."
        )

    atr = _calculate_atr(
        cleaned_data
    )

    annualised_volatility = (
        _calculate_annualised_volatility(
            cleaned_data
        )
    )

    trend_gap_percentage = (
        (
            short_average
            - long_average
        )
        / long_average
        * 100
        if long_average != 0
        else 0.0
    )

    score = 50.0

    reasons = []

    if short_average > long_average:

        score += 18

        reasons.append(
            "The short moving average is above "
            "the long moving average."
        )

    elif short_average < long_average:

        score -= 18

        reasons.append(
            "The short moving average is below "
            "the long moving average."
        )

    else:

        reasons.append(
            "The moving averages are aligned."
        )

    if rsi < 30:

        score += 14

        reasons.append(
            "RSI indicates oversold momentum."
        )

    elif rsi < 45:

        score += 7

        reasons.append(
            "RSI is below neutral and may support an entry."
        )

    elif rsi <= 60:

        reasons.append(
            "RSI is within a neutral momentum range."
        )

    elif rsi < 70:

        score -= 5

        reasons.append(
            "RSI is elevated but not yet overbought."
        )

    else:

        score -= 16

        reasons.append(
            "RSI indicates overbought conditions."
        )

    if rule_signal == "BUY":

        score += 14

        reasons.append(
            "The TAM Tradex strategy produces a BUY signal."
        )

    elif rule_signal == "SELL":

        score -= 14

        reasons.append(
            "The TAM Tradex strategy produces a SELL signal."
        )

    else:

        reasons.append(
            "The TAM Tradex strategy produces a HOLD signal."
        )

    score = max(
        0.0,
        min(
            score,
            100.0,
        ),
    )

    if score >= 68:

        recommendation = "BUY"

    elif score <= 35:

        if owned_quantity > 0:
            recommendation = "REDUCE"
        else:
            recommendation = "AVOID"

    else:

        recommendation = "HOLD"

    if annualised_volatility >= 55:

        risk_level = "High"

    elif annualised_volatility >= 30:

        risk_level = "Medium"

    else:

        risk_level = "Low"

    profile_settings = {
        "Conservative": {
            "risk_per_trade": 0.005,
            "maximum_allocation": 0.10,
            "atr_multiplier": 2.5,
            "reward_multiple": 2.0,
        },
        "Balanced": {
            "risk_per_trade": 0.010,
            "maximum_allocation": 0.20,
            "atr_multiplier": 2.0,
            "reward_multiple": 2.0,
        },
        "Aggressive": {
            "risk_per_trade": 0.020,
            "maximum_allocation": 0.30,
            "atr_multiplier": 1.5,
            "reward_multiple": 2.5,
        },
    }

    settings = profile_settings.get(
        risk_profile,
        profile_settings[
            "Balanced"
        ],
    )

    if atr <= 0:
        atr = (
            latest_price
            * 0.02
        )

    stop_distance = max(
        (
            atr
            * settings[
                "atr_multiplier"
            ]
        ),
        (
            latest_price
            * 0.01
        ),
    )

    stop_loss = max(
        (
            latest_price
            - stop_distance
        ),
        0.01,
    )

    take_profit = (
        latest_price
        + (
            stop_distance
            * settings[
                "reward_multiple"
            ]
        )
    )

    cash_risk_budget = (
        available_cash
        * settings[
            "risk_per_trade"
        ]
    )

    if stop_distance > 0:

        risk_based_quantity = (
            cash_risk_budget
            / stop_distance
        )

    else:

        risk_based_quantity = 0.0

    allocation_cap_value = (
        available_cash
        * settings[
            "maximum_allocation"
        ]
    )

    if latest_price > 0:

        allocation_quantity = (
            allocation_cap_value
            / latest_price
        )

    else:

        allocation_quantity = 0.0

    suggested_quantity = min(
        risk_based_quantity,
        allocation_quantity,
    )

    if recommendation != "BUY":
        suggested_quantity = 0.0

    suggested_position_value = (
        suggested_quantity
        * latest_price
    )

    if available_cash > 0:

        suggested_allocation_percentage = (
            suggested_position_value
            / available_cash
            * 100
        )

    else:

        suggested_allocation_percentage = 0.0

    confidence = (
        abs(
            score - 50.0
        )
        * 2
    )

    confidence = max(
        40.0,
        min(
            confidence,
            95.0,
        ),
    )

    if latest_price > stop_loss:

        risk_reward_ratio = (
            (
                take_profit
                - latest_price
            )
            / (
                latest_price
                - stop_loss
            )
        )

    else:

        risk_reward_ratio = 0.0

    return {
        "ticker": ticker,
        "recommendation": recommendation,
        "confidence": round(
            confidence,
            1,
        ),
        "risk_level": risk_level,
        "score": round(
            score,
            1,
        ),
        "latest_price": round(
            latest_price,
            2,
        ),
        "stop_loss": round(
            stop_loss,
            2,
        ),
        "take_profit": round(
            take_profit,
            2,
        ),
        "risk_reward_ratio": round(
            risk_reward_ratio,
            2,
        ),
        "suggested_quantity": round(
            suggested_quantity,
            4,
        ),
        "suggested_position_value": round(
            suggested_position_value,
            2,
        ),
        "suggested_allocation_percentage": round(
            suggested_allocation_percentage,
            2,
        ),
        "annualised_volatility": round(
            annualised_volatility,
            2,
        ),
        "atr": round(
            atr,
            2,
        ),
        "trend_gap_percentage": round(
            trend_gap_percentage,
            2,
        ),
        "risk_profile": risk_profile,
        "reasons": reasons,
    }