"""
Unit Tests for CSV Loader, Validation, and Standalone HTML Report Generation
"""
import unittest
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.csv_loader import parse_trades_csv
from core.auditor import RiskAuditor
from core.html_reporter import generate_html_report

class TestCSVAndReporting(unittest.TestCase):
    def test_valid_csv_string(self):
        csv_data = """timestamp,symbol,side,price,quantity,fee,order_id
2026-10-25T10:00:00Z,BTCUSDT,BUY,60000.0,0.1,1.0,ord_1
2026-10-25T12:00:00Z,BTCUSDT,SELL,62000.0,0.1,1.0,ord_2
"""
        trades, errors = parse_trades_csv(csv_data, is_content=True)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]["symbol"], "BTCUSDT")
        self.assertEqual(trades[0]["price"], 60000.0)

    def test_missing_header_columns(self):
        csv_data = """timestamp,side,price,quantity\n2026-10-25T10:00:00Z,BUY,60000.0,0.1"""
        trades, errors = parse_trades_csv(csv_data, is_content=True)
        self.assertEqual(len(trades), 0)
        self.assertTrue(any("Missing required columns" in e for e in errors))

    def test_malformed_numeric_and_negative_fee(self):
        csv_data = """timestamp,symbol,side,price,quantity,fee,order_id
2026-10-25T10:00:00Z,BTCUSDT,BUY,invalid_price,0.1,1.0,ord_1
2026-10-25T11:00:00Z,ETHUSDT,BUY,2500.0,-0.5,1.0,ord_2
2026-10-25T12:00:00Z,SOLUSDT,BUY,180.0,1.0,-5.0,ord_3
"""
        trades, errors = parse_trades_csv(csv_data, is_content=True)
        self.assertEqual(len(trades), 0)
        self.assertTrue(any("Invalid numeric price" in e for e in errors))
        self.assertTrue(any("Quantity must be > 0" in e for e in errors))
        self.assertTrue(any("Fee cannot be negative" in e for e in errors))

    def test_duplicate_order_id(self):
        csv_data = """timestamp,symbol,side,price,quantity,fee,order_id
2026-10-25T10:00:00Z,BTCUSDT,BUY,60000.0,0.1,1.0,ord_1
2026-10-25T11:00:00Z,BTCUSDT,SELL,61000.0,0.1,1.0,ord_1
"""
        trades, errors = parse_trades_csv(csv_data, is_content=True)
        self.assertEqual(len(trades), 1)
        self.assertTrue(any("Duplicate order_id" in e for e in errors))

    def test_html_report_rendering(self):
        csv_data = """timestamp,symbol,side,price,quantity,fee,order_id
2026-10-25T10:00:00Z,BTCUSDT,BUY,60000.0,0.1,1.0,ord_1
2026-10-25T12:00:00Z,BTCUSDT,SELL,62000.0,0.1,1.0,ord_2
"""
        trades, errors = parse_trades_csv(csv_data, is_content=True)
        auditor = RiskAuditor(initial_equity=5000.0)
        report = auditor.audit(trades)
        html = generate_html_report(report, trades=trades, title="Test Report")

        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Test Report", html)
        self.assertIn("$5,000.00", html)
        self.assertIn("ord_1", html)
        self.assertIn("ord_2", html)
        self.assertIn("Clean Ledger Integrity Verified", html)

if __name__ == "__main__":
    unittest.main()
