import yfinance as yf


def get_market_data(ticker):
    data = yf.download(
        ticker,
        period="6mo",
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    return data