import json
import logging
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import mplfinance as mpf
import mplcursors
from zoneinfo import ZoneInfo

# inherit logging configuration from main.py
logger = logging.getLogger(__name__)

def candlestick_chart(data: Dict[str, Any]) -> None:
    # Extract meta data
    symbol = data['meta']['symbol']
    interval = data['meta']['interval']


    # 1. Convert TickData_generate output to DataFrame
    df = pd.DataFrame(data['values'])
    
    # If the interval is daily, we can treat timestamps as naive datetime objects. 
    # For intraday data, we need to handle timezones properly.
    if interval == '1d':
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        timezone = data['meta'].get('timezone') or 'UTC'
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC').dt.tz_convert(ZoneInfo(timezone))

    df.set_index('timestamp', inplace=True)

    # 2. Calculate MACD (12, 26, 9)
    # EMA 12 and EMA 26
    df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()

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
    up = df[df.close >= df.open]
    down = df[df.close < df.open]

    # Up candles (Binance bright green)
    ax1.bar(up['x'], up.close - up.open, width, bottom=up.open, color='#0ecb81', edgecolor='#0ecb81')
    ax1.bar(up['x'], up.high - up.close, width2, bottom=up.close, color='#0ecb81')
    ax1.bar(up['x'], up.low - up.open, width2, bottom=up.open, color='#0ecb81')

    # Down candles (Binance bright red)
    ax1.bar(down['x'], down.close - down.open, width, bottom=down.open, color='#f6465d', edgecolor='#f6465d')
    ax1.bar(down['x'], down.high - down.open, width2, bottom=down.open, color='#f6465d')
    ax1.bar(down['x'], down.low - down.close, width2, bottom=down.close, color='#f6465d')

    # Add hoverable points for tooltip annotations
    hover_points = ax1.scatter(df['x'], df['close'], s=100, alpha=0.0, picker=True)
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
                                         f"O: {row['open']:.2f}\n"
                                         f"H: {row['high']:.2f}\n"
                                         f"L: {row['low']:.2f}\n"
                                         f"C: {row['close']:.2f}\n"
                                         f"V: {int(row['volume']):,}"))
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

    # Plot MACD lines on histogram chart
    ax2_twin = ax2.twinx()
    ax2_twin.plot(df['x'], df['MACD'], label='MACD Line (12, 26)', color='#2196f3', linewidth=1.5)
    ax2_twin.plot(df['x'], df['Signal'], label='Signal Line (9)', color='#ffa500', linewidth=1.5)
    ax2_twin.set_ylabel('MACD', fontsize=12, color='#e8e8e8')
    ax2_twin.tick_params(colors='#e8e8e8')

    ax2.set_ylabel('MACD Histogram', fontsize=12, color='#e8e8e8')
    ax2.set_xlabel('Date' if interval == "1d" else 'Date & Time', fontsize=12, color='#e8e8e8')
    ax2.tick_params(colors='#e8e8e8')
    ax2.grid(True, linestyle='--', alpha=0.2, color='#4a4a4a')

    # Create legend for MACD lines on ax2_twin
    legend = ax2_twin.legend(loc='upper left', fancybox=True, shadow=False)
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

def marketclose_chart(data: Dict[str, Any]) -> None:
    # Extract datetime and close values from the API response
    datetimes = [item["date"] if "date" in item else item["datetime"] for item in data["values"]]
    closes = [float(item["close"]) for item in data["values"]]

    # Convert datetime strings to pandas datetime objects
    datetimes = pd.to_datetime(datetimes)

    # Now plot with proper date handling
    plt.figure(figsize=(12, 6))
    df = pd.DataFrame({'close': closes}, index=datetimes)
    plt.plot(df.index, df['close'], linewidth=2, label='Close Price')
    for m in (3, 6, 9):
        ma = df['close'].rolling(window=m).mean()
        plt.plot(df.index, ma, label=f'{m}-period MA', linestyle='--')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.xlabel('Date')
    plt.ylabel('Close Price')
    plt.title('Stock Price Over Time')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def daily_chart(data: Dict[str, Any]) -> None:
    # Extract datetime, open, high, low, close values from the API response
    datetimes = [item["date"] if "date" in item else item["datetime"] for item in data["values"]]
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
