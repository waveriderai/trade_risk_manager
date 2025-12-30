"""
Pydantic schemas for request/response validation.
Separate from SQLAlchemy models for clean API contracts.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# ==================== Trade Schemas ====================

class TradeCreate(BaseModel):
    """Request schema for creating a trade."""
    trade_id: str = Field(..., min_length=1, max_length=50, description="User-provided Trade ID")
    ticker: str = Field(..., min_length=1, max_length=20, description="Stock ticker symbol")
    entry_date: date = Field(..., description="Entry date")
    entry_price: Decimal = Field(..., gt=0, description="Entry price (must be positive)")
    entry_shares: int = Field(..., gt=0, description="Number of shares (must be positive)")
    low_of_day: Optional[Decimal] = Field(None, description="Low of day (optional)")
    stop3_override: Optional[Decimal] = Field(None, description="Manual Stop3 override (optional)")
    portfolio_size: Optional[Decimal] = Field(None, description="Portfolio size snapshot (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "trade_id": "AAPL-001",
                "ticker": "AAPL",
                "entry_date": "2024-01-15",
                "entry_price": "185.50",
                "entry_shares": 100,
                "low_of_day": "184.20",
                "portfolio_size": "50000.00"
            }
        }


class TradeUpdate(BaseModel):
    """Request schema for updating user-editable fields."""
    low_of_day: Optional[Decimal] = None
    stop3_override: Optional[Decimal] = None
    portfolio_size: Optional[Decimal] = None


class TradeResponse(BaseModel):
    """Response schema for trade data."""
    # Identity
    trade_id: str
    ticker: str

    # Entry Details
    entry_date: date
    entry_price: Decimal
    entry_shares: int

    # User Inputs
    low_of_day: Optional[Decimal]
    stop3_override: Optional[Decimal]
    portfolio_size: Optional[Decimal]

    # Market Data
    current_price: Optional[Decimal]
    atr_14: Optional[Decimal]
    sma_50: Optional[Decimal]
    sma_10: Optional[Decimal]
    market_data_updated_at: Optional[datetime]

    # Calculated Stops
    stop_3: Optional[Decimal]
    stop_2: Optional[Decimal]
    stop_1: Optional[Decimal]
    one_r_distance: Optional[Decimal]

    # Trade Status
    status: Optional[str]
    shares_remaining: Optional[int]

    # Rollup Calculations
    total_shares_exited: int
    weighted_avg_exit_price: Optional[Decimal]
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    percent_gain_loss: Optional[Decimal]
    r_multiple: Optional[Decimal]

    # Audit
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


# ==================== Transaction Schemas ====================

class TransactionCreate(BaseModel):
    """Request schema for creating a transaction."""
    trade_id: str = Field(..., min_length=1, max_length=50, description="Trade ID (must exist)")
    transaction_date: date = Field(..., description="Transaction date")
    action: str = Field(..., description="Action type")
    shares: int = Field(..., gt=0, description="Number of shares (must be positive)")
    price: Decimal = Field(..., gt=0, description="Exit price (must be positive)")
    fees: Optional[Decimal] = Field(0, description="Transaction fees")
    notes: Optional[str] = Field(None, description="Optional notes")

    @validator('action')
    def validate_action(cls, v):
        """Ensure action is valid."""
        valid_actions = ['Stop1', 'Stop2', 'Stop3', 'Profit', 'Other']
        if v not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "trade_id": "AAPL-001",
                "transaction_date": "2024-01-20",
                "action": "Stop2",
                "shares": 50,
                "price": "190.25",
                "fees": "1.00",
                "notes": "Partial exit at Stop2"
            }
        }


class TransactionUpdate(BaseModel):
    """Request schema for updating a transaction."""
    transaction_date: Optional[date] = None
    action: Optional[str] = None
    shares: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    fees: Optional[Decimal] = None
    notes: Optional[str] = None

    @validator('action')
    def validate_action(cls, v):
        """Ensure action is valid if provided."""
        if v is not None:
            valid_actions = ['Stop1', 'Stop2', 'Stop3', 'Profit', 'Other']
            if v not in valid_actions:
                raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return v


class TransactionResponse(BaseModel):
    """Response schema for transaction data."""
    id: int
    trade_id: str
    transaction_date: date
    action: str
    shares: int
    price: Decimal
    fees: Decimal
    notes: Optional[str]
    proceeds: Optional[Decimal]
    pnl: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Bulk Operations ====================

class TransactionBulkCreate(BaseModel):
    """Request schema for bulk transaction creation (CSV upload)."""
    transactions: List[TransactionCreate]


# ==================== Summary/Analytics ====================

class TradeSummary(BaseModel):
    """Summary statistics for all trades."""
    total_trades: int
    open_trades: int
    partial_trades: int
    closed_trades: int
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
    total_pnl: Decimal
    average_r_multiple: Optional[Decimal]


# ==================== Error Responses ====================

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    detail: List[dict]
