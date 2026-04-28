import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import ProcessData as pd_process
import marketdata as md
import sqlite3

conn1 = pd_process.connect_clover()
data = pd_process.TickData_generate(conn1, "GLW")

# 1. Convert TickData_generate output to DataFrame
df = pd.DataFrame(data['values'])
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df.set_index('Timestamp', inplace=True)

# 2. Calculate MACD (12, 26, 9)
# EMA 12 and EMA 26
df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()

df['MACD'] = df['EMA12'] - df['EMA26']
df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

df['Histogram'] = df['MACD'] - df['Signal']

# 3. Plotting
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [1, 2]}, sharex=True)

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

ax1.set_title('IBIT 5-Minute Candlestick Chart with MACD (April 16 - April 22, 2026)', fontsize=14, color='#e8e8e8', pad=15)
ax1.set_ylabel('Price (USD)', fontsize=12, color='#e8e8e8')
ax1.tick_params(colors='#e8e8e8')
ax1.grid(True, linestyle='--', alpha=0.2, color='#4a4a4a')

# Plot MACD
ax2.plot(df['x'], df['MACD'], label='MACD Line (12, 26)', color='#2196f3', linewidth=1.5)
ax2.plot(df['x'], df['Signal'], label='Signal Line (9)', color='#ffa500', linewidth=1.5)

# Histogram colors (Binance style)
colors = ['#0ecb81' if val >= 0 else '#f6465d' for val in df['Histogram']]
ax2.bar(df['x'], df['Histogram'], width=width, color=colors, alpha=0.5)

ax2.set_ylabel('MACD', fontsize=12, color='#e8e8e8')
ax2.set_xlabel('Date & Time', fontsize=12, color='#e8e8e8')
ax2.tick_params(colors='#e8e8e8')
ax2.grid(True, linestyle='--', alpha=0.2, color='#4a4a4a')

# Create legend with dark background
legend = ax2.legend(loc='upper left', fancybox=True, shadow=False)
legend.get_frame().set_facecolor('#1a1a1a')
legend.get_frame().set_edgecolor('#4a4a4a')
for text in legend.get_texts():
    text.set_color('#e8e8e8')

# Label x-axis with timestamps at regular intervals
tick_interval = max(1, len(df) // 10)
xticks = df['x'][::tick_interval]
xtick_labels = df.index.strftime('%m-%d %H:%M')[::tick_interval]
ax2.set_xticks(xticks)
ax2.set_xticklabels(xtick_labels, rotation=45, ha='right', color='#e8e8e8')

plt.tight_layout()

# Save and show
plt.savefig('ibit_macd_candlestick.png')
plt.show()