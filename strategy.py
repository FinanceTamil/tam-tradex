def generate_signal(data):
    latest_short_average = float(
        data["short_average"].iloc[-1].item()
    )

    latest_long_average = float(
        data["long_average"].iloc[-1].item()
    )

    latest_rsi = float(
        data["rsi"].iloc[-1].item()
    )

    if (
        latest_short_average > latest_long_average
        and latest_rsi < 70
    ):
        signal = "BUY"
        reason = "The short average is above the long average, and RSI is below 70."

    elif (
        latest_short_average < latest_long_average
        and latest_rsi > 30
    ):
        signal = "SELL"
        reason = "The short average is below the long average, and RSI is above 30."

    else:
        signal = "HOLD"
        reason = "The indicators do not provide a clear trading signal."

    return signal, reason