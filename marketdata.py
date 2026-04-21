# marketdata.py contains the functions to pull market data from various sources and to process that data for use in the application
#   (1) Twelve Data and 
#   (2) Yahoo Finance 
# Features currently supported: 
#   - pulldata: Retrieve data from Twelve Data
#   - pulldata_yahoo: Retrieve data from Yahoo Finance

import json
import logging
import numpy as np
import requests
import yfinance as yf

debug = True
#debug = False

def pulldata_twelvedata(symbol, interval, startdate, enddate):
    try:
        response = requests.get("https://api.twelvedata.com/time_series?apikey=de4c2942b4284c4eb01e6097c0f9919e"+
                                "&symbol="+symbol+
                                "&interval="+interval+
                                "&start_date="+startdate+
                                "&end_date="+enddate+
                                "&format=JSON")
        if debug:
            print(f"Fetching data for {symbol}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
    return response.json()

def pulldata_yahoo(symbol, interval, startdate, enddate):
    try:
        data = yf.download(symbol, start=startdate, end=enddate, interval=interval, multi_level_index=False)

        output = {"meta":{ "symbol": symbol, "interval": interval, "start_date": startdate, "end_date": enddate}}
        
        values = []
        for index, row in data.iterrows():
            values.append({
                "datetime": index.strftime('%Y-%m-%d' if interval.endswith('d') else '%Y-%m-%d %H:%M:%S'),
                "open": str(row['Open']),
                "high": str(row['High']),
                "low": str(row['Low']),
                "close": str(row['Close']),
                "volume": str(row['Volume'])
            })
        output["values"] = values
        return output
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
