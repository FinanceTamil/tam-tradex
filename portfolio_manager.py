from __future__ import annotations

from typing import Any

import pandas as pd


RISK_PROFILES = {
    "Conservative": {
        "target_cash_percentage": 30.0,
        "maximum_position_percentage": 20.0,
        "rebalance_threshold_percentage": 4.0,
    },
    "Balanced": {
        "target_cash_percentage": 20.0,
        "maximum_position_percentage": 25.0,
        "rebalance_threshold_percentage": 5.0,
    },
    "Aggressive": {
        "target_cash_percentage": 10.0,
        "maximum_position_percentage": 35.0,
        "rebalance_threshold_percentage": 7.0,
    },
}


def _safe_float(value: Any) -> float:
    try:
        if hasattr(value, "item"):
            return float(value.item())
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def generate_rebalance_plan(
    positions: pd.DataFrame,
    *,
    cash: float,
    account_value: float,
    risk_profile: str,
) -> dict[str, Any]:
    """
    Generate a heuristic portfolio rebalancing plan.

    The model:
    - reserves a profile-specific cash target,
    - equally weights invested capital across existing positions,
    - limits each target allocation,
    - recommends BUY, SELL, HOLD or REVIEW actions.

    This is an educational allocation model rather than personalised advice.
    """

    profile = RISK_PROFILES.get(
        risk_profile,
        RISK_PROFILES["Balanced"],
    )

    target_cash_percentage = profile["target_cash_percentage"]
    maximum_position_percentage = profile["maximum_position_percentage"]
    rebalance_threshold_percentage = profile[
        "rebalance_threshold_percentage"
    ]

    cash = max(_safe_float(cash), 0.0)
    account_value = max(_safe_float(account_value), 0.0)

    if positions is None or positions.empty or account_value <= 0:
        return {
            "risk_profile": risk_profile,
            "target_cash_percentage": target_cash_percentage,
            "target_cash_value": account_value
            * target_cash_percentage
            / 100,
            "current_cash_percentage": (
                cash / account_value * 100
                if account_value > 0
                else 0.0
            ),
            "rows": [],
            "summary": {
                "buy_value": 0.0,
                "sell_value": 0.0,
                "hold_count": 0,
                "buy_count": 0,
                "sell_count": 0,
                "review_count": 0,
            },
            "messages": [
                "No open positions are available for rebalancing."
            ],
        }

    dataframe = positions.copy()

    required_columns = {
        "Ticker",
        "Current Price",
        "Market Value",
    }

    missing_columns = required_columns.difference(
        dataframe.columns
    )

    if missing_columns:
        raise ValueError(
            "Positions are missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    dataframe["Current Price"] = pd.to_numeric(
        dataframe["Current Price"],
        errors="coerce",
    ).fillna(0.0)

    dataframe["Market Value"] = pd.to_numeric(
        dataframe["Market Value"],
        errors="coerce",
    ).fillna(0.0)

    position_count = len(dataframe)

    target_invested_percentage = max(
        0.0,
        100.0 - target_cash_percentage,
    )

    equal_weight_target = (
        target_invested_percentage / position_count
        if position_count > 0
        else 0.0
    )

    target_position_percentage = min(
        equal_weight_target,
        maximum_position_percentage,
    )

    target_position_value = (
        account_value
        * target_position_percentage
        / 100
    )

    rows: list[dict[str, Any]] = []

    total_buy_value = 0.0
    total_sell_value = 0.0

    for _, row in dataframe.iterrows():
        ticker = str(row.get("Ticker", "UNKNOWN"))
        current_price = _safe_float(
            row.get("Current Price", 0.0)
        )
        current_value = _safe_float(
            row.get("Market Value", 0.0)
        )

        current_allocation = (
            current_value / account_value * 100
            if account_value > 0
            else 0.0
        )

        allocation_gap = (
            target_position_percentage
            - current_allocation
        )

        suggested_value_change = (
            target_position_value
            - current_value
        )

        if current_price > 0:
            suggested_quantity_change = (
                suggested_value_change
                / current_price
            )
        else:
            suggested_quantity_change = 0.0

        if current_allocation > maximum_position_percentage:
            action = "REVIEW"
            rationale = (
                f"Allocation exceeds the "
                f"{maximum_position_percentage:.1f}% profile limit."
            )
        elif allocation_gap >= rebalance_threshold_percentage:
            action = "BUY"
            rationale = (
                f"Allocation is {allocation_gap:.1f} percentage points "
                f"below target."
            )
            total_buy_value += max(
                suggested_value_change,
                0.0,
            )
        elif allocation_gap <= -rebalance_threshold_percentage:
            action = "SELL"
            rationale = (
                f"Allocation is {abs(allocation_gap):.1f} percentage points "
                f"above target."
            )
            total_sell_value += abs(
                min(suggested_value_change, 0.0)
            )
        else:
            action = "HOLD"
            rationale = (
                "Allocation is within the configured "
                "rebalancing threshold."
            )

        rows.append(
            {
                "Ticker": ticker,
                "Action": action,
                "Current Allocation %": current_allocation,
                "Target Allocation %": target_position_percentage,
                "Allocation Gap %": allocation_gap,
                "Current Value": current_value,
                "Target Value": target_position_value,
                "Suggested Value Change": suggested_value_change,
                "Suggested Quantity Change": suggested_quantity_change,
                "Rationale": rationale,
            }
        )

    current_cash_percentage = (
        cash / account_value * 100
        if account_value > 0
        else 0.0
    )

    target_cash_value = (
        account_value
        * target_cash_percentage
        / 100
    )

    cash_gap_value = target_cash_value - cash

    messages: list[str] = []

    if cash_gap_value > 0:
        messages.append(
            f"Raise approximately £{cash_gap_value:,.2f} to reach "
            f"the {target_cash_percentage:.1f}% cash target."
        )
    elif cash_gap_value < 0:
        messages.append(
            f"Approximately £{abs(cash_gap_value):,.2f} is available "
            f"above the profile cash target."
        )
    else:
        messages.append(
            "Current cash is aligned with the profile target."
        )

    if position_count * target_position_percentage < target_invested_percentage:
        messages.append(
            "The maximum-position cap prevents full equal-weight deployment. "
            "Additional positions may be required for broader diversification."
        )

    action_series = pd.Series(
        [row["Action"] for row in rows]
    )

    summary = {
        "buy_value": total_buy_value,
        "sell_value": total_sell_value,
        "hold_count": int((action_series == "HOLD").sum()),
        "buy_count": int((action_series == "BUY").sum()),
        "sell_count": int((action_series == "SELL").sum()),
        "review_count": int((action_series == "REVIEW").sum()),
    }

    return {
        "risk_profile": risk_profile,
        "target_cash_percentage": target_cash_percentage,
        "target_cash_value": target_cash_value,
        "current_cash_percentage": current_cash_percentage,
        "maximum_position_percentage": maximum_position_percentage,
        "rebalance_threshold_percentage": rebalance_threshold_percentage,
        "target_position_percentage": target_position_percentage,
        "rows": rows,
        "summary": summary,
        "messages": messages,
    }