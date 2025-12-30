"""
API routes for trades - V2 (Complete WaveRider 3-Stop).
Handles CRUD operations with all 36 columns.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.trade_v2 import Trade
from app.models.schemas_v2 import TradeCreate, TradeUpdate, TradeResponse, TradeSummary
from app.services.market_data_v2 import market_data_service
from app.services.calculations_v2 import waverider_calc

router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("", response_model=TradeResponse, status_code=201)
def create_trade(trade_data: TradeCreate, db: Session = Depends(get_db)):
    """
    Create a new trade entry with complete market data.

    Steps:
    1. Validate Trade ID uniqueness
    2. Fetch current market data + entry snapshot
    3. Calculate all derived fields
    4. Persist to database

    Returns:
        Created trade with all 36 calculated fields
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
        purchase_date=trade_data.purchase_date,
        purchase_price=trade_data.purchase_price,
        shares=trade_data.shares,
        entry_day_low=trade_data.entry_day_low,
        stop_override=trade_data.stop_override,
        portfolio_size=trade_data.portfolio_size,
        shares_remaining=trade_data.shares,  # Initially all shares remain
    )

    # Fetch market data (current + entry snapshot)
    try:
        current_data, entry_snapshot = market_data_service.get_complete_market_data(
            trade_data.ticker,
            trade_data.purchase_date
        )

        # Current market data
        trade.current_price = current_data["current_price"]
        trade.atr_14 = current_data["atr_14"]
        trade.sma_50 = current_data["sma_50"]
        trade.sma_10 = current_data["sma_10"]

        # Entry snapshot (captured at purchase_date)
        trade.atr_at_entry = entry_snapshot["atr_14"]
        trade.sma_at_entry = entry_snapshot["sma_50"]

        trade.market_data_updated_at = datetime.utcnow()

    except Exception as e:
        print(f"Warning: Could not fetch market data for {trade_data.ticker}: {e}")
        # Continue without market data (can be refreshed later)

    # Calculate ALL derived fields
    waverider_calc.update_all_calculations(trade, db)

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
        List of trades with all 36 columns
    """
    query = db.query(Trade)

    if status:
        query = query.filter(Trade.status == status.upper())

    if ticker:
        query = query.filter(Trade.ticker == ticker.upper())

    trades = query.order_by(Trade.purchase_date.desc()).all()
    return trades


@router.get("/summary", response_model=TradeSummary)
def get_trades_summary(db: Session = Depends(get_db)):
    """
    Get summary statistics across all trades.

    Returns:
        Aggregate metrics for portfolio including configuration values
    """
    from decimal import Decimal
    from app.core.config import settings

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

    # Total portfolio value (current positions)
    total_portfolio_value = None
    open_positions = [t for t in trades if t.shares_remaining and t.shares_remaining > 0 and t.current_price]
    if open_positions:
        total_portfolio_value = sum(
            (t.shares_remaining * t.current_price for t in open_positions),
            Decimal(0)
        )

    # % Portfolio Invested (sum of pct_portfolio_current for open/partial positions)
    pct_portfolio_invested = None
    active_positions = [t for t in trades if t.status in ["OPEN", "PARTIAL"] and t.pct_portfolio_current]
    if active_positions:
        pct_portfolio_invested = sum(
            (t.pct_portfolio_current for t in active_positions),
            Decimal(0)
        )

    # Configuration values
    portfolio_size = Decimal(str(settings.DEFAULT_PORTFOLIO_SIZE))
    buffer_pct = Decimal(str(settings.STOP3_BUFFER_PCT))

    return TradeSummary(
        total_trades=total_trades,
        open_trades=open_trades,
        partial_trades=partial_trades,
        closed_trades=closed_trades,
        total_realized_pnl=total_realized_pnl,
        total_unrealized_pnl=total_unrealized_pnl,
        total_pnl=total_pnl,
        average_r_multiple=average_r_multiple,
        total_portfolio_value=total_portfolio_value,
        portfolio_size=portfolio_size,
        buffer_pct=buffer_pct,
        pct_portfolio_invested=pct_portfolio_invested,
    )


@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade(trade_id: str, db: Session = Depends(get_db)):
    """
    Get a single trade by Trade ID.

    Returns:
        Trade details with all 36 calculated fields
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
    - entry_day_low
    - stop_override
    - portfolio_size

    Triggers recalculation of all derived fields.

    Returns:
        Updated trade with recalculated values
    """
    trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()

    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found")

    # Update fields
    if trade_data.entry_day_low is not None:
        trade.entry_day_low = trade_data.entry_day_low

    if trade_data.stop_override is not None:
        trade.stop_override = trade_data.stop_override

    if trade_data.portfolio_size is not None:
        trade.portfolio_size = trade_data.portfolio_size

    # Recalculate all derived fields
    waverider_calc.update_all_calculations(trade, db)

    db.commit()
    db.refresh(trade)

    return trade


@router.post("/{trade_id}/refresh", response_model=TradeResponse)
def refresh_market_data(trade_id: str, db: Session = Depends(get_db)):
    """
    Manually refresh market data for a trade.

    Fetches latest:
    - Current price
    - ATR(14), SMA(50), SMA(10)

    NOTE: Entry snapshot (atr_at_entry, sma_at_entry) is NOT refreshed
    as it represents historical values at purchase_date.

    Triggers recalculation of all derived fields.

    Returns:
        Updated trade
    """
    trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()

    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found")

    try:
        # Fetch only current market data (not entry snapshot)
        current_data = market_data_service.get_current_indicators(
            trade.ticker,
            trade.purchase_date
        )

        trade.current_price = current_data["current_price"]
        trade.atr_14 = current_data["atr_14"]
        trade.sma_50 = current_data["sma_50"]
        trade.sma_10 = current_data["sma_10"]
        trade.market_data_updated_at = datetime.utcnow()

        # Recalculate all derived fields
        waverider_calc.update_all_calculations(trade, db)

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
