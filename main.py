# Main program.  Everything starts here!

import os
import sys
import subprocess

# Auto-re-execute using the virtual environment if running outside it
_venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
if os.path.isdir(_venv_dir):
    _venv_python = os.path.join(_venv_dir, "Scripts", "python.exe") if os.name == "nt" else os.path.join(_venv_dir, "bin", "python")
    if os.path.exists(_venv_python) and os.path.abspath(sys.executable).lower() != os.path.abspath(_venv_python).lower():
        result = subprocess.run([_venv_python] + sys.argv)
        sys.exit(result.returncode)

import logging
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import ProcessData as pd
import marketdata as md
import psycopg2
from typing import Tuple

# Initialize logging base config
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_file_logging(parentDir: str, global_today: str) -> None:
    """Setup FileHandler for logging into the Logs/ directory."""
    try:
        logDir = os.path.join(str(parentDir), "Logs")
        os.makedirs(logDir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(logDir, f"{global_today}.log"))
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
        logger.info(f"[main.py]: Logging initialized. Log file is {os.path.join(logDir, global_today + '.log')}")
    except IOError as e:
        logger.error(f"[main.py]: Error setting up log file: {e}", exc_info=True)

def sync_global_today(cursor: psycopg2.extensions.cursor) -> Tuple[str, str]:
    """Update and retrieve global dates from SysValue table."""
    # Update SysValue.GLOBAL_TODAY to current date
    cursor.execute("UPDATE SysValue SET DateValue = CURRENT_DATE WHERE Name = 'GLOBAL_TODAY'")
    
    # Query SysValue table for global dates
    logger.info("[main.py]: Querying SysValue for global dates")
    cursor.execute("select Name, DateValue from SysValue where Name in ('GLOBAL_STARTDATE', 'GLOBAL_TODAY')")
    sys_values = cursor.fetchall()
    sys_dict = {row[0]: row[1] for row in sys_values}
    global_startdate_raw = sys_dict.get('GLOBAL_STARTDATE', '2025-01-01')
    global_today_raw = sys_dict.get('GLOBAL_TODAY', '2026-04-01')
    
    global_startdate = global_startdate_raw.strftime('%Y-%m-%d') if hasattr(global_startdate_raw, 'strftime') else str(global_startdate_raw).split()[0]
    global_today = global_today_raw.strftime('%Y-%m-%d') if hasattr(global_today_raw, 'strftime') else str(global_today_raw).split()[0]
    
    logger.info(f"[main.py]: Global start date is {global_startdate}, Global today is {global_today}")
    return global_startdate, global_today

def fetch_and_store_eod(cursor: psycopg2.extensions.cursor, conn: psycopg2.extensions.connection, global_startdate: str, global_today: str) -> None:
    """Fetch End-Of-Day market data from Yahoo Finance and insert it into database."""
    try:
        cursor.execute("""
            select w.Symbol, 
            (case when max(e.Date) is NULL then CAST(%s AS date) 
            else GREATEST((max(e.Date) + INTERVAL '1 day')::date, CAST(%s AS date)) end) 
            from WatchList w left join EODData e on w.Symbol=e.Symbol group by w.Symbol
            """, (global_startdate, global_startdate))
        logger.debug("[main.py]: Retrieved symbols from WatchList for EODData")
        
        symbols = cursor.fetchall()
        
        for symbol_tuple in symbols:
            symbol = symbol_tuple[0]
            symbol_start_date = symbol_tuple[1]
            logger.debug("[main.py].EODData: Processing symbol: %s with start date: %s", symbol, symbol_start_date)
            
            try:
                pulldata = md.pulldata_yahoo(symbol, "1d", symbol_start_date, global_today)
                
                if pulldata is None:
                    logger.warning("[main.py].EODData: No data retrieved for symbol: %s", symbol)
                    continue
                
                logger.debug("[main.py].EODData: Inserting data for symbol: %s", symbol)
                pd.insert_EODData(conn, pulldata)
                conn.commit()
                logger.info("[main.py].EODData: Successfully processed symbol: %s", symbol)
            except Exception as e:
                logger.error("[main.py].EODData: Error processing symbol %s: %s", symbol, e, exc_info=True)
                conn.rollback()
                continue
    except psycopg2.Error as e:
        logger.error("[main.py]: Database error retrieving EODData symbols: %s", e, exc_info=True)
    except Exception as e:
        logger.error("[main.py]: Unexpected error in EODData processing: %s", e, exc_info=True)
