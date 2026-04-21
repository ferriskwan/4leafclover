from pathlib import Path
import os
import sqlite3
import logging
import marketdata as md

parentDir = os.getcwd()
print(f"Parent directory: {parentDir}")


# inherit logging configuration from main.py
logger = logging.getLogger(__name__)

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
        logger.debug("[ProcessData.py].insert_tickdata(): Inserting row for symbol %s: %s", symbol, row)
        values.append((symbol, interval, timestamp, open_price, high_price, low_price, close_price, volume))

    if not values:
        logger.warning("[ProcessData.py].insert_tickdata(): No valid tick rows were found in data1")
        return 0

    cursor = connection.cursor()
    cursor.executemany(
        "INSERT INTO TickData (Symbol, Interval, Timestamp, Open, High, Low, Close, Volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
        "INSERT INTO EODData (Symbol, Date, Open, High, Low, Close, Volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
        values
    )
    connection.commit()
    logger.debug("[ProcessData.py].insert_EODData(): Inserted %d rows for symbol %s", cursor.rowcount, symbol)
    return cursor.rowcount


# Pull the tick data first, then insert into SQLite
# data1 = md.pulldata_twelvedata("GLW", "5min", "2026-04-15", "2026-04-16")
# data3 = md.pulldata_yahoo("5E2.SI", "5m", "2026-04-15", "2026-04-16")
# 
# conn = connect_clover()
# with conn:
#     inserted = insert_tickdata(conn, data1)
#     print(f'Inserted {inserted} rows into TickData')
#     cursor = conn.cursor()
#     cursor.execute("SELECT count(*) FROM TickData")
#     results = cursor.fetchall()
#     print(results)

