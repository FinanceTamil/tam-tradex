from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

import pandas as pd

from strategy_lab import StrategyParameters, run_strategy_backtest


SUPPORTED_STRATEGIES = [
    "Moving Average Crossover",
    "RSI Reversal",
    "MACD Crossover",
    "Bollinger Mean Reversion",
    "Breakout",
]


def _safe_float(value: Any) -> float:
    try:
        if hasattr(value, "item"):
            return float(value.item())
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalise_values(
    values: Iterable[Any],
    *,
    cast,
) -> list[Any]:
    clean_values = []

    for value in values:
        clean_value = cast(value)

        if clean_value not in clean_values:
            clean_values.append(clean_value)

    return clean_values


def _score_results(results: pd.DataFrame) -> pd.DataFrame:
    """
    Rank optimisation runs using return, Sharpe ratio, drawdown,
    profit factor and trade count.

    Scores are relative to the tested parameter combinations.
    """

    scored = results.copy()

    if scored.empty:
        scored["Optimisation Score"] = pd.Series(dtype=float)
        return scored

    scored["Return Rank"] = scored["Return %"].rank(
        pct=True,
        method="average",
    )

    scored["Sharpe Rank"] = scored["Sharpe"].rank(
        pct=True,
        method="average",
    )

    # Drawdowns are normally negative. A value closer to zero is preferred.
    scored["Drawdown Rank"] = scored["Max Drawdown %"].rank(
        pct=True,
        ascending=True,
        method="average",
    )

    scored["Profit Factor Rank"] = (
        scored["Profit Factor"]
        .clip(upper=10)
        .rank(
            pct=True,
            method="average",
        )
    )

    scored["Trade Quality Rank"] = (
        scored["Trades"]
        .clip(upper=20)
        .rank(
            pct=True,
            method="average",
        )
    )

    scored["Optimisation Score"] = (
        scored["Return Rank"] * 0.25
        + scored["Sharpe Rank"] * 0.30
        + scored["Drawdown Rank"] * 0.25
        + scored["Profit Factor Rank"] * 0.15
        + scored["Trade Quality Rank"] * 0.05
    ) * 100

    return scored


