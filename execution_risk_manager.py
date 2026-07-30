from __future__ import annotations

from dataclasses import dataclass
from typing import Any


RISK_PROFILES = {
    "Conservative": {
        "risk_per_trade_pct": 0.5,
        "max_position_pct": 10.0,
        "max_total_exposure_pct": 60.0,
        "minimum_risk_reward": 2.0,
        "daily_loss_limit_pct": 1.5,
    },
    "Balanced": {
        "risk_per_trade_pct": 1.0,
        "max_position_pct": 20.0,
        "max_total_exposure_pct": 80.0,
        "minimum_risk_reward": 1.5,
        "daily_loss_limit_pct": 2.5,
    },
    "Aggressive": {
        "risk_per_trade_pct": 2.0,
        "max_position_pct": 30.0,
        "max_total_exposure_pct": 95.0,
        "minimum_risk_reward": 1.25,
        "daily_loss_limit_pct": 4.0,
    },
}


def _safe_float(value: Any) -> float:
    try:
        if hasattr(value, "item"):
            return float(value.item())
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def calculate_daily_realised_pnl(
    trade_history: list[dict[str, Any]],
    *,
    current_date_prefix: str,
) -> float:
    """
    Sum realised P/L for SELL orders recorded on the current date.
    """

    total = 0.0

    for trade in trade_history or []:
        timestamp = str(trade.get("timestamp", ""))

        if (
            timestamp.startswith(current_date_prefix)
            and str(trade.get("action", "")).upper() == "SELL"
        ):
            total += _safe_float(
                trade.get("realised_pnl", 0.0)
            )

    return total


