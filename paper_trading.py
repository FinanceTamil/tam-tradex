import json
import os
from datetime import datetime
from typing import Any


PORTFOLIO_FILE = "paper_portfolio.json"
STARTING_CASH = 10_000.00


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _default_portfolio() -> dict[str, Any]:
    return {
        "cash": STARTING_CASH,
        "positions": {},
        "trade_history": [],
        "closed_trades": [],
        "realised_pnl": 0.0,
    }


def load_portfolio() -> dict[str, Any]:
    if not os.path.exists(PORTFOLIO_FILE):
        portfolio = _default_portfolio()
        save_portfolio(portfolio)
        return portfolio

    try:
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as file:
            portfolio = json.load(file)

        portfolio.setdefault("cash", STARTING_CASH)
        portfolio.setdefault("positions", {})
        portfolio.setdefault("trade_history", [])
        portfolio.setdefault("closed_trades", [])
        portfolio.setdefault("realised_pnl", 0.0)

        for position in portfolio["positions"].values():
            position.setdefault("opened_at", None)
            position.setdefault("entry_signal", "UNKNOWN")
            position.setdefault(
                "entry_ai_recommendation",
                "UNKNOWN",
            )
            position.setdefault(
                "entry_risk_profile",
                "Balanced",
            )
            position.setdefault("entry_stop_loss", None)
            position.setdefault("entry_take_profit", None)
            position.setdefault("entry_notes", "")

        return portfolio

    except (json.JSONDecodeError, OSError):
        portfolio = _default_portfolio()
        save_portfolio(portfolio)
        return portfolio


def save_portfolio(portfolio: dict[str, Any]) -> None:
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as file:
        json.dump(
            portfolio,
            file,
            indent=4,
        )


def buy_asset(
    ticker: str,
    quantity: float,
    price: float,
    *,
    strategy_signal: str = "UNKNOWN",
    strategy_reason: str = "",
    ai_recommendation: str = "UNKNOWN",
    risk_profile: str = "Balanced",
    stop_loss: float | None = None,
    take_profit: float | None = None,
    notes: str = "",
) -> tuple[bool, str]:

    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    if price <= 0:
        return False, "Price must be greater than zero."

    portfolio = load_portfolio()

    total_cost = quantity * price

    if total_cost > portfolio["cash"]:
        return False, "Insufficient paper-trading cash."

    timestamp = _now_iso()

    positions = portfolio["positions"]

    if ticker in positions:
        position = positions[ticker]

        existing_quantity = float(
            position["quantity"]
        )

        existing_average_price = float(
            position["average_price"]
        )

        combined_quantity = (
            existing_quantity
            + quantity
        )

        combined_cost = (
            existing_quantity
            * existing_average_price
        ) + total_cost

        position["quantity"] = combined_quantity

        position["average_price"] = (
            combined_cost
            / combined_quantity
        )

        position.setdefault(
            "opened_at",
            timestamp,
        )

        position.setdefault(
            "entry_signal",
            strategy_signal,
        )

        position.setdefault(
            "entry_ai_recommendation",
            ai_recommendation,
        )

        position.setdefault(
            "entry_risk_profile",
            risk_profile,
        )

        position.setdefault(
            "entry_stop_loss",
            stop_loss,
        )

        position.setdefault(
            "entry_take_profit",
            take_profit,
        )

        position.setdefault(
            "entry_notes",
            notes,
        )

    else:
        positions[ticker] = {
            "quantity": quantity,
            "average_price": price,
            "opened_at": timestamp,
            "entry_signal": strategy_signal,
            "entry_ai_recommendation": ai_recommendation,
            "entry_risk_profile": risk_profile,
            "entry_stop_loss": stop_loss,
            "entry_take_profit": take_profit,
            "entry_notes": notes,
        }

    portfolio["cash"] -= total_cost

    portfolio["trade_history"].append(
        {
            "timestamp": timestamp,
            "ticker": ticker,
            "action": "BUY",
            "quantity": quantity,
            "price": price,
            "value": total_cost,
            "realised_pnl": 0.0,
            "strategy_signal": strategy_signal,
            "strategy_reason": strategy_reason,
            "ai_recommendation": ai_recommendation,
            "risk_profile": risk_profile,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "notes": notes,
        }
    )

    save_portfolio(portfolio)

    return (
        True,
        f"Bought {quantity:g} units of "
        f"{ticker} at £{price:,.2f}.",
    )


