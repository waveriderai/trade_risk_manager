"""
API routes for transactions - V2 (with TP1/TP2/TP3/Manual).
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
from app.models.trade_v2 import Trade, Transaction
from app.models.schemas_v2 import TransactionCreate, TransactionUpdate, TransactionResponse, TransactionBulkCreate
from app.services.calculations_v2 import waverider_calc

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(transaction_data: TransactionCreate, db: Session = Depends(get_db)):
    """Create a new exit transaction."""

    # Validate trade exists
    trade = db.query(Trade).filter(Trade.trade_id == transaction_data.trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade '{transaction_data.trade_id}' not found")

    # Validate sufficient shares
    shares_available = trade.shares_remaining or trade.shares
    if transaction_data.shares > shares_available:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient shares. Available: {shares_available}, Requested: {transaction_data.shares}"
        )

    # Calculate proceeds
    proceeds = waverider_calc.calculate_transaction_proceeds(
        transaction_data.shares,
        transaction_data.price,
        transaction_data.fees or Decimal("0")
    )

    # Create transaction
    transaction = Transaction(
        trade_id=transaction_data.trade_id,
        exit_date=transaction_data.exit_date,
        action=transaction_data.action,
        ticker=transaction_data.ticker or trade.ticker,
        shares=transaction_data.shares,
        price=transaction_data.price,
        fees=transaction_data.fees or Decimal("0"),
        notes=transaction_data.notes,
        proceeds=proceeds,
    )

    db.add(transaction)

    # Update trade rollups
    waverider_calc.update_all_calculations(trade, db)

    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    trade_id: Optional[str] = Query(None, description="Filter by Trade ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    db: Session = Depends(get_db)
):
    """List all transactions with optional filters."""
    query = db.query(Transaction)

    if trade_id:
        query = query.filter(Transaction.trade_id == trade_id)

    if action:
        query = query.filter(Transaction.action == action)

    transactions = query.order_by(Transaction.exit_date.desc()).all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get a single transaction by ID."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    return transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """Update a transaction and recalculate trade rollups."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    trade = transaction.trade

    # Update fields
    if transaction_data.exit_date is not None:
        transaction.exit_date = transaction_data.exit_date
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

    # Recalculate proceeds
    transaction.proceeds = waverider_calc.calculate_transaction_proceeds(
        transaction.shares,
        transaction.price,
        transaction.fees
    )

    # Update trade rollups
    waverider_calc.update_all_calculations(trade, db)

    db.commit()
    db.refresh(transaction)

    return transaction


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction and recalculate trade rollups."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    trade = transaction.trade

    db.delete(transaction)

    # Update trade rollups
    waverider_calc.update_all_calculations(trade, db)

    db.commit()

    return None


@router.post("/upload-csv", response_model=List[TransactionResponse], status_code=201)
async def upload_transactions_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload transactions from CSV file.

    Expected CSV format (with header):
    exit_date,trade_id,action,ticker,shares,price,fees,notes

    Example:
    exit_date,trade_id,action,ticker,shares,price,fees,notes
    2024-01-20,AAPL-001,TP1,AAPL,50,190.25,1.00,Partial exit at TP1
    2024-01-21,TSLA-002,Stop2,TSLA,100,245.80,2.50,Hit Stop2

    Returns:
        List of created transactions
    """
    # Read file contents
    contents = await file.read()

    try:
        decoded = contents.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded CSV")

    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(decoded))

    required_fields = ['exit_date', 'trade_id', 'action', 'shares', 'price']
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
            exit_date = datetime.strptime(row['exit_date'].strip(), '%Y-%m-%d').date()
            action = row['action'].strip()
            ticker = row.get('ticker', '').strip() or None
            shares = int(row['shares'])
            price = Decimal(row['price'])
            fees = Decimal(row.get('fees', '0') or '0')
            notes = row.get('notes', '').strip() or None

            # Validate trade exists
            trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()
            if not trade:
                raise ValueError(f"Trade '{trade_id}' not found")

            # Calculate proceeds
            proceeds = waverider_calc.calculate_transaction_proceeds(shares, price, fees)

            # Create transaction
            transaction = Transaction(
                trade_id=trade_id,
                exit_date=exit_date,
                action=action,
                ticker=ticker or trade.ticker,
                shares=shares,
                price=price,
                fees=fees,
                notes=notes,
                proceeds=proceeds,
            )

            db.add(transaction)
            created_transactions.append(transaction)
            affected_trades.add(trade_id)

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error on row {row_num}: {str(e)}")

    # Update rollups for all affected trades
    for trade_id in affected_trades:
        trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()
        waverider_calc.update_all_calculations(trade, db)

    db.commit()

    # Refresh all transactions
    for transaction in created_transactions:
        db.refresh(transaction)

    return created_transactions
