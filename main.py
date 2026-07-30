from market import get_market_data
from indicators import add_indicators
from strategy import generate_signal
from ai_analysis import get_ai_analysis


ticker = "TSLA"

data = get_market_data(ticker)


if data.empty:
    print("No market data received.")
    raise SystemExit


data = add_indicators(data)

signal, reason = generate_signal(data)


latest_price = float(data["Close"].iloc[-1].item())

latest_short_average = float(
    data["short_average"].iloc[-1].item()
)

latest_long_average = float(
    data["long_average"].iloc[-1].item()
)

latest_rsi = float(
    data["rsi"].iloc[-1].item()
)


print("--------------------------------")
print("AI TRADING BOT - VERSION 5")
print("--------------------------------")
print("Stock:", ticker)
print("Price:", round(latest_price, 2))
print("10-day average:", round(latest_short_average, 2))
print("30-day average:", round(latest_long_average, 2))
print("RSI:", round(latest_rsi, 2))
print("Rule-based signal:", signal)
print("Rule-based reason:", reason)
print("--------------------------------")
print("Requesting AI analysis...")
print("--------------------------------")


ai_analysis = get_ai_analysis(
    ticker=ticker,
    latest_price=latest_price,
    short_average=latest_short_average,
    long_average=latest_long_average,
    rsi=latest_rsi,
    rule_signal=signal,
)


print(ai_analysis)
print("--------------------------------")