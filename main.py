# Main program.  Everything starts here!

import os
import logging
import ProcessData as pd
import marketdata as md
import sqlite3

global_startdate = "2025-01-01"
global_today = "2026-04-21"

parentDir = os.getcwd()
print(f"Parent directory: {parentDir}")

# Where new datafiles reside
dataDir = os.path.join(str(parentDir), 'Data')

# Where processed datafiles resiide
# After a datafile is processed in dataDir, it is moved to processedDataDir 
processedDataDir = os.path.join(str(parentDir), 'ProcessedData')

logDir = os.path.join(str(parentDir), "Logs")
logging.basicConfig(filename=str(os.path.join(str(logDir), str(global_today) + ".log")), level=logging.DEBUG, format='%(asctime)s -  %(levelname)s -  %(message)s')

logging.debug("[main.py]: Start of program")
conn1 = pd.connect_clover()

cursor = conn1.cursor()

# This SQL query retrieves all symbols from the WatchList table and determines the appropriate start date for pulling data for each symbol based on the latest date available in the EODData table.
# Incremental Updates: Avoids re-downloading data you already have. It starts pulling from the day after the last recorded date.
# Boundary Handling: The max(..., date('2025-01-01')) prevents pulling data before your global start date, which could be useful for limiting historical depth or avoiding API limits.
# Edge Cases: Handles symbols with no existing data gracefully.
cursor.execute("select w.Symbol, (case when max(e.Date) is NULL then '"+str(global_startdate)+"' "
    "else max(date(max(e.Date),'+1 day'),date('"+str(global_startdate)+"')) end) "
    "from WatchList w left join EODData e on w.Symbol=e.Symbol group by w.Symbol")
logging.debug("[main.py]: Retrieved symbols from WatchList for EODData")

symbols = cursor.fetchall()

for symbol_tuple in symbols:
    symbol = symbol_tuple[0]
    symbol_start_date = symbol_tuple[1]
    logging.debug("[main.py].EODData: Processing symbol: %s with start date: %s", symbol, symbol_start_date)
    pulldata = md.pulldata_yahoo(symbol, "1d", symbol_start_date, global_today)
    with conn1:
        logging.debug("[main.py].EODData: Inserting data for symbol: %s", symbol)
        pd.insert_EODData(conn1, pulldata)

# This SQL query retrieves all symbols from the WatchList table and determines the appropriate start date for pulling data for each symbol based on the latest date available in the EODData table.
# Incremental Updates: Pulls tick data from the day after the last recorded timestamp, avoiding duplicates.
# Tick Data Specifics: Tick data is high-volume and often only relevant for recent periods (e.g., last 7 days). The 7-day fallback prevents overloading with old data, and the max(..., date('2026-04-21')) ensures it doesn't go beyond today.
# Edge Cases: Handles new symbols (no existing data) by starting 7 days back. If the last timestamp is recent, it resumes from the next day.
cursor.execute("select w.Symbol, (case when max(e.Timestamp) is NULL then date('"+str(global_today)+"','-7 days') "
    "else max(date(max(e.Timestamp),'+1 day'),date('"+str(global_today)+"')) end) "
    "from WatchList w left join TickData e on w.Symbol=e.Symbol group by w.Symbol")
logging.debug("[main.py].TickData: Retrieved symbols from WatchList for TickData")
print(cursor.fetchall())

symbols = cursor.fetchall()

for symbol_tuple in symbols:
    symbol = symbol_tuple[0]
    symbol_start_date = symbol_tuple[1]
    logging.debug("[main.py].TickData: Processing symbol: %s with start date: %s", symbol, symbol_start_date)
    pulldata = md.pulldata_yahoo(symbol, "5m", symbol_start_date, global_today)
    with conn1:
        logging.debug("[main.py].TickData: Inserting data for symbol: %s", symbol)
        pd.insert_Tickdata(conn1, pulldata)
