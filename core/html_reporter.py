"""
Self-Contained Standalone HTML5 Executive Risk Audit Report Generator
"""
import html
from datetime import datetime, timezone
from typing import List, Dict, Any
from .models import AuditReport

def generate_html_report(report: AuditReport, trades: List[Dict[str, Any]] = None, title: str = "Trade History Risk Audit Report") -> str:
    """
    Renders a self-contained, publication-grade dark-themed HTML report.
    Zero external dependencies (CSS is embedded inline).
    """
    trades = trades or []
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Format numbers
    init_eq = f"${report.initial_equity:,.2f}"
    final_eq = f"${report.final_equity:,.2f}"
    net_pnl_val = report.realized_net_pnl
    net_pnl_class = "positive" if net_pnl_val >= 0 else "negative"
    net_pnl_str = f"{'+' if net_pnl_val >= 0 else ''}${net_pnl_val:,.2f}"
    
    gross_pnl_val = report.realized_gross_pnl
    gross_pnl_str = f"{'+' if gross_pnl_val >= 0 else ''}${gross_pnl_val:,.2f}"
    total_fees_str = f"${report.total_fees:,.2f}"
    
    win_rate_str = f"{report.win_rate_pct:.1f}%"
    pf_val = report.profit_factor
    pf_str = "∞" if pf_val == float("inf") else f"{pf_val:.2f}"
    
    dd_pct_str = f"{report.max_drawdown_pct:.2f}%"
    dd_usd_str = f"${report.max_drawdown_usd:,.2f}"
    conc_str = f"{report.max_exposure_concentration_pct:.1f}%"

    # Risk Flags
    flags_html = ""
    if report.invalid_position_flags:
        flags_items = "".join(f"<li>{html.escape(f)}</li>" for f in report.invalid_position_flags)
        flags_html = f"""
        <div class="alert-box alert-warning">
            <div class="alert-header">⚠️ Risk & Integrity Alerts Detected ({len(report.invalid_position_flags)})</div>
            <ul>{flags_items}</ul>
        </div>
        """
    else:
        flags_html = """
        <div class="alert-box alert-success">
            <div class="alert-header">✅ Clean Ledger Integrity Verified</div>
            <p>No short-selling, non-chronological executions, or lot matching anomalies detected.</p>
        </div>
        """

    # Trades Table
    trades_rows = ""
    for t in trades[:100]: # display up to 100 in report
        side_cls = "badge-buy" if t.get("side") == "BUY" else "badge-sell"
        trades_rows += f"""
        <tr>
            <td><code>{html.escape(str(t.get('order_id', '')))}</code></td>
            <td>{html.escape(str(t.get('timestamp', '')))}</td>
            <td><strong>{html.escape(str(t.get('symbol', '')))}</strong></td>
            <td><span class="badge {side_cls}">{html.escape(str(t.get('side', '')))}</span></td>
            <td class="text-right">${float(t.get('price', 0)):,.2f}</td>
            <td class="text-right">{float(t.get('quantity', 0)):.4f}</td>
            <td class="text-right">${float(t.get('fee', 0)):,.2f}</td>
        </tr>
        """

    css = """
    :root {
        --bg-primary: #0d1117;
        --bg-secondary: #161b22;
        --bg-card: #21262d;
        --border-color: #30363d;
        --text-primary: #f0f6fc;
        --text-secondary: #8b949e;
        --accent-blue: #58a6ff;
        --accent-green: #3fb950;
        --accent-red: #f85149;
        --accent-orange: #d29922;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        background-color: var(--bg-primary);
        color: var(--text-primary);
        padding: 32px 16px;
        line-height: 1.5;
    }
    .container {
        max-width: 1100px;
        margin: 0 auto;
    }
    .header {
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 24px;
        margin-bottom: 32px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        flex-wrap: wrap;
        gap: 16px;
    }
    .header h1 { font-size: 26px; font-weight: 700; color: #fff; }
    .header .meta { font-size: 13px; color: var(--text-secondary); }
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin-bottom: 32px;
    }
    .card {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 18px;
    }
    .card-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-secondary);
        margin-bottom: 8px;
    }
    .card-val {
        font-size: 24px;
        font-weight: 700;
        color: #fff;
    }
    .card-val.positive { color: var(--accent-green); }
    .card-val.negative { color: var(--accent-red); }
    .card-sub {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 4px;
    }
    .alert-box {
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 32px;
        border: 1px solid;
    }
    .alert-warning {
        background-color: rgba(210, 153, 34, 0.1);
        border-color: var(--accent-orange);
        color: #f1e05a;
    }
    .alert-warning ul { margin-left: 20px; margin-top: 8px; font-size: 14px; }
    .alert-success {
        background-color: rgba(63, 185, 80, 0.1);
        border-color: var(--accent-green);
        color: var(--accent-green);
    }
    .alert-header { font-weight: 600; font-size: 15px; }
    .section-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 16px;
        color: #fff;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 32px;
    }
    th, td {
        padding: 10px 14px;
        border-bottom: 1px solid var(--border-color);
        text-align: left;
    }
    th {
        background-color: var(--bg-card);
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
    }
    tr:last-child td { border-bottom: none; }
    .text-right { text-align: right; }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-buy { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
    .badge-sell { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
    .footer {
        border-top: 1px solid var(--border-color);
        padding-top: 20px;
        font-size: 12px;
        color: var(--text-secondary);
        display: flex;
        justify-content: space-between;
    }
    """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>{css}</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <h1>{html.escape(title)}</h1>
            <div class="meta">Deterministic FIFO Risk Audit Engine • High-Water Mark Drawdown Tracking</div>
        </div>
        <div class="meta text-right">
            Generated: <strong>{now_utc}</strong><br>
            Ledger Records: <strong>{report.total_trades}</strong>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-label">Net Realized PnL</div>
            <div class="card-val {net_pnl_class}">{net_pnl_str}</div>
            <div class="card-sub">Gross: {gross_pnl_str} | Fees: {total_fees_str}</div>
        </div>
        <div class="card">
            <div class="card-label">Ending Equity</div>
            <div class="card-val">{final_eq}</div>
            <div class="card-sub">Started at {init_eq}</div>
        </div>
        <div class="card">
            <div class="card-label">Maximum Drawdown</div>
            <div class="card-val negative">{dd_pct_str}</div>
            <div class="card-sub">Peak-to-Trough: {dd_usd_str}</div>
        </div>
        <div class="card">
            <div class="card-label">Win Rate & Factor</div>
            <div class="card-val">{win_rate_str}</div>
            <div class="card-sub">Profit Factor: {pf_str} ({report.winning_trades}W / {report.losing_trades}L)</div>
        </div>
        <div class="card">
            <div class="card-label">Max Asset Exposure</div>
            <div class="card-val">{conc_str}</div>
            <div class="card-sub">Peak single-asset concentration</div>
        </div>
    </div>

    {flags_html}

    <div class="section-title">Audited Trade History (First {min(len(trades), 100)} Records)</div>
    <table>
        <thead>
            <tr>
                <th>Order ID</th>
                <th>Timestamp</th>
                <th>Symbol</th>
                <th>Side</th>
                <th class="text-right">Price</th>
                <th class="text-right">Quantity</th>
                <th class="text-right">Fee</th>
            </tr>
        </thead>
        <tbody>
            {trades_rows}
        </tbody>
    </table>

    <div class="footer">
        <div>Paper Trade Risk Auditor v2.0.0 • Verified Deterministic Engine</div>
        <div>Settlement Facilitator: Base USDC (<code>eip155:8453</code>)</div>
    </div>
</div>
</body>
</html>
"""
    return html_content
