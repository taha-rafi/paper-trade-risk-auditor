"""
CSV Trade Ledger Ingestion and Strict Schema Validation
"""
import csv
import io
import os
from typing import List, Dict, Any, Tuple

REQUIRED_COLUMNS = ["timestamp", "symbol", "side", "price", "quantity"]
OPTIONAL_COLUMNS = ["fee", "order_id"]

class CSVValidationError(Exception):
    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors

def parse_trades_csv(file_path_or_content: str, is_content: bool = False) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Parses a CSV file or CSV string into a validated list of trade dictionaries.
    Returns (trades, errors).
    """
    errors: List[str] = []
    trades: List[Dict[str, Any]] = []

    if is_content:
        f = io.StringIO(file_path_or_content)
    else:
        if not os.path.exists(file_path_or_content):
            return [], [f"File not found: {file_path_or_content}"]
        if os.path.getsize(file_path_or_content) == 0:
            return [], ["CSV file is completely empty"]
        f = open(file_path_or_content, mode="r", encoding="utf-8-sig", errors="replace")

    try:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            return [], ["CSV file contains no headers or rows"]

        # Normalize header: strip whitespace and lowercase
        header = [col.strip().lower() for col in raw_header]
        
        # Check required columns
        missing_cols = [req for req in REQUIRED_COLUMNS if req not in header]
        if missing_cols:
            return [], [f"Missing required columns in CSV header: {', '.join(missing_cols)}. Expected at least {REQUIRED_COLUMNS}"]

        col_map = {name: idx for idx, name in enumerate(header)}
        seen_order_ids = set()

        for line_no, row in enumerate(reader, start=2):
            if not row or all(c.strip() == "" for c in row):
                continue  # skip blank lines

            if len(row) < len(header):
                errors.append(f"Line {line_no}: Incomplete row, expected {len(header)} columns, got {len(row)}")
                continue

            # Extract fields
            timestamp = row[col_map["timestamp"]].strip()
            symbol = row[col_map["symbol"]].strip().upper()
            side = row[col_map["side"]].strip().upper()
            price_str = row[col_map["price"]].strip()
            qty_str = row[col_map["quantity"]].strip()
            
            fee_str = row[col_map["fee"]].strip() if "fee" in col_map and col_map["fee"] < len(row) else "0.0"
            order_id = row[col_map["order_id"]].strip() if "order_id" in col_map and col_map["order_id"] < len(row) else f"row_{line_no}"
            if not order_id:
                order_id = f"row_{line_no}"

            # Validate numeric values
            row_errs = []
            try:
                price = float(price_str)
                if price <= 0:
                    row_errs.append(f"Price must be > 0, got {price}")
            except ValueError:
                row_errs.append(f"Invalid numeric price '{price_str}'")
                price = 0.0

            try:
                qty = float(qty_str)
                if qty <= 0:
                    row_errs.append(f"Quantity must be > 0, got {qty}")
            except ValueError:
                row_errs.append(f"Invalid numeric quantity '{qty_str}'")
                qty = 0.0

            try:
                fee = float(fee_str) if fee_str else 0.0
                if fee < 0:
                    row_errs.append(f"Fee cannot be negative, got {fee}")
            except ValueError:
                row_errs.append(f"Invalid numeric fee '{fee_str}'")
                fee = 0.0

            if side not in ["BUY", "SELL"]:
                row_errs.append(f"Invalid side '{side}' (must be BUY or SELL)")

            if not timestamp:
                row_errs.append("Timestamp is missing")

            if order_id in seen_order_ids:
                row_errs.append(f"Duplicate order_id '{order_id}'")
            else:
                seen_order_ids.add(order_id)

            if row_errs:
                errors.append(f"Line {line_no} (ID: {order_id}): {'; '.join(row_errs)}")
            else:
                trades.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "side": side,
                    "price": price,
                    "quantity": qty,
                    "fee": fee,
                    "order_id": order_id
                })

    finally:
        if not is_content:
            f.close()

    return trades, errors
