from indicators import add_indicators
from market import get_market_data
from strategy import generate_signal


def scan_market(tickers):
    results = []

    for ticker in tickers:
        try:
            data = get_market_data(ticker)

            if data.empty:
                continue

            data = add_indicators(data)
            signal, reason = generate_signal(data)

            latest_price = float(data["Close"].iloc[-1].item())
            short_average = float(
                data["short_average"].iloc[-1].item()
            )
            long_average = float(
                data["long_average"].iloc[-1].item()
            )
            rsi = float(data["rsi"].iloc[-1].item())

            results.append(
                {
                    "Ticker": ticker,
                    "Price": round(latest_price, 2),
                    "10-Day Average": round(short_average, 2),
                    "30-Day Average": round(long_average, 2),
                    "RSI": round(rsi, 2),
                    "Signal": signal,
                }
            )

        except Exception as error:
            print(f"Could not analyse {ticker}: {error}")

    return results