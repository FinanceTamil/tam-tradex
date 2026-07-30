def add_indicators(data):
    # Moving averages
    data["short_average"] = data["Close"].rolling(window=10).mean()
    data["long_average"] = data["Close"].rolling(window=30).mean()

    # Price change from the previous day
    price_change = data["Close"].diff()

    # Separate positive and negative price changes
    gain = price_change.clip(lower=0)
    loss = -price_change.clip(upper=0)

    # Calculate average gain and average loss
    average_gain = gain.rolling(window=14).mean()
    average_loss = loss.rolling(window=14).mean()

    # Calculate RSI
    relative_strength = average_gain / average_loss
    data["rsi"] = 100 - (100 / (1 + relative_strength))

    return data