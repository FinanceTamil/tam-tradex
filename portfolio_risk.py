from __future__ import annotations

from math import sqrt
from typing import Any

import pandas as pd


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def calculate_portfolio_risk(
    positions: pd.DataFrame,
    *,
    cash_percentage: float,
) -> dict[str, Any]:
    """
    Calculate a portfolio risk and diversification assessment.

    The score is based on:
    - position concentration,
    - effective number of positions,
    - cash reserve,
    - balance between winning and losing positions.

    This is a heuristic portfolio-health model, not a regulatory risk model.
    """

    cash_percentage = _clamp(cash_percentage)

    if positions is None or positions.empty:
        return {
            "risk_score": 0.0,
            "diversification_score": 0.0,
            "risk_level": "No Positions",
            "concentration_score": 0.0,
            "cash_score": 100.0,
            "performance_balance_score": 0.0,
            "herfindahl_index": 0.0,
            "effective_positions": 0.0,
            "largest_position_percentage": 0.0,
            "top_three_percentage": 0.0,
            "messages": [
                "No open positions are available for risk assessment."
            ],
        }

    dataframe = positions.copy()

    if "Allocation %" not in dataframe.columns:
        if "Market Value" not in dataframe.columns:
            raise ValueError(
                "Positions must include either 'Allocation %' or 'Market Value'."
            )

        total_market_value = pd.to_numeric(
            dataframe["Market Value"],
            errors="coerce",
        ).fillna(0.0).sum()

        dataframe["Allocation %"] = (
            pd.to_numeric(
                dataframe["Market Value"],
                errors="coerce",
            ).fillna(0.0)
            / total_market_value
            * 100
            if total_market_value > 0
            else 0.0
        )

    allocations = pd.to_numeric(
        dataframe["Allocation %"],
        errors="coerce",
    ).fillna(0.0)

    allocations = allocations[allocations > 0]

    if allocations.empty:
        return {
            "risk_score": 0.0,
            "diversification_score": 0.0,
            "risk_level": "No Positions",
            "concentration_score": 0.0,
            "cash_score": 100.0,
            "performance_balance_score": 0.0,
            "herfindahl_index": 0.0,
            "effective_positions": 0.0,
            "largest_position_percentage": 0.0,
            "top_three_percentage": 0.0,
            "messages": [
                "No positive position allocations are available."
            ],
        }

    weights = allocations / 100.0
    herfindahl_index = float((weights ** 2).sum())
    effective_positions = (
        1.0 / herfindahl_index
        if herfindahl_index > 0
        else 0.0
    )

    largest_position_percentage = float(allocations.max())
    top_three_percentage = float(
        allocations.sort_values(ascending=False).head(3).sum()
    )

    position_count = len(allocations)

    # HHI of an equally weighted portfolio is 1 / N.
    minimum_hhi = 1.0 / position_count
    maximum_hhi = 1.0

    concentration_score = (
        (maximum_hhi - herfindahl_index)
        / (maximum_hhi - minimum_hhi)
        * 100
        if position_count > 1 and maximum_hhi > minimum_hhi
        else 0.0
    )
    concentration_score = _clamp(concentration_score)

    # A practical cash buffer is treated as approximately 10%–30%.
    if 10 <= cash_percentage <= 30:
        cash_score = 100.0
    elif cash_percentage < 10:
        cash_score = _clamp(cash_percentage / 10 * 100)
    else:
        cash_score = _clamp(100 - ((cash_percentage - 30) * 1.5))

    if "Unrealised P/L" in dataframe.columns:
        pnl = pd.to_numeric(
            dataframe["Unrealised P/L"],
            errors="coerce",
        ).fillna(0.0)

        winning_positions = int((pnl > 0).sum())
        losing_positions = int((pnl < 0).sum())
        active_positions = winning_positions + losing_positions

        performance_balance_score = (
            winning_positions / active_positions * 100
            if active_positions > 0
            else 50.0
        )
    else:
        winning_positions = 0
        losing_positions = 0
        performance_balance_score = 50.0

    diversification_score = _clamp(
        concentration_score * 0.70
        + min(effective_positions / 8.0 * 100, 100.0) * 0.30
    )

    portfolio_health_score = _clamp(
        diversification_score * 0.55
        + cash_score * 0.25
        + performance_balance_score * 0.20
    )

    risk_score = 100.0 - portfolio_health_score

    if risk_score >= 70:
        risk_level = "High"
    elif risk_score >= 45:
        risk_level = "Elevated"
    elif risk_score >= 25:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    messages: list[str] = []

    if largest_position_percentage >= 50:
        messages.append(
            "A single position represents at least 50% of invested capital."
        )
    elif largest_position_percentage >= 35:
        messages.append(
            "The portfolio has material single-position concentration."
        )
    else:
        messages.append(
            "No single position dominates invested capital."
        )

    if top_three_percentage >= 80 and position_count > 3:
        messages.append(
            "The three largest positions account for at least 80% of invested capital."
        )

    if effective_positions < 3:
        messages.append(
            "The effective number of positions is below three."
        )
    elif effective_positions < 5:
        messages.append(
            "Diversification is moderate based on effective position count."
        )
    else:
        messages.append(
            "The allocation structure is reasonably diversified."
        )

    if cash_percentage < 10:
        messages.append(
            "Cash reserves are below 10% of total account value."
        )
    elif cash_percentage > 60:
        messages.append(
            "More than 60% of account value remains undeployed."
        )
    else:
        messages.append(
            "Cash reserves are within a practical operating range."
        )

    if losing_positions > winning_positions:
        messages.append(
            "More open positions are losing than winning."
        )

    return {
        "risk_score": risk_score,
        "portfolio_health_score": portfolio_health_score,
        "diversification_score": diversification_score,
        "risk_level": risk_level,
        "concentration_score": concentration_score,
        "cash_score": cash_score,
        "performance_balance_score": performance_balance_score,
        "herfindahl_index": herfindahl_index,
        "effective_positions": effective_positions,
        "largest_position_percentage": largest_position_percentage,
        "top_three_percentage": top_three_percentage,
        "winning_positions": winning_positions,
        "losing_positions": losing_positions,
        "messages": messages,
    }