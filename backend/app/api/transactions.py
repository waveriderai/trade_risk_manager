"""
API routes for transactions.
Handles exit transaction management and CSV upload.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
import csv
import io
from datetime import datetime
from decimal import Decimal

from app.core.database import get_db
from app.models.trade import Trade, Transaction
from app.models.schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionBulkCreate
)
from app.services.calculations import calculation_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new exit transaction.

    Steps:
    1. Validate Trade ID exists
    2. Validate sufficient shares available
    3. Calculate proceeds and PnL
    4. Persist transaction
    5. Update trade rollups

    Returns:
        Created transaction with calculated fields
    """
    # Validate trade exists
    trade = db.query(Trade).filter(Trade.trade_id == transaction_data.trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=404,
            detail=f"Trade '{transaction_data.trade_id}' not found"
        )

    # Validate sufficient shares
    shares_available = trade.shares_remaining or trade.entry_shares
    if transaction_data.shares > shares_available:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient shares. Available: {shares_available}, Requested: {transaction_data.shares}"
        )

    # Calculate proceeds and PnL
    proceeds, pnl = calculation_service.calculate_transaction_pnl(
        transaction_data.shares,
        transaction_data.price,
        trade.entry_price,
        transaction_data.fees or Decimal("0")
    )

    # Create transaction
    transaction = Transaction(
        trade_id=transaction_data.trade_id,
        transaction_date=transaction_data.transaction_date,
        action=transaction_data.action,
        shares=transaction_data.shares,
        price=transaction_data.price,
        fees=transaction_data.fees or Decimal("0"),
        notes=transaction_data.notes,
        proceeds=proceeds,
        pnl=pnl,
    )

    db.add(transaction)

    # Update trade rollups
    calculation_service.update_trade_calculations(trade, db)

    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    trade_id: Optional[str] = Query(None, description="Filter by Trade ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    db: Session = Depends(get_db)
):
    """
    List all transactions with optional filters.

    Query parameters:
    - trade_id: Filter by specific trade
    - action: Filter by action type (Stop1, Stop2, Stop3, Profit, Other)

    Returns:
        List of transactions matching filters
    """
    query = db.query(Transaction)

    if trade_id:
        query = query.filter(Transaction.trade_id == trade_id)

    if action:
        query = query.filter(Transaction.action == action)

    transactions = query.order_by(Transaction.transaction_date.desc()).all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Get a single transaction by ID.

    Returns:
        Transaction details
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found"
        )

    return transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a transaction.

    Editable fields:
    - transaction_date
    - action
    - shares
    - price
    - fees
    - notes

    Triggers recalculation of proceeds, PnL, and trade rollups.

    Returns:
        Updated transaction
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found"
        )

    trade = transaction.trade

    # Update fields
    if transaction_data.transaction_date is not None:
        transaction.transaction_date = transaction_data.transaction_date

    if transaction_data.action is not None:
        transaction.action = transaction_data.action

    if transaction_data.shares is not None:
        transaction.shares = transaction_data.shares

    if transaction_data.price is not None:
        transaction.price = transaction_data.price

    if transaction_data.fees is not None:
        transaction.fees = transaction_data.fees

    if transaction_data.notes is not None:
        transaction.notes = transaction_data.notes

    # Recalculate proceeds and PnL
    proceeds, pnl = calculation_service.calculate_transaction_pnl(
        transaction.shares,
        transaction.price,
        trade.entry_price,
        transaction.fees
    )
    transaction.proceeds = proceeds
    transaction.pnl = pnl

    # Update trade rollups
    calculation_service.update_trade_calculations(trade, db)

    db.commit()
    db.refresh(transaction)

    return transaction


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Delete a transaction.

    Triggers recalculation of trade rollups.

    Returns:
        204 No Content
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found"
        )

    trade = transaction.trade

    db.delete(transaction)

    # Update trade rollups
    calculation_service.update_trade_calculations(trade, db)

    db.commit()

    return None


