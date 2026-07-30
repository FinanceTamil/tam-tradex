import math

import pandas as pd


def safe_float(value) -> float:
    """
    Convert pandas or Python numeric values into a float.
    """

    try:
        if hasattr(value, "item"):
            return float(value.item())

        return float(value)

    except (TypeError, ValueError):
        return 0.0


def calculate_max_drawdown(
    equity_curve: pd.Series,
) -> float:
    """
    Calculate maximum portfolio drawdown.
    """

    if equity_curve.empty:
        return 0.0

    running_peak = equity_curve.cummax()

    drawdown = (
        equity_curve - running_peak
    ) / running_peak

    return safe_float(
        drawdown.min() * 100
    )


def calculate_sharpe_ratio(
    equity_curve: pd.Series,
    trading_days: int = 252,
) -> float:
    """
    Calculate annualised Sharpe ratio.

    This educational version assumes a 0% risk-free rate.
    """

    if equity_curve.empty:
        return 0.0

    daily_returns = (
        equity_curve
        .pct_change()
        .dropna()
    )

    if daily_returns.empty:
        return 0.0

    standard_deviation = (
        daily_returns.std()
    )

    if (
        standard_deviation == 0
        or pd.isna(standard_deviation)
    ):
        return 0.0

    sharpe_ratio = (
        daily_returns.mean()
        / standard_deviation
    ) * math.sqrt(trading_days)

    return safe_float(sharpe_ratio)


def run_backtest(
    data: pd.DataFrame,
    initial_capital: float = 10_000.0,
) -> dict:
    """
    Backtest the TAM Tradex strategy.

    BUY:
    - Short moving average above long moving average
    - RSI below 70

    SELL:
    - Short moving average below long moving average
    - RSI above 30

    The system holds one full position at a time.
    """

    required_columns = {
        "Close",
        "short_average",
        "long_average",
        "rsi",
    }

    missing_columns = (
        required_columns
        - set(data.columns)
    )

    if missing_columns:

        raise ValueError(
            "Missing columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    if initial_capital <= 0:

        raise ValueError(
            "Initial capital must be greater than zero."
        )

    backtest_data = (
        data.copy()
        .dropna(
            subset=[
                "Close",
                "short_average",
                "long_average",
                "rsi",
            ]
        )
    )

    if backtest_data.empty:

        raise ValueError(
            "No valid historical data is available."
        )

    cash = float(initial_capital)

    quantity = 0.0

    entry_price = 0.0

    equity_values = []

    trade_log = []

    winning_trades = 0

    completed_trades = 0

    for date, row in backtest_data.iterrows():

        close_price = safe_float(
            row["Close"]
        )

        short_average = safe_float(
            row["short_average"]
        )

        long_average = safe_float(
            row["long_average"]
        )

        rsi = safe_float(
            row["rsi"]
        )

        buy_condition = (
            short_average > long_average
            and rsi < 70
        )

        sell_condition = (
            short_average < long_average
            and rsi > 30
        )

        if (
            buy_condition
            and quantity == 0
        ):

            quantity = (
                cash / close_price
            )

            entry_price = close_price

            cash = 0.0

            trade_log.append(
                {
                    "Date": date,
                    "Action": "BUY",
                    "Price": round(
                        close_price,
                        2,
                    ),
                    "Quantity": round(
                        quantity,
                        6,
                    ),
                    "Trade P/L": None,
                }
            )

        elif (
            sell_condition
            and quantity > 0
        ):

            sale_value = (
                quantity
                * close_price
            )

            trade_profit = (
                close_price
                - entry_price
            ) * quantity

            cash = sale_value

            completed_trades += 1

            if trade_profit > 0:
                winning_trades += 1

            trade_log.append(
                {
                    "Date": date,
                    "Action": "SELL",
                    "Price": round(
                        close_price,
                        2,
                    ),
                    "Quantity": round(
                        quantity,
                        6,
                    ),
                    "Trade P/L": round(
                        trade_profit,
                        2,
                    ),
                }
            )

            quantity = 0.0

            entry_price = 0.0

        portfolio_value = (
            cash
            + quantity * close_price
        )

        equity_values.append(
            {
                "Date": date,
                "Portfolio Value": portfolio_value,
                "Close": close_price,
            }
        )

    final_price = safe_float(
        backtest_data[
            "Close"
        ].iloc[-1]
    )

    first_price = safe_float(
        backtest_data[
            "Close"
        ].iloc[0]
    )

    final_portfolio_value = (
        cash
        + quantity * final_price
    )

    strategy_return = (
        (
            final_portfolio_value
            - initial_capital
        )
        / initial_capital
    ) * 100

    buy_and_hold_return = (
        (
            final_price
            - first_price
        )
        / first_price
    ) * 100

    win_rate = (
        (
            winning_trades
            / completed_trades
        )
        * 100
        if completed_trades > 0
        else 0.0
    )

    equity_curve = pd.DataFrame(
        equity_values
    )

    equity_curve = (
        equity_curve
        .set_index("Date")
    )

    maximum_drawdown = (
        calculate_max_drawdown(
            equity_curve[
                "Portfolio Value"
            ]
        )
    )

    sharpe_ratio = (
        calculate_sharpe_ratio(
            equity_curve[
                "Portfolio Value"
            ]
        )
    )

    trade_log_dataframe = pd.DataFrame(
        trade_log
    )

    return {
        "initial_capital": round(
            initial_capital,
            2,
        ),
        "final_portfolio_value": round(
            final_portfolio_value,
            2,
        ),
        "strategy_return": round(
            strategy_return,
            2,
        ),
        "buy_and_hold_return": round(
            buy_and_hold_return,
            2,
        ),
        "completed_trades": completed_trades,
        "winning_trades": winning_trades,
        "win_rate": round(
            win_rate,
            2,
        ),
        "maximum_drawdown": round(
            maximum_drawdown,
            2,
        ),
        "sharpe_ratio": round(
            sharpe_ratio,
            2,
        ),
        "open_position": quantity > 0,
        "equity_curve": equity_curve,
        "trade_log": trade_log_dataframe,
    }