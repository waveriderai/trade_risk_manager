## WaveRider 3-Stop - Migration to V2 (Complete Implementation)

This guide walks through migrating from the initial implementation to the complete 36-column system.

### Step 1: Replace Model Imports

**File: `backend/app/models/__init__.py`**
```python
"""
Models package.
"""
from app.models.trade_v2 import Trade, Transaction  # Changed from trade.py to trade_v2.py

__all__ = ["Trade", "Transaction"]
```

### Step 2: Replace Service Imports

**File: `backend/app/services/__init__.py`**
```python
"""
Services package.
"""
from app.services.market_data_v2 import market_data_service, MarketDataService
from app.services.calculations_v2 import waverider_calc, WaveRiderCalculations

__all__ = [
    "market_data_service",
    "MarketDataService",
    "waverider_calc",
    "WaveRiderCalculations",
]
```

### Step 3: Update API Routes

**File: `backend/app/api/trades.py`**

Key changes:
1. Import from `schemas_v2` instead of `schemas`
2. Use `waverider_calc` instead of `calculation_service`
3. Update field names (`entry_date` → `purchase_date`, `entry_price` → `purchase_price`, etc.)
4. Call `get_complete_market_data()` to get both current and entry snapshot

```python
from app.models.schemas_v2 import TradeCreate, TradeUpdate, TradeResponse, TradeSummary
from app.services.market_data_v2 import market_data_service
from app.services.calculations_v2 import waverider_calc

@router.post("", response_model=TradeResponse, status_code=201)
def create_trade(trade_data: TradeCreate, db: Session = Depends(get_db)):
    """Create a new trade entry with complete market data."""

    # Check uniqueness
    existing = db.query(Trade).filter(Trade.trade_id == trade_data.trade_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Trade ID '{trade_data.trade_id}' already exists")

    # Create trade instance
    trade = Trade(
        trade_id=trade_data.trade_id,
        ticker=trade_data.ticker,
        purchase_date=trade_data.purchase_date,  # Changed from entry_date
        purchase_price=trade_data.purchase_price,  # Changed from entry_price
        shares=trade_data.shares,  # Changed from entry_shares
        entry_day_low=trade_data.entry_day_low,  # Changed from low_of_day
        stop_override=trade_data.stop_override,  # Changed from stop3_override
        portfolio_size=trade_data.portfolio_size,
        shares_remaining=trade_data.shares,  # Initialize
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

        # Entry snapshot
        trade.atr_at_entry = entry_snapshot["atr_14"]
        trade.sma_at_entry = entry_snapshot["sma_50"]

        trade.market_data_updated_at = datetime.utcnow()

    except Exception as e:
        print(f"Warning: Could not fetch market data for {trade_data.ticker}: {e}")

    # Calculate ALL derived fields
    waverider_calc.update_all_calculations(trade, db)

    # Persist
    db.add(trade)
    db.commit()
    db.refresh(trade)

    return trade
```

### Step 4: Update Transactions API

**File: `backend/app/api/transactions.py`**

Key changes:
1. Import from `schemas_v2`
2. Update field names (`transaction_date` → `exit_date`)
3. Use `waverider_calc.calculate_transaction_proceeds()`
4. Copy ticker from trade to transaction

```python
from app.models.schemas_v2 import TransactionCreate, TransactionUpdate, TransactionResponse

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
        exit_date=transaction_data.exit_date,  # Changed from transaction_date
        action=transaction_data.action,
        ticker=transaction_data.ticker or trade.ticker,  # Copy from trade if not provided
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
```

### Step 5: Database Migration SQL

**File: `backend/migrations/upgrade_to_v2.sql`**