@router.post("/bulk", response_model=List[TransactionResponse], status_code=201)
def bulk_create_transactions(
    bulk_data: TransactionBulkCreate,
    db: Session = Depends(get_db)
):
    """
    Create multiple transactions at once.

    Used for programmatic bulk creation.
    See /upload-csv for CSV file upload.

    Returns:
        List of created transactions
    """
    created_transactions = []
    affected_trades = set()

    for transaction_data in bulk_data.transactions:
        # Validate trade exists
        trade = db.query(Trade).filter(Trade.trade_id == transaction_data.trade_id).first()
        if not trade:
            raise HTTPException(
                status_code=404,
                detail=f"Trade '{transaction_data.trade_id}' not found"
            )

        # Calculate proceeds and PnL
        proceeds, pnl = calculation_service.calculate_transaction_pnl(
            transaction_data.shares,
            transaction_data.price,
            trade.entry_price,
            transaction_data.fees or Decimal("0")
        )

        # Create transaction
        transaction = Transaction(
            trade_id=transaction_data.trade_id,
            transaction_date=transaction_data.transaction_date,
            action=transaction_data.action,
            shares=transaction_data.shares,
            price=transaction_data.price,
            fees=transaction_data.fees or Decimal("0"),
            notes=transaction_data.notes,
            proceeds=proceeds,
            pnl=pnl,
        )

        db.add(transaction)
        created_transactions.append(transaction)
        affected_trades.add(trade.trade_id)

    # Update rollups for all affected trades
    for trade_id in affected_trades:
        trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()
        calculation_service.update_trade_calculations(trade, db)

    db.commit()

    # Refresh all transactions
    for transaction in created_transactions:
        db.refresh(transaction)

    return created_transactions


@router.post("/upload-csv", response_model=List[TransactionResponse], status_code=201)
async def upload_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload transactions from CSV file.

    Expected CSV format (with header):
    trade_id,transaction_date,action,shares,price,fees,notes

    Example:
    trade_id,transaction_date,action,shares,price,fees,notes
    AAPL-001,2024-01-20,Stop2,50,190.25,1.00,Partial exit
    TSLA-002,2024-01-21,Profit,100,245.80,2.50,Full exit

    Returns:
        List of created transactions
    """
    # Read file contents
    contents = await file.read()

    try:
        decoded = contents.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded CSV"
        )

    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(decoded))

    required_fields = ['trade_id', 'transaction_date', 'action', 'shares', 'price']
    if not all(field in csv_reader.fieldnames for field in required_fields):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {', '.join(required_fields)}"
        )

    created_transactions = []
    affected_trades = set()
    row_num = 1

    for row in csv_reader:
        row_num += 1

        try:
            # Parse row
            trade_id = row['trade_id'].strip()
            transaction_date = datetime.strptime(row['transaction_date'].strip(), '%Y-%m-%d').date()
            action = row['action'].strip()
            shares = int(row['shares'])
            price = Decimal(row['price'])
            fees = Decimal(row.get('fees', '0') or '0')
            notes = row.get('notes', '').strip() or None

            # Validate trade exists
            trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()
            if not trade:
                raise ValueError(f"Trade '{trade_id}' not found")

            # Calculate proceeds and PnL
            proceeds, pnl = calculation_service.calculate_transaction_pnl(
                shares, price, trade.entry_price, fees
            )

            # Create transaction
            transaction = Transaction(
                trade_id=trade_id,
                transaction_date=transaction_date,
                action=action,
                shares=shares,
                price=price,
                fees=fees,
                notes=notes,
                proceeds=proceeds,
                pnl=pnl,
            )

            db.add(transaction)
            created_transactions.append(transaction)
            affected_trades.add(trade_id)

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error on row {row_num}: {str(e)}"
            )

    # Update rollups for all affected trades
    for trade_id in affected_trades:
        trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()
        calculation_service.update_trade_calculations(trade, db)

    db.commit()

    # Refresh all transactions
    for transaction in created_transactions:
        db.refresh(transaction)

    return created_transactions
