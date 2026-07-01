import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Response
from fastapi.responses import FileResponse
import inspect
import datetime

# Import the module under test using importlib due to hyphen in name
import importlib
dataops = importlib.import_module("4leafclover-dataops")

class TestDataopsEndpoints(unittest.TestCase):
    
    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.EODData_generate")
    def test_get_eod_data_dict(self, mock_eod_generate, mock_put_conn, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        expected_dict = {"meta": {"symbol": "AAPL"}, "values": []}
        mock_eod_generate.return_value = expected_dict
        
        # Call function
        result = dataops.get_eod_data("AAPL", format=dataops.OutputFormat.DICT)
        
        # Assertions
        mock_get_conn.assert_called_once()
        mock_eod_generate.assert_called_once_with(mock_conn, "AAPL", output_format="dict")
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result, expected_dict)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.EODData_generate")
    def test_get_eod_data_json(self, mock_eod_generate, mock_put_conn, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        expected_json_str = '{"meta": {"symbol": "AAPL"}}'
        mock_eod_generate.return_value = expected_json_str
        
        # Call function
        result = dataops.get_eod_data("AAPL", format=dataops.OutputFormat.JSON)
        
        # Assertions
        mock_get_conn.assert_called_once()
        mock_eod_generate.assert_called_once_with(mock_conn, "AAPL", output_format="json")
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertIsInstance(result, Response)
        self.assertEqual(result.body, expected_json_str.encode("utf-8"))
        self.assertEqual(result.media_type, "application/json")

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.EODData_generate")
    def test_get_eod_data_csv(self, mock_eod_generate, mock_put_conn, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        expected_csv_path = "ProcessedData/AAPL_eod.csv"
        mock_eod_generate.return_value = expected_csv_path
        
        # Call function
        result = dataops.get_eod_data("AAPL", format=dataops.OutputFormat.CSV)
        
        # Assertions
        mock_get_conn.assert_called_once()
        mock_eod_generate.assert_called_once_with(mock_conn, "AAPL", output_format="csv")
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertIsInstance(result, FileResponse)
        self.assertEqual(result.path, expected_csv_path)
        self.assertEqual(result.media_type, "text/csv")

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.TickData_generate")
    def test_get_tick_data_dict(self, mock_tick_generate, mock_put_conn, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        expected_dict = {"meta": {"symbol": "AAPL"}, "values": []}
        mock_tick_generate.return_value = expected_dict
        
        # Call function
        result = dataops.get_tick_data("AAPL", format=dataops.OutputFormat.DICT)
        
        # Assertions
        mock_get_conn.assert_called_once()
        mock_tick_generate.assert_called_once_with(mock_conn, "AAPL", output_format="dict")
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertEqual(result, expected_dict)

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.TickData_generate")
    def test_get_tick_data_json(self, mock_tick_generate, mock_put_conn, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        expected_json_str = '{"meta": {"symbol": "AAPL"}}'
        mock_tick_generate.return_value = expected_json_str
        
        # Call function
        result = dataops.get_tick_data("AAPL", format=dataops.OutputFormat.JSON)
        
        # Assertions
        mock_get_conn.assert_called_once()
        mock_tick_generate.assert_called_once_with(mock_conn, "AAPL", output_format="json")
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertIsInstance(result, Response)
        self.assertEqual(result.body, expected_json_str.encode("utf-8"))
        self.assertEqual(result.media_type, "application/json")

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.TickData_generate")
    def test_get_tick_data_csv(self, mock_tick_generate, mock_put_conn, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        expected_csv_path = "ProcessedData/AAPL_tick.csv"
        mock_tick_generate.return_value = expected_csv_path
        
        # Call function
        result = dataops.get_tick_data("AAPL", format=dataops.OutputFormat.CSV)
        
        # Assertions
        mock_get_conn.assert_called_once()
        mock_tick_generate.assert_called_once_with(mock_conn, "AAPL", output_format="csv")
        mock_put_conn.assert_called_once_with(mock_conn)
        self.assertIsInstance(result, FileResponse)
        self.assertEqual(result.path, expected_csv_path)
        self.assertEqual(result.media_type, "text/csv")

    @patch("ProcessData.get_connection")
    @patch("ProcessData.put_connection")
    @patch("ProcessData.EODData_generate")
    def test_get_eod_data_not_found(self, mock_eod_generate, mock_put_conn, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_eod_generate.return_value = None
        
        # Assert raise HTTPException 404
        with self.assertRaises(HTTPException) as ctx:
            dataops.get_eod_data("AAPL")
        
        self.assertEqual(ctx.exception.status_code, 404)
        mock_get_conn.assert_called_once()
        mock_put_conn.assert_called_once_with(mock_conn)

    def test_endpoint_signature_validation(self):
        # Check that Path validations are configured on endpoints
        for func in [dataops.get_eod_data, dataops.get_tick_data]:
            sig = inspect.signature(func)
            self.assertIn("symbol", sig.parameters)
            symbol_param = sig.parameters["symbol"]
            self.assertEqual(symbol_param.annotation, str)
            # Ensure it has Path default object
            self.assertIsNotNone(symbol_param.default)
            self.assertEqual(symbol_param.default.__class__.__name__, "Path")
            metadata = symbol_param.default.metadata
            min_len = next((m.min_length for m in metadata if hasattr(m, 'min_length')), None)
            max_len = next((m.max_length for m in metadata if hasattr(m, 'max_length')), None)
            self.assertEqual(min_len, 1)
            self.assertEqual(max_len, 15)

        # Check date parsing on symbols endpoint query params
        for func in [dataops.get_eod_symbols, dataops.get_tick_symbols]:
            sig = inspect.signature(func)
            param_name = "global_startdate" if "global_startdate" in sig.parameters else "global_today"
            param = sig.parameters[param_name]
            self.assertEqual(param.annotation, datetime.date)

if __name__ == "__main__":
    import datetime
    unittest.main()
