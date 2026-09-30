"""Steel and broad-market index performance from Yahoo Finance.

This is public market data used for context only. It is not a price forecast
and not a bid recommendation.
"""

from datetime import date, timedelta

import pandas as pd
import yfinance as yf

# Keep the two supported fund names local to avoid another market-data request.
TICKER_NAMES = {
    "SLX": "VanEck Steel ETF",
    "SPY": "State Street SPDR S&P 500 ETF",
}
SUPPORTED_TICKERS = set(TICKER_NAMES)

# The internal network may not allow outbound traffic, so never wait forever.
DOWNLOAD_TIMEOUT_SECONDS = 15


def get_index_performance(start_date: date, end_date: date, ticker: str):
    ticker = ticker.upper()
    if ticker not in SUPPORTED_TICKERS:
        raise ValueError("Ticker must be SPY or SLX.")
    if start_date >= end_date:
        raise ValueError("The start date must be before the end date.")

    prices = yf.download(
        ticker,
        start=start_date.isoformat(),
        end=(end_date + timedelta(days=1)).isoformat(),
        auto_adjust=False,
        progress=False,
        timeout=DOWNLOAD_TIMEOUT_SECONDS,
    )
    if prices.empty or "Close" not in prices:
        raise ValueError(f"No {ticker} price data found for this date range.")

    close_prices = prices["Close"]
    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.iloc[:, 0]
    close_prices = close_prices.dropna().round(2)
    if close_prices.empty:
        raise ValueError(f"No {ticker} closing prices found for this date range.")

    first_close = float(close_prices.iloc[0])
    last_close = float(close_prices.iloc[-1])
    growth_percentage = (last_close - first_close) / first_close * 100 if first_close else 0

    return {
        "ticker": ticker,
        "name": TICKER_NAMES[ticker],
        "first_close": first_close,
        "last_close": last_close,
        "growth_percentage": round(growth_percentage, 2),
        "prices": [
            {"date": timestamp.strftime("%Y-%m-%d"), "close": float(close)}
            for timestamp, close in close_prices.items()
        ],
    }
