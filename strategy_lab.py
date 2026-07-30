from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


TRADING_DAYS = 252


@dataclass
class StrategyParameters:
    short_ma: int = 10
    long_ma: int = 30
    rsi_buy: float = 30.0
    rsi_sell: float = 70.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bollinger_window: int = 20
    bollinger_std: float = 2.0
    breakout_window: int = 20
    stop_loss_pct: float = 8.0
    take_profit_pct: float = 15.0


def _safe_float(value: Any) -> float:
    try:
        if hasattr(value, "item"):
            return float(value.item())
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _prepare_data(
    data: pd.DataFrame,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    required_columns = {"Close"}

    missing_columns = required_columns.difference(data.columns)

    if missing_columns:
        raise ValueError(
            "Strategy data is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    frame = data.copy()
    frame["Close"] = pd.to_numeric(
        frame["Close"],
        errors="coerce",
    )

    if "High" not in frame.columns:
        frame["High"] = frame["Close"]

    if "Low" not in frame.columns:
        frame["Low"] = frame["Close"]

    frame["High"] = pd.to_numeric(
        frame["High"],
        errors="coerce",
    )
    frame["Low"] = pd.to_numeric(
        frame["Low"],
        errors="coerce",
    )

    frame["short_ma_lab"] = frame["Close"].rolling(
        parameters.short_ma
    ).mean()

    frame["long_ma_lab"] = frame["Close"].rolling(
        parameters.long_ma
    ).mean()

    price_change = frame["Close"].diff()
    gains = price_change.clip(lower=0)
    losses = -price_change.clip(upper=0)

    average_gain = gains.rolling(14).mean()
    average_loss = losses.rolling(14).mean()
    relative_strength = average_gain / average_loss.replace(0, np.nan)

    frame["rsi_lab"] = 100 - (
        100 / (1 + relative_strength)
    )

    fast_ema = frame["Close"].ewm(
        span=parameters.macd_fast,
        adjust=False,
    ).mean()

    slow_ema = frame["Close"].ewm(
        span=parameters.macd_slow,
        adjust=False,
    ).mean()

    frame["macd_lab"] = fast_ema - slow_ema
    frame["macd_signal_lab"] = frame["macd_lab"].ewm(
        span=parameters.macd_signal,
        adjust=False,
    ).mean()

    bollinger_middle = frame["Close"].rolling(
        parameters.bollinger_window
    ).mean()

    bollinger_std = frame["Close"].rolling(
        parameters.bollinger_window
    ).std()

    frame["bollinger_middle_lab"] = bollinger_middle
    frame["bollinger_upper_lab"] = (
        bollinger_middle
        + parameters.bollinger_std * bollinger_std
    )
    frame["bollinger_lower_lab"] = (
        bollinger_middle
        - parameters.bollinger_std * bollinger_std
    )

    frame["breakout_high_lab"] = (
        frame["High"]
        .shift(1)
        .rolling(parameters.breakout_window)
        .max()
    )

    frame["breakout_low_lab"] = (
        frame["Low"]
        .shift(1)
        .rolling(parameters.breakout_window)
        .min()
    )

    return frame.dropna(subset=["Close"])


def _signal_for_strategy(
    strategy_name: str,
    row: pd.Series,
    previous_row: pd.Series | None,
    parameters: StrategyParameters,
) -> tuple[bool, bool]:
    close_price = _safe_float(row["Close"])

    if strategy_name == "Moving Average Crossover":
        buy = (
            _safe_float(row["short_ma_lab"])
            > _safe_float(row["long_ma_lab"])
        )
        sell = (
            _safe_float(row["short_ma_lab"])
            < _safe_float(row["long_ma_lab"])
        )

    elif strategy_name == "RSI Reversal":
        rsi = _safe_float(row["rsi_lab"])
        buy = rsi <= parameters.rsi_buy
        sell = rsi >= parameters.rsi_sell

    elif strategy_name == "MACD Crossover":
        if previous_row is None:
            return False, False

        current_macd = _safe_float(row["macd_lab"])
        current_signal = _safe_float(row["macd_signal_lab"])
        previous_macd = _safe_float(previous_row["macd_lab"])
        previous_signal = _safe_float(previous_row["macd_signal_lab"])

        buy = (
            previous_macd <= previous_signal
            and current_macd > current_signal
        )
        sell = (
            previous_macd >= previous_signal
            and current_macd < current_signal
        )

    elif strategy_name == "Bollinger Mean Reversion":
        buy = close_price <= _safe_float(
            row["bollinger_lower_lab"]
        )
        sell = close_price >= _safe_float(
            row["bollinger_middle_lab"]
        )

    elif strategy_name == "Breakout":
        buy = close_price > _safe_float(
            row["breakout_high_lab"]
        )
        sell = close_price < _safe_float(
            row["breakout_low_lab"]
        )

    else:
        raise ValueError(
            f"Unsupported strategy: {strategy_name}"
        )

    return bool(buy), bool(sell)


def _calculate_metrics(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    initial_capital: float,
) -> dict[str, float]:
    if equity_curve.empty:
        return {
            "Return %": 0.0,
            "CAGR %": 0.0,
            "Sharpe": 0.0,
            "Sortino": 0.0,
            "Max Drawdown %": 0.0,
            "Win Rate %": 0.0,
            "Profit Factor": 0.0,
            "Expectancy": 0.0,
            "Volatility %": 0.0,
            "Trades": 0,
        }

    daily_returns = equity_curve.pct_change().dropna()

    total_return = (
        equity_curve.iloc[-1] / initial_capital - 1
    ) * 100

    elapsed_days = max(
        (
            equity_curve.index[-1]
            - equity_curve.index[0]
        ).days,
        1,
    )

    years = elapsed_days / 365.25

    cagr = (
        (
            equity_curve.iloc[-1] / initial_capital
        ) ** (1 / years) - 1
    ) * 100 if years > 0 else 0.0

    volatility = (
        daily_returns.std() * math.sqrt(TRADING_DAYS) * 100
        if not daily_returns.empty
        else 0.0
    )

    sharpe = (
        daily_returns.mean()
        / daily_returns.std()
        * math.sqrt(TRADING_DAYS)
        if (
            not daily_returns.empty
            and daily_returns.std() != 0
        )
        else 0.0
    )

    downside_returns = daily_returns[daily_returns < 0]

    sortino = (
        daily_returns.mean()
        / downside_returns.std()
        * math.sqrt(TRADING_DAYS)
        if (
            not downside_returns.empty
            and downside_returns.std() != 0
        )
        else 0.0
    )

    running_peak = equity_curve.cummax()
    drawdown = (
        equity_curve - running_peak
    ) / running_peak

    maximum_drawdown = _safe_float(
        drawdown.min() * 100
    )

    if trades.empty:
        winning_trades = pd.Series(dtype=float)
        losing_trades = pd.Series(dtype=float)
        completed_trades = 0
    else:
        completed = trades[
            trades["Action"] == "SELL"
        ].copy()

        completed_trades = len(completed)
        winning_trades = completed[
            completed["Trade P/L"] > 0
        ]["Trade P/L"]
        losing_trades = completed[
            completed["Trade P/L"] < 0
        ]["Trade P/L"]

    win_rate = (
        len(winning_trades)
        / completed_trades
        * 100
        if completed_trades > 0
        else 0.0
    )

    gross_profit = winning_trades.sum()
    gross_loss = abs(losing_trades.sum())

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else (
            float("inf")
            if gross_profit > 0
            else 0.0
        )
    )

    expectancy = (
        trades.loc[
            trades["Action"] == "SELL",
            "Trade P/L",
        ].mean()
        if completed_trades > 0
        else 0.0
    )

    return {
        "Return %": round(_safe_float(total_return), 2),
        "CAGR %": round(_safe_float(cagr), 2),
        "Sharpe": round(_safe_float(sharpe), 2),
        "Sortino": round(_safe_float(sortino), 2),
        "Max Drawdown %": round(
            _safe_float(maximum_drawdown),
            2,
        ),
        "Win Rate %": round(_safe_float(win_rate), 2),
        "Profit Factor": (
            round(_safe_float(profit_factor), 2)
            if math.isfinite(profit_factor)
            else 999.0
        ),
        "Expectancy": round(_safe_float(expectancy), 2),
        "Volatility %": round(_safe_float(volatility), 2),
        "Trades": int(completed_trades),
    }


def run_strategy_backtest(
    data: pd.DataFrame,
    strategy_name: str,
    initial_capital: float,
    parameters: StrategyParameters,
) -> dict[str, Any]:
    if initial_capital <= 0:
        raise ValueError(
            "Initial capital must be greater than zero."
        )

    frame = _prepare_data(
        data,
        parameters,
    )

    cash = float(initial_capital)
    quantity = 0.0
    entry_price = 0.0
    equity_records: list[dict[str, Any]] = []
    trade_records: list[dict[str, Any]] = []

    previous_row = None

    for index, row in frame.iterrows():
        close_price = _safe_float(row["Close"])

        buy_signal, sell_signal = _signal_for_strategy(
            strategy_name,
            row,
            previous_row,
            parameters,
        )

        stop_loss_triggered = (
            quantity > 0
            and close_price
            <= entry_price
            * (1 - parameters.stop_loss_pct / 100)
        )

        take_profit_triggered = (
            quantity > 0
            and close_price
            >= entry_price
            * (1 + parameters.take_profit_pct / 100)
        )

        if buy_signal and quantity == 0 and close_price > 0:
            quantity = cash / close_price
            entry_price = close_price
            cash = 0.0

            trade_records.append(
                {
                    "Date": index,
                    "Action": "BUY",
                    "Price": close_price,
                    "Quantity": quantity,
                    "Trade P/L": np.nan,
                    "Exit Reason": "",
                }
            )

        elif quantity > 0 and (
            sell_signal
            or stop_loss_triggered
            or take_profit_triggered
        ):
            sale_value = quantity * close_price
            trade_profit = (
                close_price - entry_price
            ) * quantity

            if stop_loss_triggered:
                exit_reason = "Stop Loss"
            elif take_profit_triggered:
                exit_reason = "Take Profit"
            else:
                exit_reason = "Strategy Signal"

            cash = sale_value

            trade_records.append(
                {
                    "Date": index,
                    "Action": "SELL",
                    "Price": close_price,
                    "Quantity": quantity,
                    "Trade P/L": trade_profit,
                    "Exit Reason": exit_reason,
                }
            )

            quantity = 0.0
            entry_price = 0.0

        portfolio_value = cash + quantity * close_price

        equity_records.append(
            {
                "Date": index,
                "Portfolio Value": portfolio_value,
            }
        )

        previous_row = row

    if quantity > 0:
        final_price = _safe_float(frame["Close"].iloc[-1])
        final_value = quantity * final_price
        final_profit = (
            final_price - entry_price
        ) * quantity

        cash = final_value

        trade_records.append(
            {
                "Date": frame.index[-1],
                "Action": "SELL",
                "Price": final_price,
                "Quantity": quantity,
                "Trade P/L": final_profit,
                "Exit Reason": "End of Test",
            }
        )

        equity_records[-1]["Portfolio Value"] = cash

    equity_curve = pd.DataFrame(
        equity_records
    ).set_index("Date")["Portfolio Value"]

    trade_log = pd.DataFrame(
        trade_records
    )

    metrics = _calculate_metrics(
        equity_curve,
        trade_log,
        initial_capital,
    )

    return {
        "strategy": strategy_name,
        "metrics": metrics,
        "equity_curve": equity_curve,
        "trade_log": trade_log,
        "final_value": _safe_float(
            equity_curve.iloc[-1]
        ),
    }


def compare_strategies(
    data: pd.DataFrame,
    strategies: list[str],
    initial_capital: float,
    parameters: StrategyParameters,
) -> dict[str, Any]:
    results = {}

    for strategy_name in strategies:
        results[strategy_name] = run_strategy_backtest(
            data=data,
            strategy_name=strategy_name,
            initial_capital=initial_capital,
            parameters=parameters,
        )

    comparison_rows = []

    for strategy_name, result in results.items():
        row = {
            "Strategy": strategy_name,
            **result["metrics"],
            "Final Value": result["final_value"],
        }
        comparison_rows.append(row)

    comparison = pd.DataFrame(
        comparison_rows
    )

    if comparison.empty:
        recommendation = {
            "strategy": "Unavailable",
            "confidence": 0.0,
            "reason": "No valid strategy results were produced.",
        }
    else:
        scoring = comparison.copy()

        scoring["Return Score"] = scoring["Return %"].rank(
            pct=True
        )
        scoring["Sharpe Score"] = scoring["Sharpe"].rank(
            pct=True
        )
        scoring["Drawdown Score"] = (
            -scoring["Max Drawdown %"]
        ).rank(pct=True)
        scoring["Profit Factor Score"] = scoring[
            "Profit Factor"
        ].clip(upper=10).rank(pct=True)

        scoring["Composite Score"] = (
            scoring["Return Score"] * 0.30
            + scoring["Sharpe Score"] * 0.30
            + scoring["Drawdown Score"] * 0.25
            + scoring["Profit Factor Score"] * 0.15
        )

        best_row = scoring.sort_values(
            "Composite Score",
            ascending=False,
        ).iloc[0]

        confidence = _safe_float(
            best_row["Composite Score"] * 100
        )

        recommendation = {
            "strategy": best_row["Strategy"],
            "confidence": round(confidence, 1),
            "reason": (
                "Highest composite score across total return, "
                "risk-adjusted return, drawdown control and profit factor."
            ),
        }

    return {
        "results": results,
        "comparison": comparison,
        "recommendation": recommendation,
    }