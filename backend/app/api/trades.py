"""
API routes for trades.
Handles CRUD operations and market data refresh.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.trade import Trade
from app.models.schemas import (
    TradeCreate, TradeUpdate, TradeResponse, TradeSummary
)
from app.services.market_data import market_data_service
from app.services.calculations import calculation_service

router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("", response_model=TradeResponse, status_code=201)
def create_trade(trade_data: TradeCreate, db: Session = Depends(get_db)):
    """
    Create a new trade entry.

    Steps:
    1. Validate Trade ID uniqueness
    2. Fetch market data
    3. Calculate derived fields
    4. Persist to database

    Returns:
        Created trade with all calculated fields
    """
    # Check if Trade ID already exists
    existing = db.query(Trade).filter(Trade.trade_id == trade_data.trade_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Trade ID '{trade_data.trade_id}' already exists"
        )

    # Create trade instance
    trade = Trade(
        trade_id=trade_data.trade_id,
        ticker=trade_data.ticker,
        entry_date=trade_data.entry_date,
        entry_price=trade_data.entry_price,
        entry_shares=trade_data.entry_shares,
        low_of_day=trade_data.low_of_day,
        stop3_override=trade_data.stop3_override,
        portfolio_size=trade_data.portfolio_size,
        shares_remaining=trade_data.entry_shares,  # Initially all shares remain
    )

    # Fetch market data
    try:
        market_data = market_data_service.get_market_data_for_trade(
            trade_data.ticker,
            trade_data.entry_date
        )

        trade.current_price = market_data["current_price"]
        trade.atr_14 = market_data["atr_14"]
        trade.sma_50 = market_data["sma_50"]
        trade.sma_10 = market_data["sma_10"]
        trade.market_data_updated_at = datetime.utcnow()

    except Exception as e:
        print(f"Warning: Could not fetch market data for {trade_data.ticker}: {e}")
        # Continue without market data (can be refreshed later)

    # Calculate derived fields
    calculation_service.update_trade_calculations(trade, db)

    # Persist
    db.add(trade)
    db.commit()
    db.refresh(trade)

    return trade


@router.get("", response_model=List[TradeResponse])
def list_trades(
    status: Optional[str] = Query(None, description="Filter by status: OPEN, PARTIAL, CLOSED"),
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    db: Session = Depends(get_db)
):
    """
    List all trades with optional filters.

    Query parameters:
    - status: Filter by trade status
    - ticker: Filter by ticker symbol

    Returns:
        List of trades matching filters
    """
    query = db.query(Trade)

    if status:
        query = query.filter(Trade.status == status.upper())

    if ticker:
        query = query.filter(Trade.ticker == ticker.upper())

    trades = query.order_by(Trade.entry_date.desc()).all()
    return trades


@router.get("/summary", response_model=TradeSummary)
def get_trades_summary(db: Session = Depends(get_db)):
    """
    Get summary statistics across all trades.

    Returns:
        Aggregate metrics for portfolio
    """
    from sqlalchemy import func
    from decimal import Decimal

    trades = db.query(Trade).all()

    total_trades = len(trades)
    open_trades = len([t for t in trades if t.status == "OPEN"])
    partial_trades = len([t for t in trades if t.status == "PARTIAL"])
    closed_trades = len([t for t in trades if t.status == "CLOSED"])

    total_realized_pnl = sum((t.realized_pnl or Decimal(0) for t in trades), Decimal(0))
    total_unrealized_pnl = sum((t.unrealized_pnl or Decimal(0) for t in trades), Decimal(0))
    total_pnl = total_realized_pnl + total_unrealized_pnl

    # Average R-multiple (for closed trades only)
    r_multiples = [t.r_multiple for t in trades if t.r_multiple and t.status == "CLOSED"]
    average_r_multiple = None
    if r_multiples:
        average_r_multiple = sum(r_multiples, Decimal(0)) / len(r_multiples)

    return TradeSummary(
        total_trades=total_trades,
        open_trades=open_trades,
        partial_trades=partial_trades,
        closed_trades=closed_trades,
        total_realized_pnl=total_realized_pnl,
        total_unrealized_pnl=total_unrealized_pnl,
        total_pnl=total_pnl,
        average_r_multiple=average_r_multiple,
    )


@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade(trade_id: str, db: Session = Depends(get_db)):
    """
    Get a single trade by Trade ID.

    Returns:
        Trade details with all calculated fields
    """
    trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()

    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found")

    return trade


@router.patch("/{trade_id}", response_model=TradeResponse)
def update_trade(
    trade_id: str,
    trade_data: TradeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user-editable fields on a trade.

    Editable fields:
    - low_of_day
    - stop3_override
    - portfolio_size

    Triggers recalculation of derived fields.

    Returns:
        Updated trade
    """
    trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()

    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found")

    # Update fields
    if trade_data.low_of_day is not None:
        trade.low_of_day = trade_data.low_of_day

    if trade_data.stop3_override is not None:
        trade.stop3_override = trade_data.stop3_override

    if trade_data.portfolio_size is not None:
        trade.portfolio_size = trade_data.portfolio_size

    # Recalculate
    calculation_service.update_trade_calculations(trade, db)

    db.commit()
    db.refresh(trade)

    return trade


@router.post("/{trade_id}/refresh", response_model=TradeResponse)
def refresh_market_data(trade_id: str, db: Session = Depends(get_db)):
    """
    Manually refresh market data for a trade.

    Fetches latest:
    - Current price
    - ATR(14)
    - SMA(50)
    - SMA(10)

    Triggers recalculation of PnL and derived fields.

    Returns:
        Updated trade
    """
    trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()

    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found")

    try:
        # Fetch market data
        market_data = market_data_service.get_market_data_for_trade(
            trade.ticker,
            trade.entry_date
        )

        trade.current_price = market_data["current_price"]
        trade.atr_14 = market_data["atr_14"]
        trade.sma_50 = market_data["sma_50"]
        trade.sma_10 = market_data["sma_10"]
        trade.market_data_updated_at = datetime.utcnow()

        # Recalculate
        calculation_service.update_trade_calculations(trade, db)

        db.commit()
        db.refresh(trade)

        return trade

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh market data: {str(e)}"
        )


@router.delete("/{trade_id}", status_code=204)
def delete_trade(trade_id: str, db: Session = Depends(get_db)):
    """
    Delete a trade and all associated transactions.

    Uses CASCADE delete (defined in model).

    Returns:
        204 No Content
    """
    trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()

    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found")

    db.delete(trade)
    db.commit()

    return None
