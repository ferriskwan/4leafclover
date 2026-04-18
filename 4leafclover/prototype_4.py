import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import requests

def generate_series(symbol, interval, startdate, enddate):
    try:
        response = requests.get("https://api.twelvedata.com/time_series?apikey=de4c2942b4284c4eb01e6097c0f9919e"+
                                "&symbol="+symbol+
                                "&interval="+interval+
                                "&start_date="+startdate+
                                "&end_date="+enddate+
                                "&format=JSON")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
    return response.json()
    # glw_closes = [float(d['close']) for d in data_glw['values'][::-1]]
    # glw = (np.array(glw_closes) / glw_closes[0]) * 100

#data = json.loads(generate_series("GLW", "1day", "2025-04-15", "2026-04-16"))
data = generate_series("GLW", "1day", "2025-04-15", "2026-04-16")

# for index in data["values"]:
#     print(index["datetime"], " ", index["close"])

# Extract datetime and close values from the API response
datetimes = [item["datetime"] for item in data["values"]]
closes = [float(item["close"]) for item in data["values"]]

# Convert datetime strings to pandas datetime objects
datetimes = pd.to_datetime(datetimes)

# Now plot with proper date handling
plt.figure(figsize=(12, 6))
plt.plot(datetimes, closes, linewidth=2)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.title('Stock Price Over Time')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


