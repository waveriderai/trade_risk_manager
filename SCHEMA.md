# WaveRider Trading Journal - Database Schema

## Overview

This schema preserves Excel spreadsheet behavior with strong referential integrity.
All calculations are server-side. Trade ID is user-provided (not auto-generated).

## Tables

### 1. trades

Primary table for trade entries. One row per Trade ID.

```sql
CREATE TABLE trades (
    -- Identity
    trade_id VARCHAR(50) PRIMARY KEY,  -- User-provided, unique
    ticker VARCHAR(20) NOT NULL,

    -- Entry Details
    entry_date DATE NOT NULL,
    entry_price DECIMAL(12, 4) NOT NULL,
    entry_shares INTEGER NOT NULL,

    -- User Inputs
    low_of_day DECIMAL(12, 4),  -- Optional, used for Stop3 calculation
    stop3_override DECIMAL(12, 4),  -- Optional manual override
    portfolio_size DECIMAL(15, 2),  -- Optional snapshot

    -- Market Data (refreshed periodically)
    current_price DECIMAL(12, 4),
    atr_14 DECIMAL(12, 4),
    sma_50 DECIMAL(12, 4),
    sma_10 DECIMAL(12, 4),
    market_data_updated_at TIMESTAMP,

    -- Calculated Stops (derived, read-only in UI)
    stop_3 DECIMAL(12, 4),  -- LoD or override
    stop_2 DECIMAL(12, 4),  -- 2/3 distance from entry to stop3
    stop_1 DECIMAL(12, 4),  -- 1/3 distance from entry to stop3
    one_r_distance DECIMAL(12, 4),  -- Entry - Stop3

    -- Trade Status (computed)
    status VARCHAR(20),  -- OPEN, PARTIAL, CLOSED
    shares_remaining INTEGER,

    -- Rollup Calculations (computed from transactions)
    total_shares_exited INTEGER DEFAULT 0,
    weighted_avg_exit_price DECIMAL(12, 4),
    realized_pnl DECIMAL(15, 2) DEFAULT 0,
    unrealized_pnl DECIMAL(15, 2) DEFAULT 0,
    total_pnl DECIMAL(15, 2) DEFAULT 0,
    percent_gain_loss DECIMAL(10, 4),
    r_multiple DECIMAL(10, 4),

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (entry_shares > 0),
    CHECK (entry_price > 0),
    CHECK (shares_remaining >= 0)
);

CREATE INDEX idx_trades_ticker ON trades(ticker);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_entry_date ON trades(entry_date);
```

### 2. transactions

Exit transactions. References trades via Trade ID.

```sql
CREATE TABLE transactions (
    -- Identity
    id SERIAL PRIMARY KEY,  -- Auto-generated for transaction records

    -- Foreign Key
    trade_id VARCHAR(50) NOT NULL,

    -- Transaction Details
    transaction_date DATE NOT NULL,
    action VARCHAR(20) NOT NULL,  -- Stop1, Stop2, Stop3, Profit, Other
    shares INTEGER NOT NULL,
    price DECIMAL(12, 4) NOT NULL,

    -- Optional
    fees DECIMAL(10, 2) DEFAULT 0,
    notes TEXT,

    -- Calculated
    proceeds DECIMAL(15, 2),  -- (shares * price) - fees
    pnl DECIMAL(15, 2),  -- proceeds - (shares * entry_price)

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE,
    CHECK (shares > 0),
    CHECK (price > 0),
    CHECK (action IN ('Stop1', 'Stop2', 'Stop3', 'Profit', 'Other'))
);

CREATE INDEX idx_transactions_trade_id ON transactions(trade_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_action ON transactions(action);
```

## Key Design Decisions

### 1. Trade ID as Natural Key

- User provides Trade ID (e.g., "AAPL-001", "TSLA-20230515")
- No surrogate key for trades table
- Matches Excel workflow exactly

### 2. Derived Fields Stored in trades

- Stops, PnL, R-multiples stored for query performance
- Recalculated on:
  - Trade creation
  - Market data refresh
  - Transaction insert/update/delete

### 3. Transaction Validation

- Backend enforces: `SUM(transactions.shares) <= trade.entry_shares`
- Prevents over-exiting positions

### 4. Cascading Deletes

- Deleting a trade removes all linked transactions
- Matches spreadsheet behavior (delete row = delete all references)

## Calculation Formulas

### Stop Levels

```
Stop3 = stop3_override OR low_of_day
Stop2 = entry_price - (2/3 * (entry_price - Stop3))
Stop1 = entry_price - (1/3 * (entry_price - Stop3))
1R = entry_price - Stop3
```

### R-Multiple

```
R-Multiple = total_pnl / (entry_shares * 1R)
```

### Trade Status

```
IF shares_remaining == entry_shares THEN 'OPEN'
ELSE IF shares_remaining == 0 THEN 'CLOSED'
ELSE 'PARTIAL'
```

### Rollups from Transactions

```
total_shares_exited = SUM(transactions.shares WHERE trade_id = X)
shares_remaining = entry_shares - total_shares_exited
weighted_avg_exit_price = SUM(shares * price) / total_shares_exited
realized_pnl = SUM(transactions.pnl WHERE trade_id = X)
unrealized_pnl = shares_remaining * (current_price - entry_price)
total_pnl = realized_pnl + unrealized_pnl
```

## Migration Notes

- Initial deployment: Create tables via SQL migrations
- Use Alembic (Python) for version control
- Seed data: Optional CSV import for existing trades

## Indexes

Optimized for:
- Trade lookup by ID (primary key)
- Filtering by status/ticker
- Transaction queries by trade_id
- Date range queries

## Backup Strategy

- Daily snapshots recommended
- Transaction log retention for audit
- Export to CSV for portability
