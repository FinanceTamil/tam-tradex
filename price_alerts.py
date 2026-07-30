from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ALERTS_FILE = Path("price_alerts.json")

SUPPORTED_CONDITIONS = {
    "Price Above",
    "Price Below",
    "RSI Above",
    "RSI Below",
    "Signal Equals",
}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _normalise_ticker(ticker: str) -> str:
    return str(ticker).strip().upper()


def _default_alerts() -> list[dict[str, Any]]:
    return []


def load_alerts() -> list[dict[str, Any]]:
    if not ALERTS_FILE.exists():
        save_alerts(_default_alerts())
        return []

    try:
        data = json.loads(
            ALERTS_FILE.read_text(
                encoding="utf-8"
            )
        )
    except (json.JSONDecodeError, OSError):
        save_alerts(_default_alerts())
        return []

    if not isinstance(data, list):
        save_alerts(_default_alerts())
        return []

    alerts: list[dict[str, Any]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        alert = {
            "id": str(
                item.get(
                    "id",
                    f"alert_{len(alerts) + 1}",
                )
            ),
            "ticker": _normalise_ticker(
                item.get("ticker", "")
            ),
            "condition": str(
                item.get("condition", "")
            ),
            "target": item.get("target"),
            "active": bool(
                item.get("active", True)
            ),
            "triggered": bool(
                item.get("triggered", False)
            ),
            "created_at": item.get(
                "created_at"
            ),
            "triggered_at": item.get(
                "triggered_at"
            ),
            "last_value": item.get(
                "last_value"
            ),
            "message": item.get(
                "message",
                "",
            ),
        }

        if (
            alert["ticker"]
            and alert["condition"]
            in SUPPORTED_CONDITIONS
        ):
            alerts.append(alert)

    return alerts


def save_alerts(
    alerts: list[dict[str, Any]],
) -> None:
    ALERTS_FILE.write_text(
        json.dumps(
            alerts,
            indent=2,
        ),
        encoding="utf-8",
    )


def create_alert(
    ticker: str,
    condition: str,
    target: float | str,
) -> tuple[bool, str]:
    ticker = _normalise_ticker(ticker)
    condition = str(condition).strip()

    if not ticker:
        return False, "Enter a valid ticker."

    if condition not in SUPPORTED_CONDITIONS:
        return False, "Unsupported alert condition."

    if condition == "Signal Equals":
        target = str(target).strip().upper()

        if target not in {
            "BUY",
            "HOLD",
            "SELL",
        }:
            return (
                False,
                "Signal target must be BUY, HOLD or SELL.",
            )

    else:
        try:
            target = float(target)
        except (TypeError, ValueError):
            return (
                False,
                "Enter a valid numerical target.",
            )

    alerts = load_alerts()

    alert_id = (
        f"{ticker}_"
        f"{int(datetime.now().timestamp() * 1000)}"
    )

    alerts.append(
        {
            "id": alert_id,
            "ticker": ticker,
            "condition": condition,
            "target": target,
            "active": True,
            "triggered": False,
            "created_at": _now_iso(),
            "triggered_at": None,
            "last_value": None,
            "message": "",
        }
    )

    save_alerts(alerts)

    return (
        True,
        f"Alert created for {ticker}.",
    )


def delete_alert(
    alert_id: str,
) -> tuple[bool, str]:
    alerts = load_alerts()

    filtered_alerts = [
        alert
        for alert in alerts
        if alert.get("id") != alert_id
    ]

    if len(filtered_alerts) == len(alerts):
        return False, "Alert was not found."

    save_alerts(filtered_alerts)

    return True, "Alert deleted."


def set_alert_active(
    alert_id: str,
    active: bool,
) -> tuple[bool, str]:
    alerts = load_alerts()

    for alert in alerts:
        if alert.get("id") == alert_id:
            alert["active"] = bool(active)

            if active:
                alert["triggered"] = False
                alert["triggered_at"] = None
                alert["message"] = ""

            save_alerts(alerts)

            return (
                True,
                "Alert status updated.",
            )

    return False, "Alert was not found."


def evaluate_alert(
    alert: dict[str, Any],
    *,
    price: float,
    rsi: float,
    signal: str,
) -> tuple[bool, str, Any]:
    condition = alert.get("condition")
    target = alert.get("target")

    if condition == "Price Above":
        current_value = float(price)
        triggered = current_value >= float(target)
        message = (
            f"{alert['ticker']} price "
            f"{current_value:.2f} is above "
            f"{float(target):.2f}."
        )

    elif condition == "Price Below":
        current_value = float(price)
        triggered = current_value <= float(target)
        message = (
            f"{alert['ticker']} price "
            f"{current_value:.2f} is below "
            f"{float(target):.2f}."
        )

    elif condition == "RSI Above":
        current_value = float(rsi)
        triggered = current_value >= float(target)
        message = (
            f"{alert['ticker']} RSI "
            f"{current_value:.1f} is above "
            f"{float(target):.1f}."
        )

    elif condition == "RSI Below":
        current_value = float(rsi)
        triggered = current_value <= float(target)
        message = (
            f"{alert['ticker']} RSI "
            f"{current_value:.1f} is below "
            f"{float(target):.1f}."
        )

    elif condition == "Signal Equals":
        current_value = str(signal).upper()
        triggered = (
            current_value
            == str(target).upper()
        )
        message = (
            f"{alert['ticker']} signal is "
            f"{current_value}."
        )

    else:
        return False, "Unsupported condition.", None

    return triggered, message, current_value


def check_alerts(
    market_snapshot: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Evaluate all active alerts using a ticker-keyed market snapshot.

    Expected snapshot structure:
    {
        "AAPL": {
            "price": 200.0,
            "rsi": 55.0,
            "signal": "BUY",
        }
    }
    """

    alerts = load_alerts()
    triggered_alerts: list[dict[str, Any]] = []
    changed = False

    for alert in alerts:
        if not alert.get("active", True):
            continue

        ticker = alert.get("ticker", "")
        snapshot = market_snapshot.get(ticker)

        if not snapshot:
            continue

        try:
            triggered, message, current_value = evaluate_alert(
                alert,
                price=float(
                    snapshot.get("price", 0.0)
                ),
                rsi=float(
                    snapshot.get("rsi", 0.0)
                ),
                signal=str(
                    snapshot.get("signal", "")
                ),
            )
        except (TypeError, ValueError):
            continue

        alert["last_value"] = current_value

        if triggered and not alert.get(
            "triggered",
            False,
        ):
            alert["triggered"] = True
            alert["triggered_at"] = _now_iso()
            alert["message"] = message
            triggered_alerts.append(alert.copy())
            changed = True

    if changed:
        save_alerts(alerts)
    else:
        # Save latest values even when no alert triggers.
        save_alerts(alerts)

    return triggered_alerts