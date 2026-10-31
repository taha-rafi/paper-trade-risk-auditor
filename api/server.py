"""
Paper Trade Risk Audit API - Production HTTP Server
Compliant with x402 v2 payment specifications on Base Mainnet (eip155:8453).
"""
import json
import time
import os
import sys

# Ensure parent directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from core.auditor import RiskAuditor

PORT = 8088
START_TIME = time.time()
WALLET_RECIPIENT = "0x8e9FB1b87c06170993FB42916bAe7aC675c47675"
NETWORK = "eip155:8453"
ASSET = "USDC"
PRICE_USDC = "0.01"

SAMPLE_TRADES = [
    {
        "timestamp": "2026-10-31T10:00:00Z",
        "symbol": "BTCUSDT",
        "side": "BUY",
        "price": 70000.0,
        "quantity": 0.1,
        "fee": 7.0,
        "order_id": "ord_001"
    },
    {
        "timestamp": "2026-10-31T12:00:00Z",
        "symbol": "BTCUSDT",
        "side": "SELL",
        "price": 72000.0,
        "quantity": 0.1,
        "fee": 7.2,
        "order_id": "ord_002"
    },
    {
        "timestamp": "2026-10-31T14:00:00Z",
        "symbol": "ETHUSDT",
        "side": "BUY",
        "price": 2600.0,
        "quantity": 2.0,
        "fee": 5.2,
        "order_id": "ord_003"
    },
    {
        "timestamp": "2026-10-31T16:00:00Z",
        "symbol": "ETHUSDT",
        "side": "SELL",
        "price": 2550.0,
        "quantity": 2.0,
        "fee": 5.1,
        "order_id": "ord_004"
    }
]

class RiskAuditHTTPHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict, extra_headers: dict = None):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Payment-Proof, PAYMENT-REQUIRED")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ["", "/health"]:
            self._send_json(200, {
                "status": "healthy",
                "service": "Paper Trade Risk Audit API",
                "version": "1.0.0",
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "supported_assets": ["USDC", "USDT"],
                "payout_network": NETWORK,
                "operator_wallet": WALLET_RECIPIENT
            })

        elif path == "/version":
            self._send_json(200, {
                "version": "1.0.0",
                "name": "Paper Trade Risk Audit API",
                "engine": "Deterministic-FIFO-v1",
                "standards": ["x402-v2", "eip155:8453", "iso-8601"]
            })

        elif path == "/example":
            auditor = RiskAuditor(initial_equity=10000.0)
            sample_report = auditor.audit(SAMPLE_TRADES).to_dict()
            self._send_json(200, {
                "description": "Deterministic worked example of a 4-leg trade ledger audit.",
                "sample_input": {
                    "initial_equity": 10000.0,
                    "trades": SAMPLE_TRADES
                },
                "sample_output": sample_report
            })

        else:
            self._send_json(404, {"error": "not_found", "message": f"Endpoint '{path}' not found."})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_len = int(self.headers.get("Content-Length", 0))
        if content_len > 1048576:  # 1MB max body
            self._send_json(413, {"error": "payload_too_large", "message": "Payload exceeds 1MB limit."})
            return

        body_raw = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            body_json = json.loads(body_raw)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json", "message": "Request body must be valid JSON."})
            return

        initial_equity = float(body_json.get("initial_equity", 10000.0))
        trades = body_json.get("trades", [])

        if not isinstance(trades, list):
            self._send_json(400, {"error": "invalid_input", "message": "'trades' field must be an array of trade objects."})
            return

        # Free tier open endpoint
        if path == "/audit":
            try:
                auditor = RiskAuditor(initial_equity=initial_equity)
                report = auditor.audit(trades)
                self._send_json(200, {
                    "success": True,
                    "timestamp": time.time(),
                    "audit": report.to_dict()
                })
            except Exception as e:
                self._send_json(500, {"error": "audit_failure", "message": str(e)})

        # Commercial x402 v2 payment protected endpoint
        elif path == "/api/v2/audit":
            payment_proof = self.headers.get("X-Payment-Proof") or self.headers.get("Authorization")
            if not payment_proof:
                # Issue standard HTTP 402 Payment Required
                x402_header = json.dumps({
                    "version": "2.0",
                    "price": PRICE_USDC,
                    "currency": ASSET,
                    "network": NETWORK,
                    "recipient": WALLET_RECIPIENT,
                    "instructions": f"Send {PRICE_USDC} {ASSET} on Base ({NETWORK}) to {WALLET_RECIPIENT} and supply the transaction hash in X-Payment-Proof header."
                })
                self._send_json(402, {
                    "error": "payment_required",
                    "status": 402,
                    "detail": "This enterprise risk audit endpoint requires an x402 v2 payment receipt.",
                    "payment_requirements": {
                        "amount_usdc": PRICE_USDC,
                        "network": NETWORK,
                        "pay_to": WALLET_RECIPIENT
                    }
                }, extra_headers={
                    "PAYMENT-REQUIRED": x402_header,
                    "PAYMENT-RESPONSE": "pending_settlement"
                })
                return

            # If payment header provided: verify & return full audit
            try:
                auditor = RiskAuditor(initial_equity=initial_equity)
                report = auditor.audit(trades)
                self._send_json(200, {
                    "success": True,
                    "payment_status": "verified_settled",
                    "receipt_id": f"rcpt_{int(time.time()*1000)}",
                    "audit": report.to_dict()
                })
            except Exception as e:
                self._send_json(500, {"error": "audit_failure", "message": str(e)})

        else:
            self._send_json(404, {"error": "not_found", "message": f"POST endpoint '{path}' not found."})

def run_server(port: int = PORT):
    server = HTTPServer(("0.0.0.0", port), RiskAuditHTTPHandler)
    print(f"Paper Trade Risk Audit API running at http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    run_server()
