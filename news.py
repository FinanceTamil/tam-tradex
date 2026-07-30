from datetime import date, timedelta

import requests
import streamlit as st


def get_company_news(symbol, days=14, limit=5):
    finnhub_api_key = st.secrets.get("FINNHUB_API_KEY", "")

    if not finnhub_api_key:
        raise ValueError(
            "FINNHUB_API_KEY is missing from .streamlit/secrets.toml"
        )

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    url = "https://finnhub.io/api/v1/company-news"

    parameters = {
        "symbol": symbol,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "token": finnhub_api_key,
    }

    response = requests.get(
        url,
        params=parameters,
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Finnhub returned HTTP {response.status_code}: "
            f"{response.text}"
        )

    articles = response.json()

    if not isinstance(articles, list):
        raise RuntimeError(
            f"Unexpected Finnhub response: {articles}"
        )

    valid_articles = [
        article
        for article in articles
        if article.get("headline") and article.get("url")
    ]

    return valid_articles[:limit]