"""
Pydantic schemas for WaveRider 3-Stop system - V2 (Complete).
Request/response validation for all 36 columns.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ==================== Trade Schemas ====================

class TradeCreate(BaseModel):
    """Request schema for creating a trade - USER INPUT FIELDS ONLY."""

    # Required fields
    trade_id: str = Field(..., min_length=1, max_length=50, description="User-provided Trade ID")
    ticker: str = Field(..., min_length=1, max_length=20, description="Stock ticker")
    purchase_price: Decimal = Field(..., gt=0, description="Purchase/Entry price (PP)")
    purchase_date: date = Field(..., description="Purchase date")
    shares: int = Field(..., gt=0, description="Number of shares")

    # Optional fields
    entry_day_low: Optional[Decimal] = Field(None, description="Low of entry day (for Stop3)")
    stop_override: Optional[Decimal] = Field(None, description="Manual Stop3 override")
    portfolio_size: Optional[Decimal] = Field(None, gt=0, description="Portfolio size snapshot")

    class Config:
        json_schema_extra = {
            "example": {
                "trade_id": "AAPL-001",
                "ticker": "AAPL",
                "purchase_price": "185.50",
                "purchase_date": "2024-01-15",
                "shares": 100,
                "entry_day_low": "184.20",
                "portfolio_size": "50000.00"
            }
        }


class TradeUpdate(BaseModel):
    """Request schema for updating user-editable fields."""
    entry_day_low: Optional[Decimal] = None
    stop_override: Optional[Decimal] = None
    portfolio_size: Optional[Decimal] = None


class TradeResponse(BaseModel):
    """Complete response schema with ALL 36 columns."""

    # ===== IDENTITY =====
    trade_id: str
    ticker: str

    # ===== USER INPUT FIELDS =====
    purchase_price: Decimal  # PP
    purchase_date: date
    shares: int
    entry_day_low: Optional[Decimal]
    stop_override: Optional[Decimal]
    portfolio_size: Optional[Decimal]

    # ===== MARKET DATA (Current) =====
    current_price: Optional[Decimal]  # CP
    atr_14: Optional[Decimal]
    sma_50: Optional[Decimal]
    sma_10: Optional[Decimal]
    market_data_updated_at: Optional[datetime]

    # ===== ENTRY SNAPSHOT =====
    atr_at_entry: Optional[Decimal]
    sma_at_entry: Optional[Decimal]

    # ===== CALCULATED: Price & Day Movement =====
    day_pct_moved: Optional[Decimal]
    gain_loss_pct_vs_pp: Optional[Decimal]

    # ===== CALCULATED: Portfolio =====
    pct_portfolio_invested_at_entry: Optional[Decimal]
    pct_portfolio_current: Optional[Decimal]

    # ===== CALCULATED: Time =====
    trading_days_open: Optional[int]

    # ===== CALCULATED: Risk/ATR Metrics =====
    risk_atr_pct_above_low: Optional[Decimal]
    multiple_from_sma_at_entry: Optional[Decimal]
    atr_multiple_from_sma_current: Optional[Decimal]

    # ===== CALCULATED: Stop Levels =====
    stop_3: Optional[Decimal]
    stop_2: Optional[Decimal]
    stop_1: Optional[Decimal]
    entry_pct_above_stop3: Optional[Decimal]
    one_r: Optional[Decimal]

    # ===== CALCULATED: Take Profit Levels =====
    tp_1x: Optional[Decimal]
    tp_2x: Optional[Decimal]
    tp_3x: Optional[Decimal]

    # ===== CALCULATED: Exit Info =====
    sell_price_at_entry: Optional[Decimal]  # SP

    # ===== TRANSACTION ROLLUPS =====
    shares_exited: int
    shares_remaining: Optional[int]
    total_proceeds: Decimal
    total_fees: Decimal
    avg_exit_price: Optional[Decimal]

    # ===== CALCULATED: PnL =====
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal

    # ===== STATUS =====
    status: Optional[str]  # OPEN, PARTIAL, CLOSED

    # ===== AUDIT =====
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2


# ==================== Transaction Schemas ====================

class TransactionCreate(BaseModel):
    """Request schema for creating a transaction."""

    trade_id: str = Field(..., min_length=1, max_length=50, description="Trade ID")
    exit_date: date = Field(..., description="Exit date")
    action: str = Field(..., description="Action type")
    shares: int = Field(..., gt=0, description="Number of shares")
    price: Decimal = Field(..., gt=0, description="Exit price")
    ticker: Optional[str] = Field(None, description="Ticker (optional, copied from trade)")
    fees: Optional[Decimal] = Field(0, description="Transaction fees")
    notes: Optional[str] = Field(None, description="Optional notes")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Ensure action is valid."""
        valid_actions = ['Stop1', 'Stop2', 'Stop3', 'TP1', 'TP2', 'TP3', 'Manual', 'Other']
        if v not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "trade_id": "AAPL-001",
                "exit_date": "2024-01-20",
                "action": "TP1",
                "shares": 50,
                "price": "190.25",
                "fees": "1.00",
                "notes": "Partial exit at TP1"
            }
        }


class TransactionUpdate(BaseModel):
    """Request schema for updating a transaction."""
    exit_date: Optional[date] = None
    action: Optional[str] = None
    shares: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    fees: Optional[Decimal] = None
    notes: Optional[str] = None

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Ensure action is valid if provided."""
        if v is not None:
            valid_actions = ['Stop1', 'Stop2', 'Stop3', 'TP1', 'TP2', 'TP3', 'Manual', 'Other']
            if v not in valid_actions:
                raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return v


class TransactionResponse(BaseModel):
    """Response schema for transaction - EXACTLY 9 fields displayed."""

    id: int
    trade_id: str
    exit_date: date  # "Exit Date"
    action: str  # "Action"
    ticker: Optional[str]  # "Ticker"
    shares: int  # "Shares"
    price: Decimal  # "Price"
    proceeds: Optional[Decimal]  # "Proceeds"
    fees: Decimal  # "Fees (optional)"
    notes: Optional[str]  # "Notes"

    # Audit (not displayed in grid)
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
    total_portfolio_value: Optional[Decimal]


# ==================== Market Data Refresh ====================

class MarketDataRefreshResponse(BaseModel):
    """Response after refreshing market data."""
    trade_id: str
    ticker: str
    current_price: Optional[Decimal]
    atr_14: Optional[Decimal]
    sma_50: Optional[Decimal]
    sma_10: Optional[Decimal]
    updated_at: datetime
    message: str


# ==================== Error Responses ====================

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    detail: List[dict]


# ==================== CSV Upload Template ====================

class TransactionCSVRow(BaseModel):
    """Single row for CSV upload validation."""
    exit_date: str  # Will be parsed as date
    trade_id: str
    action: str
    ticker: Optional[str]
    shares: int
    price: Decimal
    fees: Optional[Decimal] = Decimal("0")
    notes: Optional[str] = None

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action type."""
        valid_actions = ['Stop1', 'Stop2', 'Stop3', 'TP1', 'TP2', 'TP3', 'Manual', 'Other']
        if v not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return v
