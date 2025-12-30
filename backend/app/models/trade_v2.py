"""
SQLAlchemy models for trades and transactions - V2 (Complete WaveRider 3-Stop).
Implements ALL 36 columns from Google Sheet.
Matches SCHEMA_V2.md exactly - DO NOT simplify.
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime,
    CheckConstraint, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Trade(Base):
    """
    Trade entry model - Complete WaveRider 3-Stop implementation.
    One row per Trade ID (user-provided, not auto-generated).
    Implements all 36 columns from the Google Sheet.
    """
    __tablename__ = "trades"

    # ===== IDENTITY =====
    trade_id = Column(String(50), primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)  # "Stock"

    # ===== USER INPUT FIELDS (Green headers - Entry) =====
    purchase_price = Column(Numeric(12, 4), nullable=False)  # "Entry / Purchase Price" (PP)
    purchase_date = Column(Date, nullable=False, index=True)  # "Purchase Date"
    shares = Column(Integer, nullable=False)  # "Shares (Qty)"
    entry_day_low = Column(Numeric(12, 4), nullable=True)  # "Entry-day Low"
    stop_override = Column(Numeric(12, 4), nullable=True)  # "Override" (Stop3 override)

    # ===== MARKET DATA (Fetched from Polygon.io) =====
    current_price = Column(Numeric(12, 4), nullable=True)  # "Current Price" (CP)
    atr_14 = Column(Numeric(12, 4), nullable=True)  # "ATR(14) (sm)"
    sma_50 = Column(Numeric(12, 4), nullable=True)  # "SMA50"
    sma_10 = Column(Numeric(12, 4), nullable=True)  # "SMA10"
    market_data_updated_at = Column(DateTime, nullable=True)

    # ===== ENTRY SNAPSHOT (Captured at purchase_date) =====
    atr_at_entry = Column(Numeric(12, 4), nullable=True)  # ATR(14) at entry
    sma_at_entry = Column(Numeric(12, 4), nullable=True)  # SMA(50) at entry

    # ===== CALCULATED: Day Movement =====
    day_pct_moved = Column(Numeric(10, 4), nullable=True)  # "Day % Moved" (Day's % Activity)

    # ===== CALCULATED: Price vs Purchase Price =====
    cp_pct_diff_from_entry = Column(Numeric(10, 4), nullable=True)  # "CP % Diff From Entry (PP)"
    pct_gain_loss_trade = Column(Numeric(10, 4), nullable=True)  # "% Gain/Loss on Trade"

    # ===== CALCULATED: Portfolio Allocation =====
    portfolio_size = Column(Numeric(15, 2), nullable=True)  # Portfolio snapshot
    pct_portfolio_invested_at_entry = Column(Numeric(10, 4), nullable=True)  # "% of Portfolio Invested at Entry"
    pct_portfolio_current = Column(Numeric(10, 4), nullable=True)  # "% of Portfolio Current $"
    gain_loss_pct_portfolio_impact = Column(Numeric(10, 4), nullable=True)  # "Gain/Loss % Portfolio Impact"

    # ===== CALCULATED: Trading Days =====
    trading_days_open = Column(Integer, nullable=True)  # "Trading Days Open"

    # ===== CALCULATED: Risk/ATR Metrics =====
    risk_atr_r_units = Column(Numeric(10, 4), nullable=True)  # "Risk / ATR (R units)" = OneR / ATR_Entry
    atr_pct_multiple_from_ma_at_entry = Column(Numeric(10, 4), nullable=True)  # "ATR% Multiple from MA @ Entry"
    atr_pct_multiple_from_ma = Column(Numeric(10, 4), nullable=True)  # "ATR% Multiple from MA"

    # ===== CALCULATED: Stop Levels (3-Stop System) =====
    stop_3 = Column(Numeric(12, 4), nullable=True)  # "Stop3 (zone)"
    stop_2 = Column(Numeric(12, 4), nullable=True)  # "Stop2 (2/3)"
    stop_1 = Column(Numeric(12, 4), nullable=True)  # "Stop1 (1/3)"
    entry_pct_above_stop3 = Column(Numeric(10, 4), nullable=True)  # "Entry% Above Stop3"
    one_r = Column(Numeric(12, 4), nullable=True)  # 1R risk unit (PP - Stop3)

    # ===== CALCULATED: Take Profit Levels =====
    tp_1r = Column(Numeric(12, 4), nullable=True)  # "TP @ 1R"
    tp_2r = Column(Numeric(12, 4), nullable=True)  # "TP @ 2R"
    tp_3r = Column(Numeric(12, 4), nullable=True)  # "TP @ 3R"

    # ===== CALCULATED: Sale/Exit Info =====
    sold_price = Column(Numeric(12, 4), nullable=True)  # "Sold Price" (SP)

    # ===== TRANSACTION ROLLUPS =====
    shares_exited = Column(Integer, default=0)  # "Exited Shares"
    shares_remaining = Column(Integer, nullable=True)  # "Remaining Shares"
    total_proceeds = Column(Numeric(15, 2), default=0)  # "Total Proceeds"
    total_fees = Column(Numeric(15, 2), default=0)  # "Total Fees"
    avg_exit_price = Column(Numeric(12, 4), nullable=True)  # "Avg Exit Price"

    # ===== CALCULATED: PnL =====
    realized_pnl = Column(Numeric(15, 2), default=0)  # "Realized PnL ($)"
    unrealized_pnl = Column(Numeric(15, 2), default=0)  # "Unrealized PnL ($)"
    total_pnl = Column(Numeric(15, 2), default=0)  # "Total PnL ($)"
    r_multiple = Column(Numeric(10, 4), nullable=True)  # "R-Multiple" = Total PnL / (OneR * Shares)

    # ===== CALCULATED: Status =====
    status = Column(String(20), nullable=True)  # "Status" - OPEN/PARTIAL/CLOSED

    # ===== AUDIT =====
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ===== RELATIONSHIPS =====
    transactions = relationship(
        "Transaction",
        back_populates="trade",
        cascade="all, delete-orphan"
    )

    # ===== CONSTRAINTS =====
    __table_args__ = (
        CheckConstraint('shares > 0', name='check_shares_positive'),
        CheckConstraint('purchase_price > 0', name='check_purchase_price_positive'),
        CheckConstraint('shares_remaining >= 0', name='check_shares_remaining_non_negative'),
        Index('idx_trades_status', 'status'),
        Index('idx_trades_purchase_date', 'purchase_date'),
    )

    def __repr__(self):
        return f"<Trade(trade_id='{self.trade_id}', ticker='{self.ticker}', status='{self.status}')>"


class Transaction(Base):
    """
    Exit transaction model - Updated with TP1/TP2/TP3/Manual actions.
    """
    __tablename__ = "transactions"

    # ===== IDENTITY =====
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ===== FOREIGN KEY =====
    trade_id = Column(
        String(50),
        ForeignKey('trades.trade_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # ===== TRANSACTION DETAILS =====
    exit_date = Column(Date, nullable=False, index=True)  # "Exit Date"
    action = Column(String(20), nullable=False, index=True)  # "Action" - Stop1/2/3, TP1/2/3, Manual, Other
    ticker = Column(String(20), nullable=True)  # "Ticker" (for display)
    shares = Column(Integer, nullable=False)  # "Shares"
    price = Column(Numeric(12, 4), nullable=False)  # "Price"

    # ===== CALCULATED =====
    proceeds = Column(Numeric(15, 2), nullable=True)  # "Proceeds" = (shares * price) - fees

    # ===== OPTIONAL =====
    fees = Column(Numeric(10, 2), default=0)  # "Fees (optional)"
    notes = Column(String, nullable=True)  # "Notes"

    # ===== AUDIT =====
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ===== RELATIONSHIPS =====
    trade = relationship("Trade", back_populates="transactions")

    # ===== CONSTRAINTS =====
    __table_args__ = (
        CheckConstraint('shares > 0', name='check_shares_positive'),
        CheckConstraint('price > 0', name='check_price_positive'),
        CheckConstraint(
            "action IN ('Stop1', 'Stop2', 'Stop3', 'TP1', 'TP2', 'TP3', 'Manual', 'Other')",
            name='check_valid_action'
        ),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, trade_id='{self.trade_id}', action='{self.action}', shares={self.shares})>"
