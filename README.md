# Paper Trade Risk Audit API & Engine

[![Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen.svg)]()
[![Standard](https://img.shields.io/badge/accounting-FIFO-blue.svg)]()
[![CLI](https://img.shields.io/badge/cli-CSV%20to%20HTML%20Report-orange.svg)]()
[![Network](https://img.shields.io/badge/network-Base%20(8453)-purple.svg)]()

A high-performance, deterministic trade ledger risk auditor and verification engine designed for quantitative funds, algorithmic trading bots, and backtest analysis.

Built by **Taha Rafi** (`@taha-rafi`).

---

## What's New in v2.1.0
- **One-Command CSV-to-HTML Workflow:** Ingest any standard trade history CSV file and generate a publication-grade, self-contained HTML5 dark-theme executive audit report.
- **Strict Ingestion Validation:** Schema enforcement, empty file guards, malformed numeric value checks, duplicate order ID detection, and non-chronological execution alerts.
- **Zero-Dependency Reports:** Embeds all styling inline; zero external CDN dependencies, fully offline & firewall safe.

---

## Quickstart: CLI Audit Workflow

### 1. Ingest CSV Ledger and Generate Executive Reports
```bash
python cli.py audit sample_trades.csv --equity 10000 --html audit_report.html --json audit_report.json
```

Output:
```text
[*] Ingesting CSV trade ledger from: sample_trades.csv
[+] Successfully validated 12 trade records.
[*] Running FIFO cost-basis audit with initial equity of $10,000.00...

==================================================
          AUDIT EXECUTIVE SUMMARY
==================================================
Total Trades Audited:        12
Initial Equity:              $10,000.00
Final Equity:                $10,676.69
Net Realized PnL:            $676.69
Total Execution Fees:        $13.31
Win Rate:                    85.7% (6W / 1L)
Profit Factor:               20.71
Max Drawdown:                1.08% ($111.77)
Max Single-Asset Exposure:   65.0%
Integrity Flags Detected:    0
==================================================

[+] Standalone HTML report generated: audit_report.html
[+] Raw JSON metrics exported: audit_report.json
[+] Audit completed successfully.
```

---

## Features
- **Deterministic FIFO Cost-Basis Matching:** Multi-lot partial fills with exact lot depletion and cost basis attribution.
- **Fee-Adjusted Accounting:** Separate tracking of Gross Realized P&L, cumulative exchange fees, and Net Realized P&L.
- **Mark-to-Market Equity Curve & Maximum Drawdown:** Peak-to-trough high-water mark tracking in both dollar and percentage terms.
- **Exposure Concentration Analysis:** Real-time monitoring of single-asset portfolio capital allocation.
- **Anomaly & Violation Guardrails:**
  - Short-selling / overselling detection.
  - Non-chronological timestamp validation.
  - Negative or zero price/quantity payload validation.
- **x402 Payment Architecture:** Enterprise endpoints protected by standard HTTP 402 Payment Required headers on Base Mainnet (`eip155:8453`) USDC.

---

## Commercial Fixed-Price Development Services

I offer fixed-price Python trading tools, trade ledger auditing, and API integrations:

| Service | Price | Deliverables |
|---|---|---|
| **Trade History Risk Audit** | **$35 USDC** | Full FIFO audit of your supplied CSV ledger, net P&L, cumulative fee accounting, peak drawdown analysis, exposure concentration flags, and a self-contained executive HTML report. |
| **Paper Trading Bot Setup** | **$25 USDC** | Complete local setup of a simulated trading engine with public Binance live market data feed, SMA crossover strategy, and 2% risk stop-loss. |
| **Python API Integration & Fix** | **$45 USDC** | Turnkey bug fix, data pipeline integration, or REST API endpoint with unit test suite. |

Payments accepted directly via USDC on Base Mainnet (`0x8e9FB1b87c06170993FB42916bAe7aC675c47675`) or via x402 on-chain escrow.

---

## Running Tests
```bash
python -m unittest discover -s tests
```
15 unit tests verifying FIFO matching, short-selling detection, drawdown calculation, CSV schema validation, and HTML report rendering.
