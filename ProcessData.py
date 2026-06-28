from pathlib import Path
import os
import logging
from typing import Dict, Any, Optional
import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv

load_dotenv()

parentDir = os.getcwd()

# inherit logging configuration from main.py
logger = logging.getLogger(__name__)
logger.debug(f"[ProcessData.py]: Parent directory: {parentDir}")


def _get_db_config() -> Dict[str, Any]:
    """Build PostgreSQL connection parameters from environment variables."""
    public_ip = os.getenv("DB_PUBLIC_IP") or os.getenv("DB_HOST")
    if not public_ip:
        raise RuntimeError("DB_PUBLIC_IP or DB_HOST must be set")

    if ":" in public_ip and public_ip.count(":") >= 2 and not os.getenv("DB_PUBLIC_IP"):
        raise RuntimeError(
            "DB_HOST appears to be a Cloud SQL instance connection name. Set DB_PUBLIC_IP to the public IP address."
        )

    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT")

    if not db_name or not db_user or not db_password or not db_port:
        raise RuntimeError("DB_NAME, DB_USER, DB_PASSWORD, and DB_PORT must be configured")

    return {
        "host": public_ip,
        "port": int(db_port),
        "dbname": db_name,
        "user": db_user,
        "password": db_password,
        "sslmode": os.getenv("DB_SSLMODE", "require"),
    }


def connect_clover() -> psycopg2.extensions.connection:
    """Return a PostgreSQL connection to the Clover database."""
    logger.debug("[ProcessData.py].connect_clover(): connect to PostgreSQL")
    return psycopg2.connect(**_get_db_config())

# Inserts from a json or dict data structure into the TickData table in the PostgreSQL database
def insert_Tickdata(connection: psycopg2.extensions.connection, data: Dict[str, Any]) -> int:
    if not data or 'values' not in data:
        logger.warning("[ProcessData.py].insert_tickdata(): No tick data to insert")
        return 0

    symbol = data.get('meta', {}).get('symbol')
    interval = data.get('meta', {}).get('interval')
    values = []

    for row in data['values']:
        timestamp = row.get('datetime') or row.get('Datetime')
        try:
            open_price = float(row.get('open', row.get('Open', 0)))
            high_price = float(row.get('high', row.get('High', 0)))
            low_price = float(row.get('low', row.get('Low', 0)))
            close_price = float(row.get('close', row.get('Close', 0)))
            volume = float(row.get('volume', row.get('Volume', 0)))
        except (ValueError, TypeError) as exc:
            logger.warning('Skipping invalid row %s: %s', row, exc)
            continue
        logger.debug("[ProcessData.py].insert_tickdata(): Inserting row for symbol %s: %s", symbol, row)
        values.append((symbol, interval, timestamp, open_price, high_price, low_price, close_price, volume))

    if not values:
        logger.warning("[ProcessData.py].insert_tickdata(): No valid tick rows were found in data1")
        return 0

    cursor = connection.cursor()

    # delete existing rows for the same symbol and timestamp to avoid duplicates (idempotent insert)
    cursor.execute("DELETE FROM TickData WHERE Symbol = %s AND Interval = %s AND Timestamp >= %s", (symbol, interval, values[0][2]))

    cursor.executemany(
        "INSERT INTO TickData (Symbol, Interval, Timestamp, Open, High, Low, Close, Volume, UpdateTimestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)",
        values
    )
    connection.commit()
    logger.debug("[ProcessData.py].insert_tickdata(): Inserted %d rows for symbol %s", cursor.rowcount, symbol)
    return cursor.rowcount

def insert_EODData(connection: psycopg2.extensions.connection, data: Dict[str, Any]) -> int:
    if not data or 'values' not in data:
        logger.warning("[ProcessData.py].insert_EODData(): No EOD data to insert")
        return 0

    symbol = data.get('meta', {}).get('symbol')
    interval = data.get('meta', {}).get('interval')
    values = []

    for row in data['values']:
        timestamp = row.get('datetime') or row.get('Datetime')
        try:
            open_price = float(row.get('open', row.get('Open', 0)))
            high_price = float(row.get('high', row.get('High', 0)))
            low_price = float(row.get('low', row.get('Low', 0)))
            close_price = float(row.get('close', row.get('Close', 0)))
            volume = float(row.get('volume', row.get('Volume', 0)))
        except (ValueError, TypeError) as exc:
            logger.warning("[ProcessData.py].insert_EODData(): Skipping invalid row %s: %s", row, exc)
            continue

        logger.debug("[ProcessData.py].insert_EODData(): Inserting row for symbol %s: %s", symbol, row)
        values.append((symbol, timestamp, open_price, high_price, low_price, close_price, volume))

    if not values:
        logger.warning("[ProcessData.py].insert_EODData(): No valid EOD rows were found in data")
        return 0

    cursor = connection.cursor()
    
    # delete existing rows for the same symbol and date to avoid duplicates (idempotent insert)
    cursor.execute("DELETE FROM EODData WHERE Symbol = %s AND Date >= %s", (symbol, values[0][1]))
    
    cursor.executemany(
        "INSERT INTO EODData (Symbol, Date, Open, High, Low, Close, Volume, UpdateTimestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)",
        values
    )
    connection.commit()
    logger.debug("[ProcessData.py].insert_EODData(): Inserted %d rows for symbol %s", cursor.rowcount, symbol)
    return cursor.rowcount


