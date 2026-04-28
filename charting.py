import json
import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import mplfinance as mpf
import mplcursors

# inherit logging configuration from main.py
logger = logging.getLogger(__name__)

def candlestick_chart(data):
    # 1. Convert TickData_generate output to DataFrame
    df = pd.DataFrame(data['values'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df.set_index('Timestamp', inplace=True)

    # Extract meta data
    symbol = data['meta']['Symbol']
    interval = data['meta']['Interval']

    # 2. Calculate MACD (12, 26, 9)
    # EMA 12 and EMA 26
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()

    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    df['Histogram'] = df['MACD'] - df['Signal']

    # 3. Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]}, sharex=True)

    # Set Binance-style dark theme
    fig.patch.set_facecolor('#0f0f0f')
    ax1.set_facecolor('#1a1a1a')
    ax2.set_facecolor('#1a1a1a')

    # Suppress non-trading gaps by plotting against integer x positions
    df = df.copy()
    df['x'] = np.arange(len(df))

    # Plot Candlesticks
    width = 0.6
    width2 = 0.1
    up = df[df.Close >= df.Open]
    down = df[df.Close < df.Open]

    # Up candles (Binance bright green)
    ax1.bar(up['x'], up.Close - up.Open, width, bottom=up.Open, color='#0ecb81', edgecolor='#0ecb81')
    ax1.bar(up['x'], up.High - up.Close, width2, bottom=up.Close, color='#0ecb81')
    ax1.bar(up['x'], up.Low - up.Open, width2, bottom=up.Open, color='#0ecb81')

    # Down candles (Binance bright red)
    ax1.bar(down['x'], down.Close - down.Open, width, bottom=down.Open, color='#f6465d', edgecolor='#f6465d')
    ax1.bar(down['x'], down.High - down.Open, width2, bottom=down.Open, color='#f6465d')
    ax1.bar(down['x'], down.Low - down.Close, width2, bottom=down.Close, color='#f6465d')

    # Plot MACD lines on price chart
    ax1_twin = ax1.twinx()
    ax1_twin.plot(df['x'], df['MACD'], label='MACD Line (12, 26)', color='#2196f3', linewidth=1.5)
    ax1_twin.plot(df['x'], df['Signal'], label='Signal Line (9)', color='#ffa500', linewidth=1.5)
    ax1_twin.set_ylabel('MACD', fontsize=12, color='#e8e8e8')
    ax1_twin.tick_params(colors='#e8e8e8')

    # Add hoverable points for tooltip annotations
    hover_points = ax1.scatter(df['x'], df['Close'], s=100, alpha=0.0, picker=True)
    date_format = '%d-%b-%Y' if interval == '1d' else '%d-%b %H:%M'
    
    cursor = mplcursors.cursor(hover_points, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        try:
            idx = int(round(sel.target[0]))
            if 0 <= idx < len(df):
                row = df.iloc[idx]
                dt = row.name.strftime(date_format)
                sel.annotation.set(text=(f"{dt}\n"
                                         f"O: {row['Open']:.2f}\n"
                                         f"H: {row['High']:.2f}\n"
                                         f"L: {row['Low']:.2f}\n"
                                         f"C: {row['Close']:.2f}\n"
                                         f"V: {int(row['Volume']):,}"))
                sel.annotation.get_bbox_patch().set(fc='#666666', alpha=0.95, edgecolor='#4a4a4a')
                sel.annotation.get_text().set_color('#ffffff')
        except Exception as e:
            logger.debug(f"Error in hover callback: {e}")

    ax1.set_title(f'{symbol} {interval} Candlestick Chart with MACD', fontsize=14, color='#e8e8e8', pad=15)
    ax1.set_ylabel('Price (USD)', fontsize=12, color='#e8e8e8')
    ax1.tick_params(colors='#e8e8e8')
    ax1.grid(True, linestyle='--', alpha=0.2, color='#4a4a4a')

    # Plot MACD Histogram
    colors = ['#0ecb81' if val >= 0 else '#f6465d' for val in df['Histogram']]
    ax2.bar(df['x'], df['Histogram'], width=width, color=colors, alpha=0.5)

    ax2.set_ylabel('MACD Histogram', fontsize=12, color='#e8e8e8')
    ax2.set_xlabel('Date' if interval == "1d" else 'Date & Time', fontsize=12, color='#e8e8e8')
    ax2.tick_params(colors='#e8e8e8')
    ax2.grid(True, linestyle='--', alpha=0.2, color='#4a4a4a')

    # Create legend for MACD lines on ax1_twin
    legend = ax1_twin.legend(loc='upper left', fancybox=True, shadow=False)
    legend.get_frame().set_facecolor('#1a1a1a')
    legend.get_frame().set_edgecolor('#4a4a4a')
    for text in legend.get_texts():
        text.set_color('#e8e8e8')

    # Label x-axis with timestamps at regular intervals
    tick_interval = max(1, len(df) // 10)
    xticks = df['x'][::tick_interval]
    if interval == "1d":
        date_format = '%d-%b-%Y'
    else:
        date_format = '%d-%b %H:%M'
    xtick_labels = df.index.strftime(date_format)[::tick_interval]
    ax2.set_xticks(xticks)
    ax2.set_xticklabels(xtick_labels, rotation=45, ha='right', color='#e8e8e8')

    plt.tight_layout()

    # Save and show
    plt.savefig(f'{symbol}_macd_candlestick.png')
    plt.show()

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
    datetimes = [item["Date"] for item in data["values"]]
    opens = [float(item["Open"]) for item in data["values"]]
    highs = [float(item["High"]) for item in data["values"]]
    lows = [float(item["Low"]) for item in data["values"]]
    closes = [float(item["Close"]) for item in data["values"]]
    volumes = [float(item["Volume"]) for item in data["values"]]
    
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