def sell_asset(
    ticker: str,
    quantity: float,
    price: float,
    *,
    strategy_signal: str = "UNKNOWN",
    strategy_reason: str = "",
    ai_recommendation: str = "UNKNOWN",
    risk_profile: str = "Balanced",
    stop_loss: float | None = None,
    take_profit: float | None = None,
    notes: str = "",
) -> tuple[bool, str]:

    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    if price <= 0:
        return False, "Price must be greater than zero."

    portfolio = load_portfolio()

    positions = portfolio["positions"]

    if ticker not in positions:
        return (
            False,
            f"No open {ticker} position was found.",
        )

    position = positions[ticker]

    owned_quantity = float(
        position["quantity"]
    )

    if quantity > owned_quantity:
        return (
            False,
            f"You only own {owned_quantity:g} "
            f"units of {ticker}.",
        )

    average_price = float(
        position["average_price"]
    )

    sale_value = quantity * price

    realised_pnl = (
        price - average_price
    ) * quantity

    realised_return_percentage = (
        (
            price - average_price
        )
        / average_price
        * 100
        if average_price > 0
        else 0.0
    )

    exit_timestamp = _now_iso()

    entry_timestamp = position.get(
        "opened_at"
    )

    holding_days = None

    if entry_timestamp:
        try:
            entry_dt = datetime.fromisoformat(
                entry_timestamp
            )

            exit_dt = datetime.fromisoformat(
                exit_timestamp
            )

            holding_days = max(
                (
                    exit_dt - entry_dt
                ).total_seconds()
                / 86400,
                0.0,
            )

        except (TypeError, ValueError):
            holding_days = None

    entry_signal = position.get(
        "entry_signal",
        "UNKNOWN",
    )

    entry_ai_recommendation = position.get(
        "entry_ai_recommendation",
        "UNKNOWN",
    )

    entry_risk_profile = position.get(
        "entry_risk_profile",
        risk_profile,
    )

    entry_stop_loss = position.get(
        "entry_stop_loss"
    )

    entry_take_profit = position.get(
        "entry_take_profit"
    )

    entry_notes = position.get(
        "entry_notes",
        "",
    )

    portfolio["cash"] += sale_value

    portfolio["realised_pnl"] += realised_pnl

    remaining_quantity = (
        owned_quantity
        - quantity
    )

    if remaining_quantity <= 1e-12:
        del positions[ticker]

    else:
        position["quantity"] = (
            remaining_quantity
        )

    portfolio["trade_history"].append(
        {
            "timestamp": exit_timestamp,
            "ticker": ticker,
            "action": "SELL",
            "quantity": quantity,
            "price": price,
            "value": sale_value,
            "realised_pnl": realised_pnl,
            "strategy_signal": strategy_signal,
            "strategy_reason": strategy_reason,
            "ai_recommendation": ai_recommendation,
            "risk_profile": risk_profile,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "notes": notes,
        }
    )

    portfolio["closed_trades"].append(
        {
            "entry_timestamp": entry_timestamp,
            "exit_timestamp": exit_timestamp,
            "ticker": ticker,
            "quantity": quantity,
            "entry_price": average_price,
            "exit_price": price,
            "cost_basis": (
                average_price
                * quantity
            ),
            "exit_value": sale_value,
            "realised_pnl": realised_pnl,
            "return_percentage": (
                realised_return_percentage
            ),
            "holding_days": holding_days,
            "outcome": (
                "WIN"
                if realised_pnl > 0
                else "LOSS"
                if realised_pnl < 0
                else "BREAKEVEN"
            ),
            "entry_signal": entry_signal,
            "exit_signal": strategy_signal,
            "entry_ai_recommendation": (
                entry_ai_recommendation
            ),
            "exit_ai_recommendation": (
                ai_recommendation
            ),
            "risk_profile": (
                entry_risk_profile
            ),
            "entry_stop_loss": (
                entry_stop_loss
            ),
            "entry_take_profit": (
                entry_take_profit
            ),
            "exit_stop_loss": stop_loss,
            "exit_take_profit": take_profit,
            "entry_notes": entry_notes,
            "exit_notes": notes,
        }
    )

    save_portfolio(portfolio)

    return (
        True,
        f"Sold {quantity:g} units of "
        f"{ticker} at £{price:,.2f}. "
        f"Realised P/L: £{realised_pnl:,.2f}.",
    )


def reset_portfolio() -> None:
    save_portfolio(
        _default_portfolio()
    )


def calculate_position_metrics(
    ticker: str,
    current_price: float,
) -> dict[str, float] | None:

    portfolio = load_portfolio()

    position = portfolio[
        "positions"
    ].get(ticker)

    if not position:
        return None

    quantity = float(
        position["quantity"]
    )

    average_price = float(
        position["average_price"]
    )

    market_value = (
        quantity
        * current_price
    )

    cost_basis = (
        quantity
        * average_price
    )

    unrealised_pnl = (
        market_value
        - cost_basis
    )

    return_percentage = (
        unrealised_pnl
        / cost_basis
        * 100
        if cost_basis > 0
        else 0.0
    )

    return {
        "quantity": quantity,
        "average_price": average_price,
        "current_price": current_price,
        "market_value": market_value,
        "cost_basis": cost_basis,
        "unrealised_pnl": unrealised_pnl,
        "return_percentage": return_percentage,
    }