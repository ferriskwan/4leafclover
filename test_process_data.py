import unittest
from unittest.mock import MagicMock, patch, mock_open
import datetime
import os
import json
import csv

# Import target module
import ProcessData

class TestProcessDataFormats(unittest.TestCase):
    def setUp(self):
        # Create a mock connection and cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        
        # Sample WatchList data
        self.watchlist_data = ("AAPL", "Tech", "Apple Inc.", "America/New_York")
        
        # Sample TickData query results
        # Columns: Interval, Timestamp, Open, High, Low, Close, Volume
        self.tick_rows = [
            ("5m", datetime.datetime(2026, 6, 29, 9, 30), 180.0, 181.0, 179.5, 180.5, 1000.0),
            ("5m", datetime.datetime(2026, 6, 29, 9, 35), 180.5, 182.0, 180.0, 181.5, 1200.0)
        ]
        
        # Sample EODData query results
        # Columns: Date, Date::timestamp as Timestamp, Open, High, Low, Close, Volume
        self.eod_rows = [
            (datetime.date(2026, 6, 26), datetime.datetime(2026, 6, 26, 0, 0), 178.0, 180.0, 177.5, 179.0, 500000.0),
            (datetime.date(2026, 6, 29), datetime.datetime(2026, 6, 29, 0, 0), 179.0, 181.5, 178.5, 180.5, 600000.0)
        ]

    def test_tickdata_generate_dict(self):
        # Configure cursor side effects
        self.mock_cursor.fetchone.return_value = self.watchlist_data
        self.mock_cursor.fetchall.return_value = self.tick_rows
        
        result = ProcessData.TickData_generate(self.mock_conn, "AAPL", output_format="dict")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["meta"]["symbol"], "AAPL")
        self.assertEqual(result["meta"]["watchlist"], "Tech")
        self.assertEqual(result["meta"]["interval"], "5m")
        self.assertEqual(result["meta"]["name"], "Apple Inc.")
        self.assertEqual(result["meta"]["timezone"], "America/New_York")
        self.assertEqual(len(result["values"]), 2)
        self.assertEqual(result["values"][0]["open"], 180.0)
        self.assertEqual(result["values"][1]["close"], 181.5)

    def test_tickdata_generate_json(self):
        self.mock_cursor.fetchone.return_value = self.watchlist_data
        self.mock_cursor.fetchall.return_value = self.tick_rows
        
        result_json = ProcessData.TickData_generate(self.mock_conn, "AAPL", output_format="json")
        
        self.assertIsInstance(result_json, str)
        # Parse it back to verify correctness
        parsed = json.loads(result_json)
        self.assertEqual(parsed["meta"]["symbol"], "AAPL")
        self.assertEqual(parsed["values"][0]["timestamp"], "2026-06-29T09:30:00")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_tickdata_generate_csv(self, mock_makedirs, mock_file):
        self.mock_cursor.fetchone.return_value = self.watchlist_data
        self.mock_cursor.fetchall.return_value = self.tick_rows
        
        # Test default path
        filepath = ProcessData.TickData_generate(self.mock_conn, "AAPL", output_format="csv")
        self.assertEqual(filepath, os.path.join("ProcessedData", "AAPL_tick.csv"))
        
        # Verify directory creation check and file open call
        mock_makedirs.assert_called_with("ProcessedData", exist_ok=True)
        mock_file.assert_called_once_with(filepath, 'w', newline='', encoding='utf-8')

    def test_eoddata_generate_dict(self):
        self.mock_cursor.fetchone.return_value = self.watchlist_data
        self.mock_cursor.fetchall.return_value = self.eod_rows
        
        result = ProcessData.EODData_generate(self.mock_conn, "AAPL", output_format="dict")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["meta"]["symbol"], "AAPL")
        self.assertEqual(result["meta"]["interval"], "1d")
        self.assertEqual(len(result["values"]), 2)
        self.assertEqual(result["values"][0]["date"], datetime.date(2026, 6, 26))
        self.assertEqual(result["values"][1]["timestamp"], datetime.datetime(2026, 6, 29, 0, 0))

    def test_eoddata_generate_json(self):
        self.mock_cursor.fetchone.return_value = self.watchlist_data
        self.mock_cursor.fetchall.return_value = self.eod_rows
        
        result_json = ProcessData.EODData_generate(self.mock_conn, "AAPL", output_format="json")
        
        self.assertIsInstance(result_json, str)
        parsed = json.loads(result_json)
        self.assertEqual(parsed["meta"]["symbol"], "AAPL")
        self.assertEqual(parsed["values"][0]["date"], "2026-06-26")
        self.assertEqual(parsed["values"][0]["timestamp"], "2026-06-26T00:00:00")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_eoddata_generate_csv(self, mock_makedirs, mock_file):
        self.mock_cursor.fetchone.return_value = self.watchlist_data
        self.mock_cursor.fetchall.return_value = self.eod_rows
        
        # Test custom path
        custom_path = "Custom/AAPL_eod_custom.csv"
        filepath = ProcessData.EODData_generate(self.mock_conn, "AAPL", output_format="csv", csv_path=custom_path)
        self.assertEqual(filepath, custom_path)
        
        mock_makedirs.assert_called_with("Custom", exist_ok=True)
        mock_file.assert_called_once_with(custom_path, 'w', newline='', encoding='utf-8')

if __name__ == '__main__':
    unittest.main()
