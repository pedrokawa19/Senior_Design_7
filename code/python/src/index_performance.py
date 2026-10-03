import datetime as dt

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

ticker = "SLX"

start_date = "2024-01-01"
end_date = dt.datetime.now(dt.timezone.utc)

df = yf.download(
    ticker,
    start=start_date,
    end=end_date,
    auto_adjust=False,
)

df = df["Close"].squeeze().to_frame(name="Close").round(2)
df = df.reset_index()
df["Date"] = pd.to_datetime(df["Date"])

plt.figure(figsize=(10, 5))
plt.plot(df["Date"], df["Close"], label="Close Price")
plt.title(f"{ticker} Performance")
plt.xlabel("Date")
plt.ylabel("Close Price")
plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()