def TickData_generate(connection: psycopg2.extensions.connection, symbol: str) -> Optional[Dict[str, Any]]:
    """
    Generates a dictionary object containing tick data and metadata for charting.
    
    Args:
        connection: psycopg2 connection to the PostgreSQL database
        symbol: The stock symbol to retrieve data for
        
    Returns:
        A dictionary with:
        - "meta": Contains reference data (symbol, watchlist, interval, name, timezone)
        - "values": List of tick data records (timestamp, open, high, low, close, volume) sorted by timestamp
    """
    logger.debug("[ProcessData.py].TickData_generate(): Generating tick data for symbol %s", symbol)
    
    cursor = connection.cursor()
    
    # Query WatchList to get Symbol and WatchList
    cursor.execute("SELECT Symbol, WatchListName, Name, Timezone FROM WatchList WHERE Symbol = %s", (symbol,))
    watchlist_row = cursor.fetchone()
    
    if not watchlist_row:
        logger.warning("[ProcessData.py].TickData_generate(): No WatchList entry found for symbol %s", symbol)
        return None
    
    watchlist_symbol, watchlist_name, name, timezone = watchlist_row
    
    # Query TickData to get Interval and OHLCV data
    cursor.execute(
        "SELECT Interval, Timestamp, Open, High, Low, Close, Volume FROM TickData WHERE Symbol = %s ORDER BY Timestamp",
        (symbol,)
    )
    tick_rows = cursor.fetchall()
    
    if not tick_rows:
        logger.warning("[ProcessData.py].TickData_generate(): No TickData found for symbol %s", symbol)
        return None
    
    # Get interval from first row (should be same for all)
    interval = tick_rows[0][0]
    
    # Build the values list with tick data sorted by timestamp (normalized to lowercase keys)
    values = []
    for row in tick_rows:
        values.append({
            'timestamp': row[1],
            'open': row[2],
            'high': row[3],
            'low': row[4],
            'close': row[5],
            'volume': row[6]
        })
    
    # Build the meta dictionary (normalized to lowercase keys)
    meta = {
        'symbol': watchlist_symbol,
        'watchlist': watchlist_name,
        'interval': interval,
        'name': name,
        'timezone': timezone
    }
    
    # Build and return the final data dictionary
    data = {
        'meta': meta,
        'values': values
    }
    
    logger.debug("[ProcessData.py].TickData_generate(): Generated data for symbol %s with %d tick records", symbol, len(values))
    return data


def EODData_generate(connection: psycopg2.extensions.connection, symbol: str) -> Optional[Dict[str, Any]]:
    """
    Generates a dictionary object containing end-of-day market data and metadata for charting.
    
    Args:
        connection: psycopg2 connection to the PostgreSQL database
        symbol: The stock symbol to retrieve data for
        
    Returns:
        A dictionary with:
        - "meta": Contains reference data (symbol, watchlist, interval='1d', name, timezone)
        - "values": List of EOD records (date, timestamp, open, high, low, close, volume) sorted by date
    """
    logger.debug("[ProcessData.py].EODData_generate(): Generating EOD data for symbol %s", symbol)
    
    cursor = connection.cursor()
    
    # Query WatchList to get Symbol and WatchList
    cursor.execute("SELECT Symbol, WatchListName, Name, Timezone FROM WatchList WHERE Symbol = %s", (symbol,))
    watchlist_row = cursor.fetchone()
    
    if not watchlist_row:
        logger.warning("[ProcessData.py].EODData_generate(): No WatchList entry found for symbol %s", symbol)
        return None
    
    watchlist_symbol, watchlist_name, name, timezone = watchlist_row
    
    # Query EODData to get market close data
    cursor.execute(
        "SELECT Date, Date::timestamp as Timestamp, Open, High, Low, Close, Volume FROM EODData WHERE Symbol = %s ORDER BY Date",
        (symbol,)
    )
    eod_rows = cursor.fetchall()
    
    if not eod_rows:
        logger.warning("[ProcessData.py].EODData_generate(): No EODData found for symbol %s", symbol)
        return None
    
    # Build the values list with EOD data sorted by date (normalized to lowercase keys)
    values = []
    for row in eod_rows:
        values.append({
            'date': row[0],
            'timestamp': row[1],
            'open': row[2],
            'high': row[3],
            'low': row[4],
            'close': row[5],
            'volume': row[6]
        })
    
    # Build the meta dictionary with hardcoded interval '1d' (normalized to lowercase keys)
    meta = {
        'symbol': watchlist_symbol,
        'watchlist': watchlist_name,
        'interval': '1d',
        'name': name,
        'timezone': timezone
    }
    
    # Build and return the final data dictionary
    data = {
        'meta': meta,
        'values': values
    }
    
    logger.debug("[ProcessData.py].EODData_generate(): Generated data for symbol %s with %d EOD records", symbol, len(values))
    return data



