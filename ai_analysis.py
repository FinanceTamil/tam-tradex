from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq


load_dotenv()


def _get_groq_api_key() -> str:
    """
    Read the Groq key from Streamlit secrets first,
    then fall back to the local .env file.
    """

    try:
        streamlit_key = st.secrets.get(
            "GROQ_API_KEY",
            "",
        )

        if streamlit_key:
            return str(streamlit_key).strip()

    except Exception:
        pass

    return os.getenv(
        "GROQ_API_KEY",
        "",
    ).strip()


def get_ai_analysis(
    ticker,
    latest_price,
    short_average,
    long_average,
    rsi,
    rule_signal,
):
    api_key = _get_groq_api_key()

    if not api_key:
        return (
            "ERROR: GROQ_API_KEY was not found. "
            "Add it to .streamlit/secrets.toml or .env."
        )

    client = Groq(
        api_key=api_key
    )

    prompt = f"""
You are a cautious financial market analysis assistant.

Analyse this market data:

Stock: {ticker}
Latest price: {latest_price:.2f}
10-day moving average: {short_average:.2f}
30-day moving average: {long_average:.2f}
RSI: {rsi:.2f}
Rule-based signal: {rule_signal}

Return exactly this structure:

MARKET TREND:
MOMENTUM:
AI VIEW:
CONFIDENCE:
RISK:
EXPLANATION:

Requirements:
- AI VIEW must be BUY, SELL, or HOLD.
- Confidence must be between 0% and 100%.
- Explain any conflict between RSI and the moving averages.
- Do not claim certainty.
- Keep the response below 150 words.
- State that this is market analysis, not personalised financial advice.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content

        if not content:
            return "Groq returned an empty analysis."

        return content.strip()

    except Exception as error:
        return f"Groq API error: {error}"