def optimise_strategy(
    data: pd.DataFrame,
    strategy_name: str,
    initial_capital: float,
    parameter_grid: dict[str, Iterable[Any]],
    *,
    maximum_tests: int = 500,
) -> dict[str, Any]:
    """
    Test parameter combinations for one Strategy Lab strategy.

    The function deliberately limits the number of combinations to prevent
    the Streamlit application becoming slow or unresponsive.
    """

    if strategy_name not in SUPPORTED_STRATEGIES:
        raise ValueError(
            f"Unsupported strategy: {strategy_name}"
        )

    if data is None or data.empty:
        raise ValueError("Market data is empty.")

    if initial_capital <= 0:
        raise ValueError(
            "Initial capital must be greater than zero."
        )

    maximum_tests = max(int(maximum_tests), 1)

    base_parameters = StrategyParameters()
    base_parameter_dict = asdict(base_parameters)

    clean_grid: dict[str, list[Any]] = {}

    for parameter_name, values in parameter_grid.items():
        if parameter_name not in base_parameter_dict:
            raise ValueError(
                f"Unknown StrategyParameters field: {parameter_name}"
            )

        current_value = base_parameter_dict[parameter_name]

        if isinstance(current_value, int):
            clean_grid[parameter_name] = _normalise_values(
                values,
                cast=int,
            )
        else:
            clean_grid[parameter_name] = _normalise_values(
                values,
                cast=float,
            )

        if not clean_grid[parameter_name]:
            raise ValueError(
                f"No values were supplied for {parameter_name}."
            )

    parameter_names = list(clean_grid.keys())

    combinations = list(
        __import__("itertools").product(
            *[
                clean_grid[parameter_name]
                for parameter_name in parameter_names
            ]
        )
    )

    total_combinations = len(combinations)

    if total_combinations > maximum_tests:
        combinations = combinations[:maximum_tests]

    rows: list[dict[str, Any]] = []
    detailed_results: dict[int, dict[str, Any]] = {}
    skipped_combinations: list[str] = []

    for test_number, parameter_values in enumerate(
        combinations,
        start=1,
    ):
        test_parameter_dict = base_parameter_dict.copy()

        for parameter_name, parameter_value in zip(
            parameter_names,
            parameter_values,
        ):
            test_parameter_dict[parameter_name] = parameter_value

        # Invalid MA combinations are skipped instead of crashing the run.
        if (
            test_parameter_dict["short_ma"]
            >= test_parameter_dict["long_ma"]
        ):
            skipped_combinations.append(
                f"Test {test_number}: short_ma must be below long_ma."
            )
            continue

        # RSI entry threshold must remain below the exit threshold.
        if (
            test_parameter_dict["rsi_buy"]
            >= test_parameter_dict["rsi_sell"]
        ):
            skipped_combinations.append(
                f"Test {test_number}: rsi_buy must be below rsi_sell."
            )
            continue

        parameters = StrategyParameters(
            **test_parameter_dict
        )

        try:
            result = run_strategy_backtest(
                data=data,
                strategy_name=strategy_name,
                initial_capital=float(initial_capital),
                parameters=parameters,
            )
        except Exception as error:
            skipped_combinations.append(
                f"Test {test_number}: {error}"
            )
            continue

        metrics = result["metrics"]

        row = {
            "Test": test_number,
            "Strategy": strategy_name,
            **{
                parameter_name: test_parameter_dict[
                    parameter_name
                ]
                for parameter_name in parameter_names
            },
            "Final Value": _safe_float(
                result["final_value"]
            ),
            "Return %": _safe_float(
                metrics.get("Return %", 0.0)
            ),
            "CAGR %": _safe_float(
                metrics.get("CAGR %", 0.0)
            ),
            "Sharpe": _safe_float(
                metrics.get("Sharpe", 0.0)
            ),
            "Sortino": _safe_float(
                metrics.get("Sortino", 0.0)
            ),
            "Max Drawdown %": _safe_float(
                metrics.get("Max Drawdown %", 0.0)
            ),
            "Win Rate %": _safe_float(
                metrics.get("Win Rate %", 0.0)
            ),
            "Profit Factor": _safe_float(
                metrics.get("Profit Factor", 0.0)
            ),
            "Expectancy": _safe_float(
                metrics.get("Expectancy", 0.0)
            ),
            "Volatility %": _safe_float(
                metrics.get("Volatility %", 0.0)
            ),
            "Trades": int(
                metrics.get("Trades", 0)
            ),
        }

        rows.append(row)
        detailed_results[test_number] = result

    results = pd.DataFrame(rows)

    if results.empty:
        return {
            "strategy": strategy_name,
            "results": results,
            "best_result": None,
            "best_parameters": {},
            "best_test": None,
            "detailed_results": detailed_results,
            "tested_combinations": 0,
            "requested_combinations": total_combinations,
            "truncated": total_combinations > maximum_tests,
            "skipped": skipped_combinations,
        }

    scored_results = _score_results(results)

    scored_results = scored_results.sort_values(
        [
            "Optimisation Score",
            "Sharpe",
            "Return %",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).reset_index(drop=True)

    best_row = scored_results.iloc[0]

    best_test = int(best_row["Test"])

    best_parameters = {
        parameter_name: best_row[parameter_name]
        for parameter_name in parameter_names
    }

    return {
        "strategy": strategy_name,
        "results": scored_results,
        "best_result": best_row.to_dict(),
        "best_parameters": best_parameters,
        "best_test": best_test,
        "detailed_results": detailed_results,
        "tested_combinations": len(scored_results),
        "requested_combinations": total_combinations,
        "truncated": total_combinations > maximum_tests,
        "skipped": skipped_combinations,
    }