# Main program.  Everything starts here!

import os
import logging
from dotenv import load_dotenv
import ProcessData as pd
import marketdata as md
import sqlite3

# Load environment variables from .env file
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("[main.py]: Start of program")

try:
    # Establish a connection to the clover.db SQLite database
    conn1 = pd.connect_clover()
    cursor = conn1.cursor()
    
    # Update SysValue.GLOBAL_TODAY to current date. This is used as a reference point for pulling data and for logging.
    cursor.execute("UPDATE SysValue SET DateValue = date(CURRENT_TIMESTAMP) WHERE Name = 'GLOBAL_TODAY'")
    conn1.commit()
    
    # Query SysValue table for global dates
    logger.info("[main.py]: Querying SysValue for global dates")
    cursor.execute("select Name, DateValue from SysValue where Name in ('GLOBAL_STARTDATE', 'GLOBAL_TODAY')")
    sys_values = cursor.fetchall()
    sys_dict = {row[0]: row[1] for row in sys_values}
    global_startdate = sys_dict.get('GLOBAL_STARTDATE', '2025-01-01')
    global_today = sys_dict.get('GLOBAL_TODAY', '2026-04-01')
    logger.info(f"[main.py]: Global start date is {global_startdate}, Global today is {global_today}")
except sqlite3.Error as e:
    logger.error(f"[main.py]: Database error during initialization: {e}", exc_info=True)
    raise
except Exception as e:
    logger.error(f"[main.py]: Unexpected error during initialization: {e}", exc_info=True)
    raise

parentDir = os.getcwd()
logger.info(f"[main.py]: Parent directory is {parentDir}")

# Where logfiles reside
try:
    logDir = os.path.join(str(parentDir), "Logs")
    os.makedirs(logDir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(logDir, f"{global_today}.log"))
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    logger.info(f"[main.py]: Logging initialized. Log file is {os.path.join(logDir, global_today + '.log')}")
except IOError as e:
    logger.error(f"[main.py]: Error setting up log file: {e}", exc_info=True)

# Where new datafiles reside
dataDir = os.path.join(str(parentDir), 'Data')
logger.debug(f"[main.py]: Data directory is {dataDir}")

# Where processed datafiles reside.  After a datafile is processed in dataDir, it is moved to processedDataDir 
processedDataDir = os.path.join(str(parentDir), 'ProcessedData')
logger.debug(f"[main.py]: Processed data directory is {processedDataDir}")

# This SQL query retrieves all symbols from the WatchList table and determines the appropriate start date for pulling data for each symbol based on the latest date available in the EODData table.
# Incremental Updates: Avoids re-downloading data you already have. It starts pulling from the day after the last recorded date.
# Boundary Handling: The max(..., date('2025-01-01')) prevents pulling data before your global start date, which could be useful for limiting historical depth or avoiding API limits.
# Edge Cases: Handles symbols with no existing data gracefully.
try:
    cursor.execute("""
        select w.Symbol, 
        (case when max(e.Date) is NULL then ? 
        else max(date(max(e.Date),'+1 day'), date(?)) end) 
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
            
            with conn1:
                logger.debug("[main.py].EODData: Inserting data for symbol: %s", symbol)
                pd.insert_EODData(conn1, pulldata)
                logger.info("[main.py].EODData: Successfully processed symbol: %s", symbol)
        except Exception as e:
            logger.error("[main.py].EODData: Error processing symbol %s: %s", symbol, e, exc_info=True)
            continue
except sqlite3.Error as e:
    logger.error("[main.py]: Database error retrieving EODData symbols: %s", e, exc_info=True)
except Exception as e:
    logger.error("[main.py]: Unexpected error in EODData processing: %s", e, exc_info=True)

# This SQL query retrieves all symbols from the WatchList table and determines the appropriate start date for pulling data for each symbol based on the latest date available in the EODData table.
# Incremental Updates: Pulls tick data from the day after the last recorded timestamp, avoiding duplicates.
# Tick Data Specifics: Tick data is high-volume and often only relevant for recent periods (e.g., last 7 days). The 7-day fallback prevents overloading with old data, and the max(..., date('2026-04-21')) ensures it doesn't go beyond today.
# Edge Cases: Handles new symbols (no existing data) by starting 7 days back. If the last timestamp is recent, it resumes from the next day.
try:
    cursor.execute("""
        select w.Symbol, 
        (case when max(e.Timestamp) is NULL then date(?, '-7 days') 
        else max(date(max(e.Timestamp)), date(?, '-7 days')) end) 
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
            
            with conn1:
                logger.debug("[main.py].TickData: Inserting data for symbol: %s", symbol)
                pd.insert_Tickdata(conn1, pulldata)
                logger.info("[main.py].TickData: Successfully processed symbol: %s", symbol)
        except Exception as e:
            logger.error("[main.py].TickData: Error processing symbol %s: %s", symbol, e, exc_info=True)
            continue
except sqlite3.Error as e:
    logger.error("[main.py]: Database error retrieving TickData symbols: %s", e, exc_info=True)
except Exception as e:
    logger.error("[main.py]: Unexpected error in TickData processing: %s", e, exc_info=True)
finally:
    logger.info("[main.py]: Program execution completed")


