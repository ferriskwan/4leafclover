import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import mplfinance as mpf
import marketdata as md

def candlestick_chart(data):
    # Extract datetime, open, high, low, close values from the API response
    datetimes = [item["datetime"] for item in data["values"]]
    opens = [float(item["open"]) for item in data["values"]]
    highs = [float(item["high"]) for item in data["values"]]
    lows = [float(item["low"]) for item in data["values"]]
    closes = [float(item["close"]) for item in data["values"]]
    volume = [float(item["volume"]) for item in data["values"]]
    
    # Convert datetime strings to pandas datetime objects
    datetimes = pd.to_datetime(datetimes)

    # Create a DataFrame for mplfinance
    df = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volume
    }, index=datetimes)
    df = df.sort_index()  # Ensure the DataFrame is sorted by datetime

    # Plot candlestick chart using mplfinance
    # mpf.plot(df, type='candle', style='charles', title='Stock Price Over Time', ylabel='Price', volume=True)
    mpf.plot(df, type='candle', title='Candlestick:'+data["meta"]["symbol"], volume=True)

def marketclose_chart(data):
    # Extract datetime and close values from the API response
    datetimes = [item["datetime"] for item in data["values"]]
    closes = [float(item["close"]) for item in data["values"]]

    # Convert datetime strings to pandas datetime objects
    datetimes = pd.to_datetime(datetimes)

    # Now plot with proper date handling
    plt.figure(figsize=(12, 6))
    plt.plot(datetimes, closes, linewidth=2, mav=(3,6,9), label='Close Price')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.xlabel('Date')
    plt.ylabel('Close Price')
    plt.title('Stock Price Over Time')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def daily_chart(data):
    # Extract datetime, open, high, low, close values from the API response
    datetimes = [item["datetime"] for item in data["values"]]
    opens = [float(item["open"]) for item in data["values"]]
    highs = [float(item["high"]) for item in data["values"]]
    lows = [float(item["low"]) for item in data["values"]]
    closes = [float(item["close"]) for item in data["values"]]
    volumes = [float(item["volume"]) for item in data["values"]]
    
    # Convert datetime strings to pandas datetime objects
    datetimes = pd.to_datetime(datetimes)

    # Create a DataFrame for mplfinance
    df = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes
    }, index=datetimes)
    df = df.sort_index()  # Ensure the DataFrame is sorted by datetime
    mpf.plot(df, type='ohlc', volume=True, mav=(3,20,50))

def main():
#    data = pulldata("GLW", "1min", "2026-04-15", "2026-04-16")
#    print(json.dumps(data, indent=4))
#    candlestick_chart(data)
#    data = pulldata("GLW", "1day", "2025-04-15", "2026-04-16")
#    print(json.dumps(data, indent=4))
#    data1 = pulldata("GLW", "1day", "2026-04-15", "2026-04-17")
    data1 = md.pulldata_twelvedata("GLW", "5min", "2026-04-15", "2026-04-16")
    print(json.dumps(data1, indent=4))
    candlestick_chart(data1)
#    data2 = pulldata_yahoo("5E2.SI", "1d", "2025-04-15", "2026-04-17")
#    print(json.dumps(data2, indent=4))
#    daily_chart(data2)
#    data3 = pulldata_yahoo("5E2.SI", "5m", "2026-04-15", "2026-04-16")
    data3 = md.pulldata_yahoo("GLW", "5m", "2026-04-15", "2026-04-16")
    print(json.dumps(data3, indent=4))
    candlestick_chart(data3)

if __name__ == "__main__":
    main()


