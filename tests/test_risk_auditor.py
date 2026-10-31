"""
Comprehensive Unit Test Suite for Paper Trade Risk Auditor
"""
import unittest
import sys
import os

# Ensure package root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.auditor import RiskAuditor
from core.models import Trade

class TestRiskAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = RiskAuditor(initial_equity=10000.0)

    def test_single_profitable_round_trip(self):
        trades = [
            {"timestamp": "2026-10-31T01:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 50000.0, "quantity": 0.1, "fee": 5.0, "order_id": "1"},
            {"timestamp": "2026-10-31T02:00:00Z", "symbol": "BTCUSDT", "side": "SELL", "price": 55000.0, "quantity": 0.1, "fee": 5.5, "order_id": "2"}
        ]
        report = self.auditor.audit(trades)
        self.assertEqual(report.total_trades, 2)
        self.assertEqual(report.winning_trades, 1)
        self.assertEqual(report.losing_trades, 0)
        self.assertAlmostEqual(report.realized_gross_pnl, 500.0)
        self.assertAlmostEqual(report.total_fees, 10.5)
        self.assertAlmostEqual(report.realized_net_pnl, 489.5)
        self.assertEqual(report.win_rate_pct, 100.0)
        self.assertEqual(len(report.invalid_position_flags), 0)

    def test_loss_making_trade(self):
        trades = [
            {"timestamp": "2026-10-31T01:00:00Z", "symbol": "ETHUSDT", "side": "BUY", "price": 2500.0, "quantity": 1.0, "fee": 2.5, "order_id": "1"},
            {"timestamp": "2026-10-31T02:00:00Z", "symbol": "ETHUSDT", "side": "SELL", "price": 2400.0, "quantity": 1.0, "fee": 2.4, "order_id": "2"}
        ]
        report = self.auditor.audit(trades)
        self.assertEqual(report.winning_trades, 0)
        self.assertEqual(report.losing_trades, 1)
        self.assertAlmostEqual(report.realized_gross_pnl, -100.0)
        self.assertAlmostEqual(report.realized_net_pnl, -104.9)
        self.assertEqual(report.profit_factor, 0.0)

    def test_multi_lot_fifo_partial_fills(self):
        # Lot 1: Buy 1.0 BTC @ 50,000
        # Lot 2: Buy 1.0 BTC @ 60,000
        # Sell 1.5 BTC @ 70,000
        # FIFO expects: 1.0 BTC matched @ 50k (profit = 20k) + 0.5 BTC matched @ 60k (profit = 5k) => Total gross = 25,000
        trades = [
            {"timestamp": "2026-10-31T01:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 50000.0, "quantity": 1.0, "fee": 0.0, "order_id": "b1"},
            {"timestamp": "2026-10-31T02:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 60000.0, "quantity": 1.0, "fee": 0.0, "order_id": "b2"},
            {"timestamp": "2026-10-31T03:00:00Z", "symbol": "BTCUSDT", "side": "SELL", "price": 70000.0, "quantity": 1.5, "fee": 0.0, "order_id": "s1"}
        ]
        auditor = RiskAuditor(initial_equity=200000.0)
        report = auditor.audit(trades)
        self.assertAlmostEqual(report.realized_gross_pnl, 25000.0)
        self.assertEqual(len(report.invalid_position_flags), 0)

    def test_short_selling_detection_flag(self):
        # Selling without open buy position
        trades = [
            {"timestamp": "2026-10-31T01:00:00Z", "symbol": "SOLUSDT", "side": "SELL", "price": 180.0, "quantity": 5.0, "fee": 1.0, "order_id": "illegal_sell"}
        ]
        report = self.auditor.audit(trades)
        self.assertTrue(any("Short-selling detected" in flag for flag in report.invalid_position_flags))

    def test_overselling_detection_flag(self):
        # Buy 1.0, sell 2.0
        trades = [
            {"timestamp": "2026-10-31T01:00:00Z", "symbol": "AVAXUSDT", "side": "BUY", "price": 25.0, "quantity": 1.0, "fee": 0.1, "order_id": "b1"},
            {"timestamp": "2026-10-31T02:00:00Z", "symbol": "AVAXUSDT", "side": "SELL", "price": 26.0, "quantity": 2.0, "fee": 0.2, "order_id": "s1"}
        ]
        report = self.auditor.audit(trades)
        self.assertTrue(any("oversold by 1.000000 AVAXUSDT" in flag for flag in report.invalid_position_flags))

    def test_non_chronological_timestamp_flag(self):
        trades = [
            {"timestamp": "2026-10-31T05:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 60000.0, "quantity": 0.1, "fee": 1.0, "order_id": "t1"},
            {"timestamp": "2026-10-31T04:00:00Z", "symbol": "BTCUSDT", "side": "SELL", "price": 61000.0, "quantity": 0.1, "fee": 1.0, "order_id": "t2"}
        ]
        report = self.auditor.audit(trades)
        self.assertTrue(any("Non-chronological timestamp" in flag for flag in report.invalid_position_flags))

    def test_invalid_payload_fields(self):
        trades = [
            {"timestamp": "2026-10-31T01:00:00Z", "symbol": "BTCUSDT", "side": "HOLD", "price": 60000.0, "quantity": 0.1, "fee": 1.0}, # Invalid side
            {"timestamp": "2026-10-31T02:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": -50.0, "quantity": 0.1, "fee": 1.0}, # Negative price
            {"timestamp": "2026-10-31T03:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 60000.0, "quantity": -1.0, "fee": 1.0} # Negative qty
        ]
        report = self.auditor.audit(trades)
        self.assertGreaterEqual(len(report.invalid_position_flags), 3)

    def test_drawdown_calculation(self):
        # Initial: 10,000
        # Trade 1: Gain 2,000 -> Equity 12,000 (HWM = 12,000)
        # Trade 2: Loss 3,000 -> Equity 9,000 (DD = 3,000 / 12,000 = 25%)
        # Trade 3: Gain 1,000 -> Equity 10,000
        trades = [
            {"timestamp": "2026-10-31T01:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 50000.0, "quantity": 0.2, "fee": 0.0, "order_id": "1"},
            {"timestamp": "2026-10-31T02:00:00Z", "symbol": "BTCUSDT", "side": "SELL", "price": 60000.0, "quantity": 0.2, "fee": 0.0, "order_id": "2"},
            {"timestamp": "2026-10-31T03:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 60000.0, "quantity": 0.2, "fee": 0.0, "order_id": "3"},
            {"timestamp": "2026-10-31T04:00:00Z", "symbol": "BTCUSDT", "side": "SELL", "price": 45000.0, "quantity": 0.2, "fee": 0.0, "order_id": "4"},
            {"timestamp": "2026-10-31T05:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 45000.0, "quantity": 0.2, "fee": 0.0, "order_id": "5"},
            {"timestamp": "2026-10-31T06:00:00Z", "symbol": "BTCUSDT", "side": "SELL", "price": 50000.0, "quantity": 0.2, "fee": 0.0, "order_id": "6"},
        ]
        report = self.auditor.audit(trades)
        self.assertAlmostEqual(report.max_drawdown_usd, 3000.0)
        self.assertAlmostEqual(report.max_drawdown_pct, 25.0)

    def test_exposure_concentration(self):
        # 10,000 equity, buy 0.1 BTC at 50,000 -> 5,000 value (50% concentration)
        trades = [
            {"timestamp": "2026-10-31T01:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 50000.0, "quantity": 0.1, "fee": 0.0, "order_id": "b1"}
        ]
        report = self.auditor.audit(trades)
        self.assertAlmostEqual(report.max_exposure_concentration_pct, 50.0)

    def test_initial_equity_negative_rejected(self):
        with self.assertRaises(ValueError):
            RiskAuditor(initial_equity=-1000.0)

if __name__ == "__main__":
    unittest.main()