```sql
-- ===== RENAME EXISTING COLUMNS =====
ALTER TABLE trades
  RENAME COLUMN entry_date TO purchase_date,
  RENAME COLUMN entry_price TO purchase_price,
  RENAME COLUMN entry_shares TO shares,
  RENAME COLUMN low_of_day TO entry_day_low,
  RENAME COLUMN stop3_override TO stop_override,
  RENAME COLUMN total_shares_exited TO shares_exited,
  RENAME COLUMN weighted_avg_exit_price TO avg_exit_price,
  RENAME COLUMN one_r_distance TO one_r;

-- ===== ADD NEW CALCULATED COLUMNS =====
ALTER TABLE trades
  ADD COLUMN day_pct_moved DECIMAL(10, 4),
  ADD COLUMN gain_loss_pct_vs_pp DECIMAL(10, 4),
  ADD COLUMN pct_portfolio_invested_at_entry DECIMAL(10, 4),
  ADD COLUMN pct_portfolio_current DECIMAL(10, 4),
  ADD COLUMN trading_days_open INTEGER,
  ADD COLUMN risk_atr_pct_above_low DECIMAL(10, 4),
  ADD COLUMN multiple_from_sma_at_entry DECIMAL(10, 4),
  ADD COLUMN atr_multiple_from_sma_current DECIMAL(10, 4),
  ADD COLUMN entry_pct_above_stop3 DECIMAL(10, 4),
  ADD COLUMN atr_at_entry DECIMAL(12, 4),
  ADD COLUMN sma_at_entry DECIMAL(12, 4),
  ADD COLUMN tp_1x DECIMAL(12, 4),
  ADD COLUMN tp_2x DECIMAL(12, 4),
  ADD COLUMN tp_3x DECIMAL(12, 4),
  ADD COLUMN sell_price_at_entry DECIMAL(12, 4),
  ADD COLUMN total_proceeds DECIMAL(15, 2) DEFAULT 0,
  ADD COLUMN total_fees DECIMAL(15, 2) DEFAULT 0;

-- ===== UPDATE TRANSACTIONS TABLE =====
ALTER TABLE transactions
  RENAME COLUMN transaction_date TO exit_date,
  ADD COLUMN ticker VARCHAR(20);

-- Update ticker from parent trade
UPDATE transactions t
SET ticker = tr.ticker
FROM trades tr
WHERE t.trade_id = tr.trade_id;

-- ===== UPDATE ACTION CONSTRAINT =====
ALTER TABLE transactions
  DROP CONSTRAINT IF EXISTS check_valid_action,
  ADD CONSTRAINT check_valid_action
    CHECK (action IN ('Stop1', 'Stop2', 'Stop3', 'TP1', 'TP2', 'TP3', 'Manual', 'Other'));

-- ===== UPDATE TRADE CONSTRAINTS =====
ALTER TABLE trades
  DROP CONSTRAINT IF EXISTS check_entry_shares_positive,
  DROP CONSTRAINT IF EXISTS check_entry_price_positive,
  ADD CONSTRAINT check_shares_positive CHECK (shares > 0),
  ADD CONSTRAINT check_purchase_price_positive CHECK (purchase_price > 0);
```

### Step 6: Python Migration Script

**File: `backend/migrations/migrate_to_v2.py`**

```python
"""
Migration script to upgrade existing trades to V2 schema.
Recalculates all derived fields.
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.trade_v2 import Trade
from app.services.market_data_v2 import market_data_service
from app.services.calculations_v2 import waverider_calc

def migrate_existing_trades():
    """Migrate all existing trades to V2 calculations."""
    db: Session = SessionLocal()

    try:
        trades = db.query(Trade).all()
        print(f"Migrating {len(trades)} trades...")

        for trade in trades:
            print(f"Processing {trade.trade_id}...")

            # Fetch historical snapshot for entry date
            try:
                current_data, entry_snapshot = market_data_service.get_complete_market_data(
                    trade.ticker,
                    trade.purchase_date
                )

                # Update entry snapshot
                trade.atr_at_entry = entry_snapshot["atr_14"]
                trade.sma_at_entry = entry_snapshot["sma_50"]

                # Update current data
                trade.current_price = current_data["current_price"]
                trade.atr_14 = current_data["atr_14"]
                trade.sma_50 = current_data["sma_50"]
                trade.sma_10 = current_data["sma_10"]
                trade.market_data_updated_at = datetime.utcnow()

            except Exception as e:
                print(f"  Warning: Market data fetch failed: {e}")

            # Recalculate all fields
            waverider_calc.update_all_calculations(trade, db)

            print(f"  ✓ {trade.trade_id} migrated")

        db.commit()
        print(f"\n✅ Migration complete! {len(trades)} trades updated.")

    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_existing_trades()
```

### Step 7: Quick Replacement Commands

```bash
# 1. Backup current database
docker-compose exec db pg_dump -U waverider waverider_db > backup_before_v2.sql

# 2. Stop containers
docker-compose down

# 3. Run SQL migration
docker-compose up -d db
docker-compose exec db psql -U waverider -d waverider_db -f /path/to/upgrade_to_v2.sql

# 4. Update Python code
# (Replace imports as shown above)

# 5. Rebuild and restart
docker-compose build --no-cache backend
docker-compose up -d

# 6. Run Python migration script
docker-compose exec backend python migrations/migrate_to_v2.py

# 7. Verify
curl http://localhost:8000/api/v1/trades | jq
```

### Step 8: Testing Checklist

- [ ] Create new trade → Verify all 36 fields populate
- [ ] Add transaction → Verify rollups update correctly
- [ ] Market data refresh → Verify current data updates, entry snapshot preserved
- [ ] CSV upload → Verify TP1/TP2/TP3/Manual actions work
- [ ] Trade detail page → All fields display correctly
- [ ] Calculations match Google Sheet formulas

### Step 9: Rollback Plan (If Needed)

```bash
# Restore database from backup
docker-compose down
docker-compose up -d db
docker-compose exec db psql -U waverider -d waverider_db < backup_before_v2.sql
docker-compose restart
```
