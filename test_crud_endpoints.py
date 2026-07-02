import unittest
from unittest.mock import MagicMock, patch
import datetime
from fastapi import HTTPException
import psycopg2

# Import target module
import importlib
dataops = importlib.import_module("4leafclover-dataops")

class TestCrudEndpoints(unittest.TestCase):
    
    # ----------------------------------------------------
    # Watchlist Endpoint Tests
    # ----------------------------------------------------
    
    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.get_watchlist")
    def test_get_watchlist(self, mock_get_wl, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        expected_records = [
            {"watchlistname": "Holdings", "symbol": "AAPL", "name": "Apple Inc.", "timezone": "America/New_York", "updatetimestamp": None}
        ]
        mock_get_wl.return_value = expected_records
        
        result = dataops.api_get_watchlist(watchlistname="Holdings", symbol="AAPL")
        
        mock_get_conn.assert_called_once()
        mock_get_wl.assert_called_once_with(mock_conn, watchlistname="Holdings", symbol="AAPL")
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result, expected_records)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.insert_watchlist")
    def test_post_watchlist_success(self, mock_insert_wl, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        payload = dataops.WatchListCreate(
            watchlistname="Holdings",
            symbol="AAPL",
            name="Apple Inc.",
            timezone="America/New_York"
        )
        expected_ret = {
            "watchlistname": "Holdings", "symbol": "AAPL", "name": "Apple Inc.", "timezone": "America/New_York", "updatetimestamp": datetime.datetime.now()
        }
        mock_insert_wl.return_value = expected_ret
        
        result = dataops.api_insert_watchlist(payload)
        
        mock_get_conn.assert_called_once()
        mock_insert_wl.assert_called_once_with(mock_conn, "Holdings", "AAPL", "Apple Inc.", "America/New_York")
        mock_conn.commit.assert_called_once()
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result, expected_ret)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.insert_watchlist")
    def test_post_watchlist_conflict(self, mock_insert_wl, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        payload = dataops.WatchListCreate(
            watchlistname="Holdings",
            symbol="AAPL",
            name="Apple Inc.",
            timezone="America/New_York"
        )
        # Mock database IntegrityError (UniqueViolation)
        mock_insert_wl.side_effect = psycopg2.IntegrityError("Duplicate key")
        
        with self.assertRaises(HTTPException) as ctx:
            dataops.api_insert_watchlist(payload)
            
        self.assertEqual(ctx.exception.status_code, 409)
        mock_get_conn.assert_called_once()
        mock_put_conn.assert_called_once_with(mock_conn)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.update_watchlist")
    def test_put_watchlist_success(self, mock_update_wl, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        payload = dataops.WatchListUpdate(name="Apple Corp.", timezone="America/New_York")
        expected_ret = {
            "watchlistname": "Holdings", "symbol": "AAPL", "name": "Apple Corp.", "timezone": "America/New_York", "updatetimestamp": None
        }
        mock_update_wl.return_value = expected_ret
        
        result = dataops.api_update_watchlist(watchlistname="Holdings", symbol="AAPL", payload=payload)
        
        mock_get_conn.assert_called_once()
        mock_update_wl.assert_called_once_with(mock_conn, "Holdings", "AAPL", name="Apple Corp.", timezone="America/New_York")
        mock_conn.commit.assert_called_once()
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result, expected_ret)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.update_watchlist")
    def test_put_watchlist_not_found(self, mock_update_wl, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_update_wl.return_value = None
        
        with self.assertRaises(HTTPException) as ctx:
            dataops.api_update_watchlist(watchlistname="Holdings", symbol="AAPL", payload=None)
            
        self.assertEqual(ctx.exception.status_code, 404)
        mock_put_conn.assert_called_once_with(mock_conn)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.delete_watchlist")
    def test_delete_watchlist_success(self, mock_delete_wl, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_delete_wl.return_value = True
        
        result = dataops.api_delete_watchlist(watchlistname="Holdings", symbol="AAPL")
        
        mock_get_conn.assert_called_once()
        mock_delete_wl.assert_called_once_with(mock_conn, "Holdings", "AAPL")
        mock_conn.commit.assert_called_once()
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result["status"], "success")

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.delete_watchlist")
    def test_delete_watchlist_not_found(self, mock_delete_wl, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_delete_wl.return_value = False
        
        with self.assertRaises(HTTPException) as ctx:
            dataops.api_delete_watchlist(watchlistname="Holdings", symbol="AAPL")
            
        self.assertEqual(ctx.exception.status_code, 404)
        mock_put_conn.assert_called_once_with(mock_conn)

    # ----------------------------------------------------
    # Trade Endpoint Tests
    # ----------------------------------------------------

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.get_trades")
    def test_get_trades(self, mock_get_tr, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        expected_records = [
            {"id": 1, "symbol": "AAPL", "buysell": "B", "tradedate": datetime.datetime.now(), "investment": True, "price": 180.0, "quantity": 10.0, "remarks": None}
        ]
        mock_get_tr.return_value = expected_records
        
        result = dataops.api_get_trades(symbol="AAPL", buysell="B")
        
        mock_get_conn.assert_called_once()
        mock_get_tr.assert_called_once_with(mock_conn, symbol="AAPL", buysell="B")
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result, expected_records)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.watchlist_symbol_exists")
    @patch("ProcessData.insert_trade")
    def test_post_trade_success(self, mock_insert_tr, mock_exists, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = True  # Enforce symbol exists
        
        tdate = datetime.datetime.now()
        payload = dataops.TradeCreate(
            symbol="AAPL",
            buysell="B",
            tradedate=tdate,
            investment=True,
            price=180.0,
            quantity=10.0,
            remarks="Test Trade"
        )
        
        expected_ret = {
            "id": 100, "symbol": "AAPL", "buysell": "B", "tradedate": tdate, "investment": True, "price": 180.0, "quantity": 10.0, "remarks": "Test Trade"
        }
        mock_insert_tr.return_value = expected_ret
        
        result = dataops.api_insert_trade(payload)
        
        mock_get_conn.assert_called_once()
        mock_exists.assert_called_once_with(mock_conn, "AAPL")
        mock_insert_tr.assert_called_once_with(mock_conn, "AAPL", "B", tdate, True, 180.0, 10.0, "Test Trade")
        mock_conn.commit.assert_called_once()
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result, expected_ret)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.watchlist_symbol_exists")
    def test_post_trade_symbol_not_in_watchlist(self, mock_exists, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = False  # Symbol doesn't exist
        
        payload = dataops.TradeCreate(
            symbol="INVALID",
            buysell="S",
            tradedate=datetime.datetime.now(),
            investment=False,
            price=10.0,
            quantity=5.0,
            remarks=None
        )
        
        with self.assertRaises(HTTPException) as ctx:
            dataops.api_insert_trade(payload)
            
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("must exist in the Watchlist", ctx.exception.detail)
        mock_get_conn.assert_called_once()
        mock_exists.assert_called_once_with(mock_conn, "INVALID")
        mock_put_conn.assert_called_once_with(mock_conn)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.watchlist_symbol_exists")
    @patch("ProcessData.update_trade")
    def test_put_trade_success(self, mock_update_tr, mock_exists, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = True  # New symbol exists
        
        payload = dataops.TradeUpdate(symbol="AAPL", price=190.0)
        expected_ret = {
            "id": 5, "symbol": "AAPL", "buysell": "B", "tradedate": None, "investment": True, "price": 190.0, "quantity": 10.0, "remarks": None
        }
        mock_update_tr.return_value = expected_ret
        
        result = dataops.api_update_trade(id=5, payload=payload)
        
        mock_get_conn.assert_called_once()
        mock_exists.assert_called_once_with(mock_conn, "AAPL")
        mock_update_tr.assert_called_once_with(
            mock_conn, 5, symbol="AAPL", buysell=None, tradedate=None, investment=None, price=190.0, quantity=None, remarks=None
        )
        mock_conn.commit.assert_called_once()
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result, expected_ret)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.watchlist_symbol_exists")
    def test_put_trade_invalid_symbol(self, mock_exists, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = False
        
        payload = dataops.TradeUpdate(symbol="BADSYM")
        
        with self.assertRaises(HTTPException) as ctx:
            dataops.api_update_trade(id=5, payload=payload)
            
        self.assertEqual(ctx.exception.status_code, 400)
        mock_put_conn.assert_called_once_with(mock_conn)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.delete_trade")
    def test_delete_trade_success(self, mock_delete_tr, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_delete_tr.return_value = True
        
        result = dataops.api_delete_trade(id=10)
        
        mock_get_conn.assert_called_once()
        mock_delete_tr.assert_called_once_with(mock_conn, 10)
        mock_conn.commit.assert_called_once()
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result["status"], "success")

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.delete_trade")
    def test_delete_trade_not_found(self, mock_delete_tr, mock_put_conn, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_delete_tr.return_value = False
        
        with self.assertRaises(HTTPException) as ctx:
            dataops.api_delete_trade(id=10)
            
        self.assertEqual(ctx.exception.status_code, 404)
        mock_put_conn.assert_called_once_with(mock_conn)

if __name__ == "__main__":
    unittest.main()
