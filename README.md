# Paper Trade Risk Audit API & Engine

[![Tests](https://img.shields.io/badge/tests-10%20passed-brightgreen.svg)]()
[![Standard](https://img.shields.io/badge/accounting-FIFO-blue.svg)]()
[![Payment](https://img.shields.io/badge/x402-v2%20Compliant-orange.svg)]()
[![Network](https://img.shields.io/badge/network-Base%20(8453)-purple.svg)]()

A high-performance, deterministic trade ledger risk auditor and verification engine designed for quantitative hedge funds, algorithmic trading bots, and backtest analysis.

Built by **Taha Rafi** (`@taha-rafi`).

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
- **x402 v2 Payment Architecture:** Enterprise endpoints protected by standard HTTP 402 Payment Required headers on Base Mainnet (`eip155:8453`) USDC.

---

## Architecture & Mathematical Specification

### 1. FIFO Lot Matching
For each sell transaction with quantity $Q_{sell}$ at price $P_{sell}$, open buy lots $(P_{buy, i}, Q_{buy, i})$ are matched sequentially:

$$\text{Gross PnL} = \sum_{i} \min(Q_{remaining}, Q_{buy, i}) \times (P_{sell} - P_{buy, i})$$

### 2. High-Water Mark and Drawdown
$$\text{Equity}_t = \text{Cash}_t + \sum_{j} \text{Position}_j \times P_{latest, j}$$
$$\text{HWM}_t = \max_{0 \le s \le t} \text{Equity}_s$$
$$\text{Drawdown}_t = \frac{\text{HWM}_t - \text{Equity}_t}{\text{HWM}_t}$$

---

## API Endpoints

### 1. `GET /health`
Returns live service status, uptime, and authorized payment rails.
```bash
curl -X GET http://localhost:8088/health
```

### 2. `GET /example`
Returns a verified worked example input and expected audit output.
```bash
curl -X GET http://localhost:8088/example
```

### 3. `POST /audit` (Open Tier)
Deterministic audit of submitted JSON trade ledger.
```bash
curl -X POST http://localhost:8088/audit \
  -H "Content-Type: application/json" \
  -d '{
    "initial_equity": 10000.0,
    "trades": [
      {"timestamp": "2026-10-31T10:00:00Z", "symbol": "BTCUSDT", "side": "BUY", "price": 70000.0, "quantity": 0.1, "fee": 7.0},
      {"timestamp": "2026-10-31T12:00:00Z", "symbol": "BTCUSDT", "side": "SELL", "price": 72000.0, "quantity": 0.1, "fee": 7.2}
    ]
  }'
```

### 4. `POST /api/v2/audit` (x402 Enterprise Protected Tier)
Requires `X-Payment-Proof` header referencing a verified Base USDC transaction to `0x8e9FB1b87c06170993FB42916bAe7aC675c47675`.

---

## Running Tests
```bash
python -m unittest discover -s tests
```
10 comprehensive unit tests verifying FIFO matching, short-selling detection, drawdown calculation, and error handling.
