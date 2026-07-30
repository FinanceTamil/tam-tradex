from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

WATCHLIST_FILE = Path("watchlist_data.json")

DEFAULT_WATCHLIST = [
    "AAPL",
    "TSLA",
    "NVDA",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "BTC-USD",
    "ETH-USD",
]


def _normalise_ticker(ticker: str) -> str:
    return str(ticker).strip().upper()


def load_watchlist() -> list[str]:
    if not WATCHLIST_FILE.exists():
        save_watchlist(DEFAULT_WATCHLIST)
        return DEFAULT_WATCHLIST.copy()

    try:
        data = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        save_watchlist(DEFAULT_WATCHLIST)
        return DEFAULT_WATCHLIST.copy()

    if not isinstance(data, list):
        save_watchlist(DEFAULT_WATCHLIST)
        return DEFAULT_WATCHLIST.copy()

    tickers = []
    for ticker in data:
        normalised = _normalise_ticker(ticker)
        if normalised and normalised not in tickers:
            tickers.append(normalised)

    return tickers


def save_watchlist(tickers: Iterable[str]) -> None:
    clean_tickers = []

    for ticker in tickers:
        normalised = _normalise_ticker(ticker)

        if normalised and normalised not in clean_tickers:
            clean_tickers.append(normalised)

    WATCHLIST_FILE.write_text(
        json.dumps(clean_tickers, indent=2),
        encoding="utf-8",
    )


def add_ticker(ticker: str) -> tuple[bool, str]:
    normalised = _normalise_ticker(ticker)

    if not normalised:
        return False, "Enter a valid ticker symbol."

    watchlist = load_watchlist()

    if normalised in watchlist:
        return False, f"{normalised} is already in the watchlist."

    watchlist.append(normalised)
    save_watchlist(watchlist)

    return True, f"{normalised} was added to the watchlist."


def remove_ticker(ticker: str) -> tuple[bool, str]:
    normalised = _normalise_ticker(ticker)
    watchlist = load_watchlist()

    if normalised not in watchlist:
        return False, f"{normalised} is not in the watchlist."

    watchlist.remove(normalised)
    save_watchlist(watchlist)

    return True, f"{normalised} was removed from the watchlist."


def reset_watchlist() -> list[str]:
    save_watchlist(DEFAULT_WATCHLIST)
    return DEFAULT_WATCHLIST.copy()