def evaluate_buy_order(
    *,
    ticker: str,
    quantity: float,
    entry_price: float,
    stop_loss: float | None,
    take_profit: float | None,
    account_value: float,
    available_cash: float,
    current_total_market_value: float,
    current_position_value: float,
    daily_realised_pnl: float,
    risk_profile: str,
) -> dict[str, Any]:
    """
    Evaluate a proposed BUY order against a rule-based risk framework.

    The manager checks:
    - quantity and cash sufficiency,
    - stop-loss and take-profit validity,
    - capital at risk,
    - risk per trade,
    - position concentration,
    - total portfolio exposure,
    - daily loss limit,
    - risk/reward ratio.
    """

    profile = RISK_PROFILES.get(
        risk_profile,
        RISK_PROFILES["Balanced"],
    )

    ticker = str(ticker).strip().upper()
    quantity = max(_safe_float(quantity), 0.0)
    entry_price = _safe_float(entry_price)
    account_value = max(_safe_float(account_value), 0.0)
    available_cash = max(_safe_float(available_cash), 0.0)
    current_total_market_value = max(
        _safe_float(current_total_market_value),
        0.0,
    )
    current_position_value = max(
        _safe_float(current_position_value),
        0.0,
    )
    daily_realised_pnl = _safe_float(
        daily_realised_pnl
    )

    stop_loss_value = (
        _safe_float(stop_loss)
        if stop_loss is not None
        else 0.0
    )

    take_profit_value = (
        _safe_float(take_profit)
        if take_profit is not None
        else 0.0
    )

    order_value = quantity * entry_price
    projected_position_value = (
        current_position_value + order_value
    )
    projected_total_market_value = (
        current_total_market_value + order_value
    )

    projected_cash = available_cash - order_value

    stop_distance = (
        entry_price - stop_loss_value
        if stop_loss_value > 0
        else 0.0
    )

    reward_distance = (
        take_profit_value - entry_price
        if take_profit_value > 0
        else 0.0
    )

    capital_at_risk = (
        stop_distance * quantity
        if stop_distance > 0
        else 0.0
    )

    risk_per_trade_pct = (
        capital_at_risk / account_value * 100
        if account_value > 0
        else 0.0
    )

    position_exposure_pct = (
        projected_position_value
        / account_value
        * 100
        if account_value > 0
        else 0.0
    )

    total_exposure_pct = (
        projected_total_market_value
        / account_value
        * 100
        if account_value > 0
        else 0.0
    )

    risk_reward_ratio = (
        reward_distance / stop_distance
        if stop_distance > 0
        else 0.0
    )

    daily_loss_pct = (
        abs(min(daily_realised_pnl, 0.0))
        / account_value
        * 100
        if account_value > 0
        else 0.0
    )

    allowed_risk_value = (
        account_value
        * profile["risk_per_trade_pct"]
        / 100
    )

    risk_based_quantity = (
        allowed_risk_value / stop_distance
        if stop_distance > 0
        else 0.0
    )

    max_position_value = (
        account_value
        * profile["max_position_pct"]
        / 100
    )

    concentration_quantity = (
        max(
            max_position_value
            - current_position_value,
            0.0,
        )
        / entry_price
        if entry_price > 0
        else 0.0
    )

    cash_quantity = (
        available_cash / entry_price
        if entry_price > 0
        else 0.0
    )

    exposure_room_value = max(
        (
            account_value
            * profile["max_total_exposure_pct"]
            / 100
        )
        - current_total_market_value,
        0.0,
    )

    exposure_quantity = (
        exposure_room_value / entry_price
        if entry_price > 0
        else 0.0
    )

    suggested_max_quantity = min(
        risk_based_quantity
        if risk_based_quantity > 0
        else float("inf"),
        concentration_quantity
        if concentration_quantity > 0
        else float("inf"),
        cash_quantity
        if cash_quantity > 0
        else float("inf"),
        exposure_quantity
        if exposure_quantity > 0
        else float("inf"),
    )

    if suggested_max_quantity == float("inf"):
        suggested_max_quantity = 0.0

    checks: list[dict[str, Any]] = []

    def add_check(
        name: str,
        passed: bool,
        message: str,
        severity: str = "block",
    ) -> None:
        checks.append(
            {
                "name": name,
                "passed": bool(passed),
                "message": message,
                "severity": severity,
            }
        )

    add_check(
        "Valid quantity",
        quantity > 0,
        (
            "Quantity is valid."
            if quantity > 0
            else "Quantity must be greater than zero."
        ),
    )

    add_check(
        "Valid entry price",
        entry_price > 0,
        (
            "Entry price is valid."
            if entry_price > 0
            else "Entry price must be greater than zero."
        ),
    )

    add_check(
        "Cash sufficiency",
        order_value <= available_cash,
        (
            f"Order value £{order_value:,.2f} is within available cash."
            if order_value <= available_cash
            else (
                f"Order value £{order_value:,.2f} exceeds "
                f"available cash of £{available_cash:,.2f}."
            )
        ),
    )

    add_check(
        "Stop-loss validity",
        (
            stop_loss_value > 0
            and stop_loss_value < entry_price
        ),
        (
            f"Stop loss is set at £{stop_loss_value:,.2f}."
            if (
                stop_loss_value > 0
                and stop_loss_value < entry_price
            )
            else (
                "A BUY order requires a stop loss below "
                "the entry price."
            )
        ),
    )

    add_check(
        "Take-profit validity",
        (
            take_profit_value > entry_price
        ),
        (
            f"Take profit is set at £{take_profit_value:,.2f}."
            if take_profit_value > entry_price
            else (
                "A BUY order requires a take profit above "
                "the entry price."
            )
        ),
    )

    add_check(
        "Risk per trade",
        (
            risk_per_trade_pct
            <= profile["risk_per_trade_pct"]
        ),
        (
            f"Trade risk is {risk_per_trade_pct:.2f}% "
            f"against a {profile['risk_per_trade_pct']:.2f}% limit."
        ),
    )

    add_check(
        "Risk/reward",
        (
            risk_reward_ratio
            >= profile["minimum_risk_reward"]
        ),
        (
            f"Risk/reward is {risk_reward_ratio:.2f}:1 "
            f"against a {profile['minimum_risk_reward']:.2f}:1 minimum."
        ),
    )

    add_check(
        "Position concentration",
        (
            position_exposure_pct
            <= profile["max_position_pct"]
        ),
        (
            f"Projected {ticker} exposure is "
            f"{position_exposure_pct:.2f}% against a "
            f"{profile['max_position_pct']:.2f}% limit."
        ),
    )

    add_check(
        "Total exposure",
        (
            total_exposure_pct
            <= profile["max_total_exposure_pct"]
        ),
        (
            f"Projected total exposure is "
            f"{total_exposure_pct:.2f}% against a "
            f"{profile['max_total_exposure_pct']:.2f}% limit."
        ),
    )

    add_check(
        "Daily loss limit",
        (
            daily_loss_pct
            < profile["daily_loss_limit_pct"]
        ),
        (
            f"Today's realised loss is {daily_loss_pct:.2f}% "
            f"against a {profile['daily_loss_limit_pct']:.2f}% limit."
        ),
    )

    blocking_failures = [
        check
        for check in checks
        if (
            check["severity"] == "block"
            and not check["passed"]
        )
    ]

    approved = len(blocking_failures) == 0

    decision = (
        "APPROVED"
        if approved
        else "BLOCKED"
    )

    return {
        "ticker": ticker,
        "decision": decision,
        "approved": approved,
        "risk_profile": risk_profile,
        "order_value": order_value,
        "projected_cash": projected_cash,
        "capital_at_risk": capital_at_risk,
        "risk_per_trade_pct": risk_per_trade_pct,
        "risk_reward_ratio": risk_reward_ratio,
        "position_exposure_pct": position_exposure_pct,
        "total_exposure_pct": total_exposure_pct,
        "daily_loss_pct": daily_loss_pct,
        "suggested_max_quantity": max(
            suggested_max_quantity,
            0.0,
        ),
        "stop_loss": stop_loss_value,
        "take_profit": take_profit_value,
        "checks": checks,
        "blocking_failures": blocking_failures,
        "profile_limits": profile,
    }