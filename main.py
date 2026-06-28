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
import marketdata as md
import requests
from typing import Tuple, List, Dict, Any

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

def init_system_dates(api_url: str, headers: dict) -> Tuple[str, str]:
    """Call the API system initialization endpoint to update and retrieve dates."""
    logger.info("[main.py]: Initializing system dates via API")
    response = requests.post(f"{api_url}/api/v1/sys/init", headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["global_startdate"], data["global_today"]

def fetch_and_store_eod(api_url: str, headers: dict, global_startdate: str, global_today: str) -> None:
    """Fetch End-Of-Day market data and upload it to the Cloud API server."""
    logger.info("[main.py]: Fetching EOD symbols queue from API")
    response = requests.get(f"{api_url}/api/v1/eod/symbols", params={"global_startdate": global_startdate}, headers=headers)
    response.raise_for_status()
    symbols_queue = response.json()
    
    for item in symbols_queue:
        symbol = item["symbol"]
        symbol_start_date = item["start_date"]
        logger.debug("[main.py].EODData: Processing symbol: %s with start date: %s", symbol, symbol_start_date)
        
        try:
            pulldata = md.pulldata_yahoo(symbol, "1d", symbol_start_date, global_today)
            if pulldata is None:
                logger.warning("[main.py].EODData: No data retrieved for symbol: %s", symbol)
                continue
            
            logger.debug("[main.py].EODData: Sending data for symbol: %s", symbol)
            upload_response = requests.post(f"{api_url}/api/v1/eod", json=pulldata, headers=headers)
            upload_response.raise_for_status()
            logger.info("[main.py].EODData: Successfully processed symbol: %s. Response: %s", symbol, upload_response.json())
        except Exception as e:
            logger.error("[main.py].EODData: Error processing symbol %s: %s", symbol, e, exc_info=True)
            continue

def fetch_and_store_tick(api_url: str, headers: dict, global_today: str) -> None:
    """Fetch Tick market data and upload it to the Cloud API server."""
    logger.info("[main.py]: Fetching Tick symbols queue from API")
    response = requests.get(f"{api_url}/api/v1/tick/symbols", params={"global_today": global_today}, headers=headers)
    response.raise_for_status()
    symbols_queue = response.json()
    
    for item in symbols_queue:
        symbol = item["symbol"]
        symbol_start_date = item["start_date"]
        logger.debug("[main.py].TickData: Processing symbol: %s with start date: %s", symbol, symbol_start_date)
        
        try:
            pulldata = md.pulldata_yahoo(symbol, "5m", symbol_start_date, global_today)
            if pulldata is None:
                logger.warning("[main.py].TickData: No data retrieved for symbol: %s", symbol)
                continue
            
            logger.debug("[main.py].TickData: Sending data for symbol: %s", symbol)
            upload_response = requests.post(f"{api_url}/api/v1/tick", json=pulldata, headers=headers)
            upload_response.raise_for_status()
            logger.info("[main.py].TickData: Successfully processed symbol: %s. Response: %s", symbol, upload_response.json())
        except Exception as e:
            logger.error("[main.py].TickData: Error processing symbol %s: %s", symbol, e, exc_info=True)
            continue

def main() -> None:
    # Load environment variables from .env file
    load_dotenv()
    
    api_url = os.getenv("API_URL", "http://localhost:8080")
    api_key = os.getenv("API_KEY", "clover-secure-token-123")
    headers = {"X-API-KEY": api_key}

    logger.info("[main.py]: Start of program client")
    parentDir = os.getcwd()
    logger.info(f"[main.py]: Parent directory is {parentDir}")

    try:
        # Initialize dates and update GLOBAL_TODAY via API
        global_startdate, global_today = init_system_dates(api_url, headers)
        
        # Setup file logging
        setup_file_logging(parentDir, global_today)
        
        # Ingest EOD and Tick market data
        fetch_and_store_eod(api_url, headers, global_startdate, global_today)
        fetch_and_store_tick(api_url, headers, global_today)
        
    except Exception as e:
        logger.error(f"[main.py]: Unexpected error during main execution: {e}", exc_info=True)
        raise
    finally:
        logger.info("[main.py]: Program execution completed")

if __name__ == "__main__":
    main()
