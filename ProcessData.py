from pathlib import Path
import os
import sqlite3
import logging
# import marketdata as md
parentDir = os.getcwd()

# inherit logging configuration from main.py
logger = logging.getLogger(__name__)
logger.debug(f"[ProcessData.py]: Parent directory: {parentDir}")

# Returns a connection to the clover.db SQLite database
def connect_clover():
    logger.debug("[ProcessData.py].connect_clover(): connect to clover.db")
    return sqlite3.connect(os.path.join(parentDir, 'SQLite', 'clover.db'))

# Inserts from a json or dict data structure into the TickData table in the clover.db SQLite database
def insert_Tickdata(connection, data):
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
        # logger.debug("[ProcessData.py].insert_tickdata(): Inserting row for symbol %s: %s", symbol, row)
        values.append((symbol, interval, timestamp, open_price, high_price, low_price, close_price, volume))

    if not values:
        logger.warning("[ProcessData.py].insert_tickdata(): No valid tick rows were found in data1")
        return 0

    cursor = connection.cursor()

    # delete existing rows for the same symbol and timestamp to avoid duplicates (idempotent insert)
    cursor.execute("DELETE FROM TickData WHERE Symbol = ? AND Interval = ? AND Timestamp >= ?", (symbol, interval, values[0][2]))

    cursor.executemany(
        "INSERT INTO TickData (Symbol, Interval, Timestamp, Open, High, Low, Close, Volume, UpdateDatetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
        values
    )
    connection.commit()
    logger.debug("[ProcessData.py].insert_tickdata(): Inserted %d rows for symbol %s", cursor.rowcount, symbol)
    return cursor.rowcount

def insert_EODData(connection, data):
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
    cursor.executemany(
        "INSERT INTO EODData (Symbol, Date, Open, High, Low, Close, Volume, UpdateDatetime) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
        values
    )
    connection.commit()
    logger.debug("[ProcessData.py].insert_EODData(): Inserted %d rows for symbol %s", cursor.rowcount, symbol)
    return cursor.rowcount


def TickData_generate(connection, symbol):
    """
    Generates a dictionary object containing tick data and metadata for charting.
    
    Args:
        connection: SQLite database connection to clover.db
        symbol: The stock symbol to retrieve data for
        
    Returns:
        A dictionary with:
        - "meta": Contains reference data (Symbol, WatchList, Interval, Name, Timezone)
        - "values": List of tick data records (Timestamp, Open, High, Low, Close, Volume) sorted by Timestamp
    """
    logger.debug("[ProcessData.py].TickData_generate(): Generating tick data for symbol %s", symbol)
    
    cursor = connection.cursor()
    
    # Query WatchList to get Symbol and WatchList
    cursor.execute("SELECT Symbol, WatchListName, Name, Timezone FROM WatchList WHERE Symbol = ?", (symbol,))
    watchlist_row = cursor.fetchone()
    
    if not watchlist_row:
        logger.warning("[ProcessData.py].TickData_generate(): No WatchList entry found for symbol %s", symbol)
        return None
    
    watchlist_symbol, watchlist_name, name, timezone = watchlist_row
    
    # Query TickData to get Interval and OHLCV data
    cursor.execute(
        "SELECT Interval, Timestamp, Open, High, Low, Close, Volume FROM TickData WHERE Symbol = ? ORDER BY Timestamp",
        (symbol,)
    )
    tick_rows = cursor.fetchall()
    
    if not tick_rows:
        logger.warning("[ProcessData.py].TickData_generate(): No TickData found for symbol %s", symbol)
        return None
    
    # Get interval from first row (should be same for all)
    interval = tick_rows[0][0]
    
    # Build the values list with tick data sorted by timestamp
    values = []
    for row in tick_rows:
        values.append({
            'Timestamp': row[1],
            'Open': row[2],
            'High': row[3],
            'Low': row[4],
            'Close': row[5],
            'Volume': row[6]
        })
    
    # Build the meta dictionary
    meta = {
        'Symbol': watchlist_symbol,
        'WatchList': watchlist_name,
        'Interval': interval,
        'Name': name,
        'Timezone': timezone
    }
    
    # Build and return the final data dictionary
    data = {
        'meta': meta,
        'values': values
    }
    
    logger.debug("[ProcessData.py].TickData_generate(): Generated data for symbol %s with %d tick records", symbol, len(values))
    return data


def EODData_generate(connection, symbol):
    """
    Generates a dictionary object containing end-of-day market data and metadata for charting.
    
    Args:
        connection: SQLite database connection to clover.db
        symbol: The stock symbol to retrieve data for
        
    Returns:
        A dictionary with:
        - "meta": Contains reference data (Symbol, WatchList, Interval='1d', Name, Timezone)
        - "values": List of EOD records (Date, Open, High, Low, Close, Volume) sorted by Date
    """
    logger.debug("[ProcessData.py].EODData_generate(): Generating EOD data for symbol %s", symbol)
    
    cursor = connection.cursor()
    
    # Query WatchList to get Symbol and WatchList
    cursor.execute("SELECT Symbol, WatchListName, Name, Timezone FROM WatchList WHERE Symbol = ?", (symbol,))
    watchlist_row = cursor.fetchone()
    
    if not watchlist_row:
        logger.warning("[ProcessData.py].EODData_generate(): No WatchList entry found for symbol %s", symbol)
        return None
    
    watchlist_symbol, watchlist_name, name, timezone = watchlist_row
    
    # Query EODData to get market close data
    cursor.execute(
        "SELECT Date, datetime(Date) as Timestamnp, Open, High, Low, Close, Volume FROM EODData WHERE Symbol = ? ORDER BY Date",
        (symbol,)
    )
    eod_rows = cursor.fetchall()
    
    if not eod_rows:
        logger.warning("[ProcessData.py].EODData_generate(): No EODData found for symbol %s", symbol)
        return None
    
    # Build the values list with EOD data sorted by date
    values = []
    for row in eod_rows:
        values.append({
            'Date': row[0],
            'Timestamp': row[1],
            'Open': row[2],
            'High': row[3],
            'Low': row[4],
            'Close': row[5],
            'Volume': row[6]
        })
    
    # Build the meta dictionary with hardcoded interval '1d'
    meta = {
        'Symbol': watchlist_symbol,
        'WatchList': watchlist_name,
        'Interval': '1d',
        'Name': name,
        'Timezone': timezone
    }
    
    # Build and return the final data dictionary
    data = {
        'meta': meta,
        'values': values
    }
    
    logger.debug("[ProcessData.py].EODData_generate(): Generated data for symbol %s with %d EOD records", symbol, len(values))
    return data



