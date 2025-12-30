"""
SQLAlchemy models for trades and transactions.
Matches SCHEMA.md exactly - DO NOT simplify.
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
    Trade entry model.
    One row per Trade ID (user-provided, not auto-generated).
    """
    __tablename__ = "trades"

    # Identity
    trade_id = Column(String(50), primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)

    # Entry Details
    entry_date = Column(Date, nullable=False, index=True)
    entry_price = Column(Numeric(12, 4), nullable=False)
    entry_shares = Column(Integer, nullable=False)

    # User Inputs
    low_of_day = Column(Numeric(12, 4), nullable=True)
    stop3_override = Column(Numeric(12, 4), nullable=True)
    portfolio_size = Column(Numeric(15, 2), nullable=True)

    # Market Data (refreshed periodically)
    current_price = Column(Numeric(12, 4), nullable=True)
    atr_14 = Column(Numeric(12, 4), nullable=True)
    sma_50 = Column(Numeric(12, 4), nullable=True)
    sma_10 = Column(Numeric(12, 4), nullable=True)
    market_data_updated_at = Column(DateTime, nullable=True)

    # Calculated Stops (derived, read-only in UI)
    stop_3 = Column(Numeric(12, 4), nullable=True)
    stop_2 = Column(Numeric(12, 4), nullable=True)
    stop_1 = Column(Numeric(12, 4), nullable=True)
    one_r_distance = Column(Numeric(12, 4), nullable=True)

    # Trade Status (computed)
    status = Column(String(20), nullable=True)  # OPEN, PARTIAL, CLOSED
    shares_remaining = Column(Integer, nullable=True)

    # Rollup Calculations (computed from transactions)
    total_shares_exited = Column(Integer, default=0)
    weighted_avg_exit_price = Column(Numeric(12, 4), nullable=True)
    realized_pnl = Column(Numeric(15, 2), default=0)
    unrealized_pnl = Column(Numeric(15, 2), default=0)
    total_pnl = Column(Numeric(15, 2), default=0)
    percent_gain_loss = Column(Numeric(10, 4), nullable=True)
    r_multiple = Column(Numeric(10, 4), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = relationship(
        "Transaction",
        back_populates="trade",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint('entry_shares > 0', name='check_entry_shares_positive'),
        CheckConstraint('entry_price > 0', name='check_entry_price_positive'),
        CheckConstraint('shares_remaining >= 0', name='check_shares_remaining_non_negative'),
        Index('idx_trades_status', 'status'),
    )

    def __repr__(self):
        return f"<Trade(trade_id='{self.trade_id}', ticker='{self.ticker}', status='{self.status}')>"


class Transaction(Base):
    """
    Exit transaction model.
    References trades via Trade ID.
    """
    __tablename__ = "transactions"

    # Identity
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    trade_id = Column(
        String(50),
        ForeignKey('trades.trade_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Transaction Details
    transaction_date = Column(Date, nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # Stop1, Stop2, Stop3, Profit, Other
    shares = Column(Integer, nullable=False)
    price = Column(Numeric(12, 4), nullable=False)

    # Optional
    fees = Column(Numeric(10, 2), default=0)
    notes = Column(String, nullable=True)

    # Calculated
    proceeds = Column(Numeric(15, 2), nullable=True)  # (shares * price) - fees
    pnl = Column(Numeric(15, 2), nullable=True)  # proceeds - (shares * entry_price)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trade = relationship("Trade", back_populates="transactions")

    # Constraints
    __table_args__ = (
        CheckConstraint('shares > 0', name='check_shares_positive'),
        CheckConstraint('price > 0', name='check_price_positive'),
        CheckConstraint(
            "action IN ('Stop1', 'Stop2', 'Stop3', 'Profit', 'Other')",
            name='check_valid_action'
        ),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, trade_id='{self.trade_id}', action='{self.action}', shares={self.shares})>"
