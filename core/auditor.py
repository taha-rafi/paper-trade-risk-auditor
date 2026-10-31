"""
Deterministic FIFO Trade Ledger Risk Auditor
"""
from datetime import datetime
from typing import List, Dict, Any, Tuple
from .models import Trade, AuditReport

class RiskAuditor:
    def __init__(self, initial_equity: float = 10000.0):
        if initial_equity <= 0:
            raise ValueError("Initial equity must be positive.")
        self.initial_equity = float(initial_equity)

    def audit(self, trades_data: List[Dict[str, Any]]) -> AuditReport:
        trades: List[Trade] = []
        invalid_flags: List[str] = []

        # 1. Validation and Parse
        last_dt = None
        for idx, t_raw in enumerate(trades_data):
            try:
                t = Trade(
                    timestamp=str(t_raw.get("timestamp", "")),
                    symbol=str(t_raw.get("symbol", "")).upper(),
                    side=str(t_raw.get("side", "")).upper(),
                    price=float(t_raw.get("price", 0.0)),
                    quantity=float(t_raw.get("quantity", 0.0)),
                    fee=float(t_raw.get("fee", 0.0)),
                    order_id=str(t_raw.get("order_id", f"trade_{idx}"))
                )
            except (ValueError, TypeError) as e:
                invalid_flags.append(f"Trade index {idx}: Malformed trade payload ({e})")
                continue

            errs = t.validate()
            if errs:
                invalid_flags.extend([f"Trade index {idx} ({t.order_id}): {err}" for err in errs])
                continue

            # Verify Chronological Order
            try:
                dt = datetime.fromisoformat(t.timestamp.replace("Z", "+00:00"))
                if last_dt and dt < last_dt:
                    invalid_flags.append(
                        f"Trade index {idx} ({t.order_id}): Non-chronological timestamp {t.timestamp} < {last_dt.isoformat()}"
                    )
                last_dt = dt
            except ValueError:
                invalid_flags.append(f"Trade index {idx} ({t.order_id}): Invalid ISO 8601 timestamp format")

            trades.append(t)

        # 2. FIFO PnL, Fees & Equity Curve
        cash_balance = self.initial_equity
        open_positions: Dict[str, List[Tuple[float, float]]] = {} # symbol -> list of [buy_price, remaining_qty]
        closed_trades_pnl: List[float] = []
        total_fees = 0.0
        latest_prices: Dict[str, float] = {}

        equity_curve: List[float] = [self.initial_equity]
        max_concentration = 0.0

        for t in trades:
            total_fees += t.fee
            latest_prices[t.symbol] = t.price

            if t.side == "BUY":
                cost = (t.price * t.quantity) + t.fee
                cash_balance -= cost
                if t.symbol not in open_positions:
                    open_positions[t.symbol] = []
                open_positions[t.symbol].append([t.price, t.quantity])

            elif t.side == "SELL":
                revenue = (t.price * t.quantity) - t.fee
                cash_balance += revenue
                
                # FIFO matching against open buys
                qty_to_match = t.quantity
                matched_cost_basis = 0.0
                actual_matched_qty = 0.0

                symbol_buys = open_positions.get(t.symbol, [])
                while symbol_buys and qty_to_match > 1e-9:
                    buy_price, avail_qty = symbol_buys[0]
                    fill_qty = min(avail_qty, qty_to_match)
                    matched_cost_basis += fill_qty * buy_price
                    actual_matched_qty += fill_qty
                    qty_to_match -= fill_qty
                    
                    if avail_qty <= fill_qty + 1e-9:
                        symbol_buys.pop(0)
                    else:
                        symbol_buys[0] = [buy_price, avail_qty - fill_qty]

                if qty_to_match > 1e-9:
                    invalid_flags.append(
                        f"Trade {t.order_id}: Short-selling detected / oversold by {qty_to_match:.6f} {t.symbol}"
                    )
                
                if actual_matched_qty > 0:
                    realized_trade_pnl = (t.price * actual_matched_qty) - matched_cost_basis
                    closed_trades_pnl.append(realized_trade_pnl)

            # Mark to market equity
            portfolio_asset_value = sum(
                sum(q for _, q in lots) * latest_prices.get(sym, 0.0)
                for sym, lots in open_positions.items()
            )
            current_equity = cash_balance + portfolio_asset_value
            equity_curve.append(current_equity)

            # Concentration calculation: max single asset exposure / equity
            if current_equity > 0:
                for sym, lots in open_positions.items():
                    asset_val = sum(q for _, q in lots) * latest_prices.get(sym, 0.0)
                    concentration = (asset_val / current_equity) * 100.0
                    if concentration > max_concentration:
                        max_concentration = concentration

        # 3. High-Water Mark and Max Drawdown
        high_water_mark = self.initial_equity
        max_drawdown_usd = 0.0
        max_drawdown_pct = 0.0

        for eq in equity_curve:
            if eq > high_water_mark:
                high_water_mark = eq
            dd_usd = high_water_mark - eq
            dd_pct = (dd_usd / high_water_mark * 100.0) if high_water_mark > 0 else 0.0

            if dd_usd > max_drawdown_usd:
                max_drawdown_usd = dd_usd
            if dd_pct > max_drawdown_pct:
                max_drawdown_pct = dd_pct

        # 4. Performance Metrics
        realized_gross = sum(closed_trades_pnl)
        realized_net = realized_gross - total_fees
        final_equity = equity_curve[-1] if equity_curve else self.initial_equity

        winning = [p for p in closed_trades_pnl if p > 0]
        losing = [p for p in closed_trades_pnl if p < 0]
        total_closed = len(closed_trades_pnl)
        win_rate = (len(winning) / total_closed * 100.0) if total_closed > 0 else 0.0

        gross_profits = sum(winning)
        gross_losses = abs(sum(losing))
        if gross_losses > 0:
            profit_factor = round(gross_profits / gross_losses, 4)
        elif gross_profits > 0:
            profit_factor = float("inf")
        else:
            profit_factor = 0.0

        assumptions = {
            "accounting_method": "FIFO (First-In, First-Out)",
            "quote_currency": "USD/USDT",
            "fee_handling": "Deducted from cash balance per transaction; net P&L incorporates cumulative fees",
            "mark_to_market_pricing": "Last observed executed trade price per asset",
            "short_selling_policy": "Strictly prohibited; flagged as invalid position anomaly",
            "drawdown_basis": "Peak-to-trough mark-to-market equity curve"
        }

        return AuditReport(
            initial_equity=round(self.initial_equity, 2),
            final_equity=round(final_equity, 2),
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate_pct=round(win_rate, 2),
            realized_gross_pnl=round(realized_gross, 4),
            total_fees=round(total_fees, 4),
            realized_net_pnl=round(realized_net, 4),
            max_drawdown_pct=round(max_drawdown_pct, 2),
            max_drawdown_usd=round(max_drawdown_usd, 2),
            profit_factor=profit_factor,
            max_exposure_concentration_pct=round(max_concentration, 2),
            invalid_position_flags=invalid_flags,
            calculation_assumptions=assumptions
        )
