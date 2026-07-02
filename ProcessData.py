from pathlib import Path
import os
import logging
import json
import csv
from typing import Dict, Any, Optional, Union
import psycopg2
import psycopg2.extensions
import psycopg2.pool
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


def _json_serialize_helper(obj):
    """JSON serializer helper for date/datetime objects."""
    from datetime import datetime, date
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def connect_clover() -> psycopg2.extensions.connection:
    """Return a PostgreSQL connection to the Clover database."""
    logger.debug("[ProcessData.py].connect_clover(): connect to PostgreSQL")
    return psycopg2.connect(**_get_db_config())


_db_pool = None


def init_pool(minconn: int = 1, maxconn: int = 20):
    """Initialize a ThreadedConnectionPool for database connections."""
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = psycopg2.pool.ThreadedConnectionPool(minconn, maxconn, **_get_db_config())
            logger.info("[ProcessData.py]: Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"[ProcessData.py]: Failed to initialize database connection pool: {e}", exc_info=True)
            raise


def close_pool():
    """Safely close all pooled connections."""
    global _db_pool
    if _db_pool is not None:
        try:
            _db_pool.closeall()
            logger.info("[ProcessData.py]: Database connection pool closed")
        except Exception as e:
            logger.error(f"[ProcessData.py]: Error closing connection pool: {e}", exc_info=True)
        finally:
            _db_pool = None


def get_connection() -> psycopg2.extensions.connection:
    """Retrieve a connection from the pool, or fallback to a direct connection."""
    global _db_pool
    if _db_pool is None:
        logger.debug("[ProcessData.py]: No pool initialized; fallback to direct connect_clover()")
        return connect_clover()
    return _db_pool.getconn()


def put_connection(conn: psycopg2.extensions.connection, close: bool = False):
    """Return a connection to the pool, or close/discard it if requested or closed."""
    global _db_pool
    if conn:
        try:
            if conn.closed:
                close = True
            elif not close:
                conn.rollback()
        except Exception as e:
            logger.warning(f"[ProcessData.py]: Error during connection reset: {e}")
            close = True

        if _db_pool is not None:
            try:
                _db_pool.putconn(conn, close=close)
            except Exception as e:
                logger.error(f"[ProcessData.py]: Error returning connection to pool: {e}", exc_info=True)
        else:
            try:
                conn.close()
            except Exception:
                pass

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


def TickData_generate(
    connection: psycopg2.extensions.connection, 
    symbol: str, 
    output_format: str = "dict", 
    csv_path: Optional[str] = None
) -> Optional[Union[Dict[str, Any], str]]:
    """
    Generates a dictionary, JSON, or CSV file containing tick data and metadata for charting.
    
    Args:
        connection: psycopg2 connection to the PostgreSQL database
        symbol: The stock symbol to retrieve data for
        output_format: Desired output format: "dict" (Python dict), "json" (JSON string), or "csv" (CSV file path)
        csv_path: Optional custom file path where the CSV data should be saved if output_format="csv"
        
    Returns:
        - If output_format="dict": A dictionary with "meta" and "values" keys.
        - If output_format="json": A serialized JSON string of the dictionary.
        - If output_format="csv": The file path string where the CSV data was saved.
        - Returns None if the symbol is not in the WatchList or if no TickData is found.
    """
    logger.debug("[ProcessData.py].TickData_generate(): Generating tick data for symbol %s in format %s", symbol, output_format)
    
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
        """
        SELECT Interval, Timestamp, Open, High, Low, Close, Volume 
        FROM TickData 
        WHERE Symbol = %s 
          AND Timestamp >= (SELECT CAST(MAX(Timestamp) AS date) - INTERVAL '7 days' FROM TickData WHERE Symbol = %s)
        ORDER BY Timestamp
        """,
        (symbol, symbol)
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
    
    # Build the final data dictionary
    data = {
        'meta': meta,
        'values': values
    }
    
    logger.debug("[ProcessData.py].TickData_generate(): Generated data for symbol %s with %d tick records", symbol, len(values))
    
    # Return formatted output based on requested format
    if output_format == "json":
        # Serialize python dictionary containing datetime objects to JSON
        return json.dumps(data, default=_json_serialize_helper, indent=4)
        
    elif output_format == "csv":
        # Save to default folder (ProcessedData/) if no path is specified
        if not csv_path:
            os.makedirs("ProcessedData", exist_ok=True)
            csv_path = os.path.join("ProcessedData", f"{symbol}_tick.csv")
        else:
            dir_name = os.path.dirname(csv_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
                
        # Write tabular values to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            writer.writeheader()
            for row in values:
                writer.writerow({
                    'timestamp': row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                })
        logger.debug("[ProcessData.py].TickData_generate(): CSV file saved at %s", csv_path)
        return csv_path
        
    else:
        # Default: return native python dictionary
        return data


def EODData_generate(
    connection: psycopg2.extensions.connection, 
    symbol: str, 
    output_format: str = "dict", 
    csv_path: Optional[str] = None
) -> Optional[Union[Dict[str, Any], str]]:
    """
    Generates a dictionary, JSON, or CSV file containing end-of-day market data and metadata for charting.
    
    Args:
        connection: psycopg2 connection to the PostgreSQL database
        symbol: The stock symbol to retrieve data for
        output_format: Desired output format: "dict" (Python dict), "json" (JSON string), or "csv" (CSV file path)
        csv_path: Optional custom file path where the CSV data should be saved if output_format="csv"
        
    Returns:
        - If output_format="dict": A dictionary with "meta" and "values" keys.
        - If output_format="json": A serialized JSON string of the dictionary.
        - If output_format="csv": The file path string where the CSV data was saved.
        - Returns None if the symbol is not in the WatchList or if no EODData is found.
    """
    logger.debug("[ProcessData.py].EODData_generate(): Generating EOD data for symbol %s in format %s", symbol, output_format)
    
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
        """
        SELECT Date, Date::timestamp as Timestamp, Open, High, Low, Close, Volume 
        FROM EODData 
        WHERE Symbol = %s 
          AND Date >= (SELECT CAST(MAX(Date::timestamp) AS date) - INTERVAL '2 years' FROM EODData WHERE Symbol = %s)
        ORDER BY Date
        """,
        (symbol, symbol)
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
    
    # Build the final data dictionary
    data = {
        'meta': meta,
        'values': values
    }
    
    logger.debug("[ProcessData.py].EODData_generate(): Generated data for symbol %s with %d EOD records", symbol, len(values))
    
    # Return formatted output based on requested format
    if output_format == "json":
        # Serialize python dictionary containing date/datetime objects to JSON
        return json.dumps(data, default=_json_serialize_helper, indent=4)
        
    elif output_format == "csv":
        # Save to default folder (ProcessedData/) if no path is specified
        if not csv_path:
            os.makedirs("ProcessedData", exist_ok=True)
            csv_path = os.path.join("ProcessedData", f"{symbol}_eod.csv")
        else:
            dir_name = os.path.dirname(csv_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
                
        # Write tabular values to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])
            writer.writeheader()
            for row in values:
                writer.writerow({
                    'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']),
                    'timestamp': row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                })
        logger.debug("[ProcessData.py].EODData_generate(): CSV file saved at %s", csv_path)
        return csv_path
        
    else:
        # Default: return native python dictionary
        return data


# ==========================================
# WatchList & Trade Database Operations
# ==========================================

def get_watchlist(
    connection: psycopg2.extensions.connection, 
    watchlistname: Optional[str] = None, 
    symbol: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve watchlist entries, optionally filtered by watchlistname and symbol."""
    logger.debug("[ProcessData.py].get_watchlist(): Querying watchlist records")
    cursor = connection.cursor()
    query = "SELECT watchlistname, symbol, name, timezone, updatetimestamp FROM watchlist WHERE 1=1"
    params = []
    
    if watchlistname:
        query += " AND watchlistname = %s"
        params.append(watchlistname)
    if symbol:
        query += " AND symbol = %s"
        params.append(symbol)
        
    query += " ORDER BY watchlistname, symbol"
    cursor.execute(query, params)
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "watchlistname": row[0],
            "symbol": row[1],
            "name": row[2],
            "timezone": row[3],
            "updatetimestamp": row[4]
        })
    return results


def insert_watchlist(
    connection: psycopg2.extensions.connection, 
    watchlistname: str, 
    symbol: str, 
    name: str, 
    timezone: str
) -> Dict[str, Any]:
    """Insert a new stock entry into the watchlist."""
    logger.debug(f"[ProcessData.py].insert_watchlist(): Inserting symbol {symbol} into watchlist {watchlistname}")
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO watchlist (watchlistname, symbol, name, timezone, updatetimestamp)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        RETURNING watchlistname, symbol, name, timezone, updatetimestamp
        """,
        (watchlistname, symbol, name, timezone)
    )
    row = cursor.fetchone()
    return {
        "watchlistname": row[0],
        "symbol": row[1],
        "name": row[2],
        "timezone": row[3],
        "updatetimestamp": row[4]
    }


def update_watchlist(
    connection: psycopg2.extensions.connection, 
    watchlistname: str, 
    symbol: str, 
    name: Optional[str] = None, 
    timezone: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update descriptive fields of a watchlist entry."""
    logger.debug(f"[ProcessData.py].update_watchlist(): Updating watchlist {watchlistname}, symbol {symbol}")
    cursor = connection.cursor()
    
    # Build dynamic update statement
    fields = []
    params = []
    if name is not None:
        fields.append("name = %s")
        params.append(name)
    if timezone is not None:
        fields.append("timezone = %s")
        params.append(timezone)
        
    if not fields:
        # No updates provided, fetch current state
        res = get_watchlist(connection, watchlistname, symbol)
        return res[0] if res else None
        
    params.extend([watchlistname, symbol])
    query = f"""
        UPDATE watchlist 
        SET {', '.join(fields)}, updatetimestamp = CURRENT_TIMESTAMP
        WHERE watchlistname = %s AND symbol = %s
        RETURNING watchlistname, symbol, name, timezone, updatetimestamp
    """
    
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row:
        return {
            "watchlistname": row[0],
            "symbol": row[1],
            "name": row[2],
            "timezone": row[3],
            "updatetimestamp": row[4]
        }
    return None


def delete_watchlist(
    connection: psycopg2.extensions.connection, 
    watchlistname: str, 
    symbol: str
) -> bool:
    """Delete a watchlist entry by composite key."""
    logger.debug(f"[ProcessData.py].delete_watchlist(): Deleting watchlist {watchlistname}, symbol {symbol}")
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM watchlist WHERE watchlistname = %s AND symbol = %s",
        (watchlistname, symbol)
    )
    return cursor.rowcount > 0


def watchlist_symbol_exists(
    connection: psycopg2.extensions.connection, 
    symbol: str
) -> bool:
    """Check if a stock symbol exists in any watchlist."""
    logger.debug(f"[ProcessData.py].watchlist_symbol_exists(): Checking symbol {symbol}")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT 1 FROM watchlist WHERE symbol = %s LIMIT 1",
        (symbol,)
    )
    return cursor.fetchone() is not None


def get_trades(
    connection: psycopg2.extensions.connection, 
    symbol: Optional[str] = None, 
    buysell: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve trades, optionally filtered by symbol and buysell."""
    logger.debug("[ProcessData.py].get_trades(): Querying trade records")
    cursor = connection.cursor()
    query = "SELECT id, symbol, buysell, tradedate, investment, price, quantity, remarks, updatetimestamp FROM trade WHERE 1=1"
    params = []
    
    if symbol:
        query += " AND symbol = %s"
        params.append(symbol)
    if buysell:
        query += " AND buysell = %s"
        params.append(buysell)
        
    query += " ORDER BY tradedate DESC, id DESC"
    cursor.execute(query, params)
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row[0],
            "symbol": row[1],
            "buysell": row[2],
            "tradedate": row[3],
            "investment": row[4],
            "price": row[5],
            "quantity": row[6],
            "remarks": row[7],
            "updatetimestamp": row[8]
        })
    return results


