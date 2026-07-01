import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
import datetime
from contextlib import asynccontextmanager

# Load env variables
load_dotenv()
from enum import Enum
from fastapi import FastAPI, HTTPException, Security, Depends, Response, Path, Query
from fastapi.responses import FileResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import ProcessData as pd
import psycopg2

# Configure logger
logger = logging.getLogger(__name__)


# Database connection pool lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize connection pool
    pd.init_pool(minconn=1, maxconn=10)
    yield
    # Close connection pool
    pd.close_pool()


app = FastAPI(
    title="4leafclover Data Operations API",
    description="Exposes ProcessData.py functions and database SQL operations via REST endpoints.",
    version="1.0.0",
    lifespan=lifespan
)

# API Key Authentication
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is not configured. Please set it in your environment or .env file.")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """Validate the incoming X-API-KEY header against the configured environment variable."""
    if api_key != API_KEY:
        logger.warning("API key validation failed")
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key


class OutputFormat(str, Enum):
    DICT = "dict"
    JSON = "json"
    CSV = "csv"


# Request payload structures
class DataPayload(BaseModel):
    meta: Dict[str, Any]
    values: List[Dict[str, Any]]


@app.post("/api/v1/sys/init", dependencies=[Depends(verify_api_key)])
def sys_init() -> Dict[str, str]:
    """
    Initialize database date parameters:
    1. Update SysValue GLOBAL_TODAY to the current system date.
    2. Fetch and return GLOBAL_STARTDATE and GLOBAL_TODAY as YYYY-MM-DD strings.
    """
    logger.info("Initializing system dates in database")
    try:
        conn = pd.get_connection()
        cursor = conn.cursor()
        
        # Update GLOBAL_TODAY to current date
        cursor.execute("UPDATE SysValue SET DateValue = CURRENT_DATE WHERE Name = 'GLOBAL_TODAY'")
        conn.commit()
        
        # Retrieve startdate and today
        cursor.execute("SELECT Name, DateValue FROM SysValue WHERE Name IN ('GLOBAL_STARTDATE', 'GLOBAL_TODAY')")
        sys_values = cursor.fetchall()
        sys_dict = {row[0]: row[1] for row in sys_values}
        
        global_startdate_raw = sys_dict.get('GLOBAL_STARTDATE', '2025-01-01')
        global_today_raw = sys_dict.get('GLOBAL_TODAY', '2026-04-01')
        
        global_startdate = global_startdate_raw.strftime('%Y-%m-%d') if hasattr(global_startdate_raw, 'strftime') else str(global_startdate_raw).split()[0]
        global_today = global_today_raw.strftime('%Y-%m-%d') if hasattr(global_today_raw, 'strftime') else str(global_today_raw).split()[0]
        
        logger.info(f"System initialized. Start date: {global_startdate}, Today: {global_today}")
        return {
            "global_startdate": global_startdate,
            "global_today": global_today
        }
    except psycopg2.Error as e:
        logger.error(f"Database error during sys_init: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during sys_init: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            pd.put_connection(conn)


@app.get("/api/v1/eod/symbols", dependencies=[Depends(verify_api_key)])
def get_eod_symbols(
    global_startdate: datetime.date = Query(..., description="Global start date in YYYY-MM-DD format")
) -> List[Dict[str, str]]:
    """
    Retrieve symbols queue for EOD data pulling.
    Runs the EODData boundary date calculation query on Cloud SQL.
    """
    logger.info(f"Retrieving EOD symbols for startdate: {global_startdate}")
    try:
        conn = pd.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            select w.Symbol, 
            (case when max(e.Date) is NULL then CAST(%s AS date) 
            else GREATEST((max(e.Date) + INTERVAL '1 day')::date, CAST(%s AS date)) end) 
            from WatchList w left join EODData e on w.Symbol=e.Symbol group by w.Symbol
        """, (global_startdate, global_startdate))
        
        results = []
        for symbol, start_date in cursor.fetchall():
            start_date_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date).split()[0]
            results.append({
                "symbol": symbol,
                "start_date": start_date_str
            })
        return results
    except psycopg2.Error as e:
        logger.error(f"Database error retrieving EOD symbols: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            pd.put_connection(conn)


@app.get("/api/v1/tick/symbols", dependencies=[Depends(verify_api_key)])
def get_tick_symbols(
    global_today: datetime.date = Query(..., description="Global today date in YYYY-MM-DD format")
) -> List[Dict[str, str]]:
    """
    Retrieve symbols queue for Tick data pulling.
    Runs the TickData boundary date calculation query on Cloud SQL.
    """
    logger.info(f"Retrieving Tick symbols for today: {global_today}")
    try:
        conn = pd.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            select w.Symbol, 
            (case when max(e.Timestamp) is NULL then (CAST(%s AS date) - INTERVAL '7 days')::date 
            else GREATEST(max(e.Timestamp)::date, (CAST(%s AS date) - INTERVAL '7 days')::date) end) 
            from WatchList w left join TickData e on w.Symbol=e.Symbol group by w.Symbol
        """, (global_today, global_today))
        
        results = []
        for symbol, start_date in cursor.fetchall():
            start_date_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date).split()[0]
            results.append({
                "symbol": symbol,
                "start_date": start_date_str
            })
        return results
    except psycopg2.Error as e:
        logger.error(f"Database error retrieving Tick symbols: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            pd.put_connection(conn)


@app.post("/api/v1/eod", dependencies=[Depends(verify_api_key)])
def insert_eod(payload: DataPayload) -> Dict[str, Any]:
    """Insert EOD data payload into the EODData database table."""
    logger.info("Inserting EOD data")
    try:
        conn = pd.get_connection()
        rows = pd.insert_EODData(conn, payload.model_dump())
        return {"status": "success", "rows_inserted": rows}
    except Exception as e:
        logger.error(f"Error inserting EOD data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            pd.put_connection(conn)


@app.post("/api/v1/tick", dependencies=[Depends(verify_api_key)])
def insert_tick(payload: DataPayload) -> Dict[str, Any]:
    """Insert Tick data payload into the TickData database table."""
    logger.info("Inserting Tick data")
    try:
        conn = pd.get_connection()
        rows = pd.insert_Tickdata(conn, payload.model_dump())
        return {"status": "success", "rows_inserted": rows}
    except Exception as e:
        logger.error(f"Error inserting Tick data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            pd.put_connection(conn)


@app.get("/api/v1/eod/{symbol}", dependencies=[Depends(verify_api_key)])
def get_eod_data(
    symbol: str = Path(..., min_length=1, max_length=15, pattern="^[A-Z0-9.-]+$"),
    format: OutputFormat = OutputFormat.DICT
) -> Any:
    """Retrieve EOD charting dataset for a stock symbol."""
    logger.info(f"Generating EOD dataset for symbol {symbol} in format {format}")
    try:
        conn = pd.get_connection()
        data = pd.EODData_generate(conn, symbol, output_format=format.value)
        if not data:
            raise HTTPException(status_code=404, detail=f"No EOD data found for symbol {symbol}")
        
        if format == OutputFormat.CSV:
            return FileResponse(path=data, media_type="text/csv", filename=f"{symbol}_eod.csv")
        elif format == OutputFormat.JSON:
            return Response(content=data, media_type="application/json")
        else:
            return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating EOD data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            pd.put_connection(conn)


@app.get("/api/v1/tick/{symbol}", dependencies=[Depends(verify_api_key)])
def get_tick_data(
    symbol: str = Path(..., min_length=1, max_length=15, pattern="^[A-Z0-9.-]+$"),
    format: OutputFormat = OutputFormat.DICT
) -> Any:
    """Retrieve Tick charting dataset for a stock symbol."""
    logger.info(f"Generating Tick dataset for symbol {symbol} in format {format}")
    try:
        conn = pd.get_connection()
        data = pd.TickData_generate(conn, symbol, output_format=format.value)
        if not data:
            raise HTTPException(status_code=404, detail=f"No Tick data found for symbol {symbol}")
        
        if format == OutputFormat.CSV:
            return FileResponse(path=data, media_type="text/csv", filename=f"{symbol}_tick.csv")
        elif format == OutputFormat.JSON:
            return Response(content=data, media_type="application/json")
        else:
            return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Tick data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            pd.put_connection(conn)


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    uvicorn.run("4leafclover-dataops:app", host="0.0.0.0", port=8080, reload=True)