def fetch_and_store_tick(cursor: psycopg2.extensions.cursor, conn: psycopg2.extensions.connection, global_today: str) -> None:
    """Fetch Tick market data from Yahoo Finance and insert it into database.
    
    This SQL query retrieves all symbols from the WatchList table and determines the appropriate start date for pulling data for each symbol based on the latest date available in the EODData table.
    Incremental Updates: Pulls tick data from the day after the last recorded timestamp, avoiding duplicates.
    Tick Data Specifics: Tick data is high-volume and often only relevant for recent periods (e.g., last 7 days). The 7-day fallback prevents overloading with old data, and the max(..., date('2026-04-21')) ensures it doesn't go beyond today.
    Edge Cases: Handles new symbols (no existing data) by starting 7 days back. If the last timestamp is recent, it resumes from the next day.
    """
    try:
        cursor.execute("""
            select w.Symbol, 
            (case when max(e.Timestamp) is NULL then (CAST(%s AS date) - INTERVAL '7 days')::date 
            else GREATEST(max(e.Timestamp)::date, (CAST(%s AS date) - INTERVAL '7 days')::date) end) 
            from WatchList w left join TickData e on w.Symbol=e.Symbol group by w.Symbol
            """, (global_today, global_today))
        logger.debug("[main.py].TickData: Retrieved symbols from WatchList for TickData")
        
        symbols = cursor.fetchall()
        
        for symbol_tuple in symbols:
            symbol = symbol_tuple[0]
            symbol_start_date = symbol_tuple[1]
            logger.debug("[main.py].TickData: Processing symbol: %s with start date: %s", symbol, symbol_start_date)
            
            try:
                pulldata = md.pulldata_yahoo(symbol, "5m", symbol_start_date, global_today)
                
                if pulldata is None:
                    logger.warning("[main.py].TickData: No data retrieved for symbol: %s", symbol)
                    continue
                
                logger.debug("[main.py].TickData: Inserting data for symbol: %s", symbol)
                pd.insert_Tickdata(conn, pulldata)
                conn.commit()
                logger.info("[main.py].TickData: Successfully processed symbol: %s", symbol)
            except Exception as e:
                logger.error("[main.py].TickData: Error processing symbol %s: %s", symbol, e, exc_info=True)
                conn.rollback()
                continue
    except psycopg2.Error as e:
        logger.error("[main.py]: Database error retrieving TickData symbols: %s", e, exc_info=True)
    except Exception as e:
        logger.error("[main.py]: Unexpected error in TickData processing: %s", e, exc_info=True)

def main() -> None:
    # Load environment variables from .env file
    load_dotenv()

    logger.info("[main.py]: Start of program")
    
    parentDir = os.getcwd()
    logger.info(f"[main.py]: Parent directory is {parentDir}")

    try:
        # Establish a connection to the PostgreSQL database with context manager
        with pd.connect_clover() as conn1:
            with conn1.cursor() as cursor:
                # Update GLOBAL_TODAY and retrieve system start/today dates
                global_startdate, global_today = sync_global_today(cursor)
                conn1.commit()
                
                # Setup log files dynamically based on date
                setup_file_logging(parentDir, global_today)
                
                # Fetch and store EOD market data
                fetch_and_store_eod(cursor, conn1, global_startdate, global_today)
                
                # Fetch and store Tick market data
                fetch_and_store_tick(cursor, conn1, global_today)
                
    except psycopg2.Error as e:
        logger.error(f"[main.py]: Database error during main execution: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"[main.py]: Unexpected error during main execution: {e}", exc_info=True)
        raise
    finally:
        logger.info("[main.py]: Program execution completed")

if __name__ == "__main__":
    main()
