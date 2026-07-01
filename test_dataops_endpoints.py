import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Response
from fastapi.responses import FileResponse

# Import the module under test using importlib due to hyphen in name
import importlib
dataops = importlib.import_module("4leafclover-dataops")

class TestDataopsEndpoints(unittest.TestCase):
    
    @patch("ProcessData.connect_clover")
    @patch("ProcessData.EODData_generate")
    def test_get_eod_data_dict(self, mock_eod_generate, mock_connect):
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        expected_dict = {"meta": {"symbol": "AAPL"}, "values": []}
        mock_eod_generate.return_value = expected_dict
        
        # Call function
        result = dataops.get_eod_data("AAPL", format=dataops.OutputFormat.DICT)
        
        # Assertions
        mock_eod_generate.assert_called_once_with(mock_conn, "AAPL", output_format="dict")
        self.assertEqual(result, expected_dict)
        mock_conn.close.assert_called_once()

    @patch("ProcessData.connect_clover")
    @patch("ProcessData.EODData_generate")
    def test_get_eod_data_json(self, mock_eod_generate, mock_connect):
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        expected_json_str = '{"meta": {"symbol": "AAPL"}}'
        mock_eod_generate.return_value = expected_json_str
        
        # Call function
        result = dataops.get_eod_data("AAPL", format=dataops.OutputFormat.JSON)
        
        # Assertions
        mock_eod_generate.assert_called_once_with(mock_conn, "AAPL", output_format="json")
        self.assertIsInstance(result, Response)
        self.assertEqual(result.body, expected_json_str.encode("utf-8"))
        self.assertEqual(result.media_type, "application/json")
        mock_conn.close.assert_called_once()

    @patch("ProcessData.connect_clover")
    @patch("ProcessData.EODData_generate")
    def test_get_eod_data_csv(self, mock_eod_generate, mock_connect):
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        expected_csv_path = "ProcessedData/AAPL_eod.csv"
        mock_eod_generate.return_value = expected_csv_path
        
        # Call function
        result = dataops.get_eod_data("AAPL", format=dataops.OutputFormat.CSV)
        
        # Assertions
        mock_eod_generate.assert_called_once_with(mock_conn, "AAPL", output_format="csv")
        self.assertIsInstance(result, FileResponse)
        self.assertEqual(result.path, expected_csv_path)
        self.assertEqual(result.media_type, "text/csv")
        mock_conn.close.assert_called_once()

    @patch("ProcessData.connect_clover")
    @patch("ProcessData.TickData_generate")
    def test_get_tick_data_dict(self, mock_tick_generate, mock_connect):
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        expected_dict = {"meta": {"symbol": "AAPL"}, "values": []}
        mock_tick_generate.return_value = expected_dict
        
        # Call function
        result = dataops.get_tick_data("AAPL", format=dataops.OutputFormat.DICT)
        
        # Assertions
        mock_tick_generate.assert_called_once_with(mock_conn, "AAPL", output_format="dict")
        self.assertEqual(result, expected_dict)
        mock_conn.close.assert_called_once()

    @patch("ProcessData.connect_clover")
    @patch("ProcessData.TickData_generate")
    def test_get_tick_data_json(self, mock_tick_generate, mock_connect):
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        expected_json_str = '{"meta": {"symbol": "AAPL"}}'
        mock_tick_generate.return_value = expected_json_str
        
        # Call function
        result = dataops.get_tick_data("AAPL", format=dataops.OutputFormat.JSON)
        
        # Assertions
        mock_tick_generate.assert_called_once_with(mock_conn, "AAPL", output_format="json")
        self.assertIsInstance(result, Response)
        self.assertEqual(result.body, expected_json_str.encode("utf-8"))
        self.assertEqual(result.media_type, "application/json")
        mock_conn.close.assert_called_once()

    @patch("ProcessData.connect_clover")
    @patch("ProcessData.TickData_generate")
    def test_get_tick_data_csv(self, mock_tick_generate, mock_connect):
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        expected_csv_path = "ProcessedData/AAPL_tick.csv"
        mock_tick_generate.return_value = expected_csv_path
        
        # Call function
        result = dataops.get_tick_data("AAPL", format=dataops.OutputFormat.CSV)
        
        # Assertions
        mock_tick_generate.assert_called_once_with(mock_conn, "AAPL", output_format="csv")
        self.assertIsInstance(result, FileResponse)
        self.assertEqual(result.path, expected_csv_path)
        self.assertEqual(result.media_type, "text/csv")
        mock_conn.close.assert_called_once()

    @patch("ProcessData.connect_clover")
    @patch("ProcessData.EODData_generate")
    def test_get_eod_data_not_found(self, mock_eod_generate, mock_connect):
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_eod_generate.return_value = None
        
        # Assert raise HTTPException 404
        with self.assertRaises(HTTPException) as ctx:
            dataops.get_eod_data("AAPL")
        
        self.assertEqual(ctx.exception.status_code, 404)
        mock_conn.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()
