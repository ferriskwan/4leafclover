# marketdata.py contains the functions to pull market data from various sources and to process that data for use in the application
#   (1) Twelve Data and 
#   (2) Yahoo Finance 
# Features currently supported: 
#   - pulldata: Retrieve data from Twelve Data
#   - pulldata_yahoo: Retrieve data from Yahoo Finance

import json
import logging
import os
from typing import Optional, Dict, Any
import numpy as np
import requests
import yfinance as yf
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# inherit logging configuration from main.py
logger = logging.getLogger(__name__)

# Load API key from environment
API_KEY = os.getenv('TWELVEDATA_API_KEY')
if not API_KEY:
    logger.warning("[marketdata.py]: TWELVEDATA_API_KEY environment variable not set")

def pulldata_twelvedata(symbol: str, interval: str, startdate: str, enddate: str) -> Optional[Dict[str, Any]]:
    """
    Fetch market data from Twelve Data API.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        interval: Time interval (e.g., '1day', '5min')
        startdate: Start date in YYYY-MM-DD format
        enddate: End date in YYYY-MM-DD format
        
    Returns:
        JSON response as dict, or None if request fails
    """
    if not API_KEY:
        logger.error("[marketdata.py].pulldata_twelvedata(): TWELVEDATA_API_KEY not configured")
        return None
    
    try:
        response = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "apikey": API_KEY,
                "symbol": symbol,
                "interval": interval,
                "start_date": startdate,
                "end_date": enddate,
                "format": "JSON"
            }
        )
        logger.debug(f"[marketdata.py].pulldata_twelvedata(): Fetching data for {symbol}")
        response.raise_for_status()  # Raise exception for bad status codes
    except requests.exceptions.RequestException as e:
        logger.error(f"[marketdata.py].pulldata_twelvedata(): Error fetching data for {symbol}: {e}")
        return None
    return response.json()

def pulldata_yahoo(symbol: str, interval: str, startdate: str, enddate: str) -> Optional[Dict[str, Any]]:
    """
    Fetch market data from Yahoo Finance.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        interval: Time interval ('1d' for daily, '5m' for 5-minute, etc.)
        startdate: Start date in YYYY-MM-DD format
        enddate: End date in YYYY-MM-DD format
        
    Returns:
        Dictionary with 'meta' and 'values' keys, or None if request fails
    """
    try:
        data = yf.download(symbol, start=startdate, end=enddate, interval=interval, multi_level_index=False)
        logger.debug(f"[marketdata.py].pulldata_yahoo(): Fetching data for {symbol}")

        output = {"meta": {"symbol": symbol, "interval": interval, "start_date": startdate, "end_date": enddate}}
        
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
        logger.debug(f"[marketdata.py].pulldata_yahoo(): Successfully fetched data for {symbol}, total records: {len(values)}")
        return output
    except Exception as e:
        logger.error(f"[marketdata.py].pulldata_yahoo(): Error fetching data for {symbol}: {e}")
        return None