def insert_trade(
    connection: psycopg2.extensions.connection,
    symbol: str,
    buysell: str,
    tradedate: Any,
    investment: bool,
    price: Optional[float],
    quantity: float,
    remarks: Optional[str]
) -> Dict[str, Any]:
    """Insert a new trade log (generating trade ID)."""
    logger.debug(f"[ProcessData.py].insert_trade(): Logging trade for symbol {symbol}")
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO trade (symbol, buysell, tradedate, investment, price, quantity, remarks, updatetimestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        RETURNING id, symbol, buysell, tradedate, investment, price, quantity, remarks, updatetimestamp
        """,
        (symbol, buysell, tradedate, investment, price, quantity, remarks)
    )
    row = cursor.fetchone()
    return {
        "id": row[0],
        "symbol": row[1],
        "buysell": row[2],
        "tradedate": row[3],
        "investment": row[4],
        "price": row[5],
        "quantity": row[6],
        "remarks": row[7],
        "updatetimestamp": row[8]
    }


def update_trade(
    connection: psycopg2.extensions.connection,
    trade_id: int,
    symbol: Optional[str] = None,
    buysell: Optional[str] = None,
    tradedate: Optional[Any] = None,
    investment: Optional[bool] = None,
    price: Optional[float] = None,
    quantity: Optional[float] = None,
    remarks: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update existing trade fields."""
    logger.debug(f"[ProcessData.py].update_trade(): Updating trade ID {trade_id}")
    cursor = connection.cursor()
    
    # Build dynamic update statement
    fields = []
    params = []
    
    if symbol is not None:
        fields.append("symbol = %s")
        params.append(symbol)
    if buysell is not None:
        fields.append("buysell = %s")
        params.append(buysell)
    if tradedate is not None:
        fields.append("tradedate = %s")
        params.append(tradedate)
    if investment is not None:
        fields.append("investment = %s")
        params.append(investment)
    if price is not None:
        fields.append("price = %s")
        params.append(price)
    if quantity is not None:
        fields.append("quantity = %s")
        params.append(quantity)
    if remarks is not None:
        fields.append("remarks = %s")
        params.append(remarks)
        
    if not fields:
        # Fetch current record state
        cursor.execute("SELECT id, symbol, buysell, tradedate, investment, price, quantity, remarks, updatetimestamp FROM trade WHERE id = %s", (trade_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0], "symbol": row[1], "buysell": row[2], "tradedate": row[3],
                "investment": row[4], "price": row[5], "quantity": row[6], "remarks": row[7], "updatetimestamp": row[8]
            }
        return None
        
    params.append(trade_id)
    query = f"""
        UPDATE trade 
        SET {', '.join(fields)}, updatetimestamp = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, symbol, buysell, tradedate, investment, price, quantity, remarks, updatetimestamp
    """
    
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "symbol": row[1],
            "buysell": row[2],
            "tradedate": row[3],
            "investment": row[4],
            "price": row[5],
            "quantity": row[6],
            "remarks": row[7],
            "updatetimestamp": row[8]
        }
    return None


def delete_trade(
    connection: psycopg2.extensions.connection, 
    trade_id: int
) -> bool:
    """Delete a trade entry by ID."""
    logger.debug(f"[ProcessData.py].delete_trade(): Deleting trade ID {trade_id}")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM trade WHERE id = %s", (trade_id,))
    return cursor.rowcount > 0



