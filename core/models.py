"""
Paper Trade Risk Audit API - Domain Models
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class Trade:
    timestamp: str  # ISO 8601 string
    symbol: str     # e.g., "BTCUSDT"
    side: str       # "BUY" or "SELL"
    price: float    # Execution price > 0
    quantity: float # Executed quantity > 0
    fee: float = 0.0 # Execution fee in quote currency
    order_id: Optional[str] = None

    def validate(self) -> List[str]:
        errors = []
        if self.side.upper() not in ["BUY", "SELL"]:
            errors.append(f"Invalid side '{self.side}': must be 'BUY' or 'SELL'")
        if self.price <= 0:
            errors.append(f"Price must be positive, got {self.price}")
        if self.quantity <= 0:
            errors.append(f"Quantity must be positive, got {self.quantity}")
        if self.fee < 0:
            errors.append(f"Fee cannot be negative, got {self.fee}")
        if not self.timestamp:
            errors.append("Timestamp is required")
        return errors

@dataclass
class AuditReport:
    initial_equity: float
    final_equity: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    realized_gross_pnl: float
    total_fees: float
    realized_net_pnl: float
    max_drawdown_pct: float
    max_drawdown_usd: float
    profit_factor: float
    max_exposure_concentration_pct: float
    invalid_position_flags: List[str]
    calculation_assumptions: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
