# WaveRider 3-Stop Trading Journal - Complete Database Schema v2

## Overview

This schema implements ALL 36 columns from the WaveRider 3-Stop Google Sheet template.
Column headers are from Row 5. Formulas from Row 6 are implemented as calculated fields.

## Column Classification

### USER INPUT FIELDS (Green headers in sheet)
Fields the user manually enters:
- Trade ID
- Stock (Ticker)
- Entry/Purchase Price (PP)
- Purchase Date
- Shares (Qty)
- Entry-day Low
- Override (optional Stop3 override)

### CALCULATED FIELDS (Other colored headers)
All other fields are computed from:
- Market data (Polygon.io API)
- Transaction rollups
- Mathematical formulas matching the spreadsheet

---

## Complete Trades Table Schema

```sql
CREATE TABLE trades (
    -- ===== IDENTITY =====
    trade_id VARCHAR(50) PRIMARY KEY,  -- User-provided, unique

    -- ===== USER INPUT FIELDS (Entry) =====
    ticker VARCHAR(20) NOT NULL,  -- "Stock" column
    purchase_price DECIMAL(12, 4) NOT NULL,  -- "Entry / Purchase Price" (PP)
    purchase_date DATE NOT NULL,  -- "Purchase Date"
    shares INTEGER NOT NULL,  -- "Shares (Qty)"
    entry_day_low DECIMAL(12, 4),  -- "Entry-day Low" (optional, used for Stop3)
    stop_override DECIMAL(12, 4),  -- "Override" (optional Stop3 override)

    -- ===== MARKET DATA (Fetched from Polygon.io) =====
    current_price DECIMAL(12, 4),  -- "Current Price" (CP)
    atr_14 DECIMAL(12, 4),  -- "ATR(14) (sm)"
    sma_50 DECIMAL(12, 4),  -- "SMA50"
    sma_10 DECIMAL(12, 4),  -- "SMA10"
    market_data_updated_at TIMESTAMP,

    -- ===== ENTRY SNAPSHOT (Captured at entry date) =====
    atr_at_entry DECIMAL(12, 4),  -- ATR value on purchase_date
    sma_at_entry DECIMAL(12, 4),  -- SMA50 value on purchase_date

    -- ===== CALCULATED: Day Movement =====
    day_pct_moved DECIMAL(10, 4),  -- "Day % Moved" = (CP - LoD) / LoD

    -- ===== CALCULATED: Price vs Purchase Price =====
    gain_loss_pct_vs_pp DECIMAL(10, 4),  -- "% Gain/Loss vs. LoD (PP)" = (CP - PP) / PP * 100

    -- ===== CALCULATED: Portfolio Allocation =====
    pct_portfolio_invested_at_entry DECIMAL(10, 4),  -- "% of Portfolio Invested at Entry"
    pct_portfolio_current DECIMAL(10, 4),  -- "% of Portfolio Current $"

    -- ===== CALCULATED: Trading Days =====
    trading_days_open INTEGER,  -- "Trading Days Open" (from purchase_date to today)

    -- ===== CALCULATED: Risk/ATR Metrics =====
    risk_atr_pct_above_low DECIMAL(10, 4),  -- "Risk/ATR (% above Low Exit)"
    multiple_from_sma_at_entry DECIMAL(10, 4),  -- "Multiple from SMA at Entry" = PP / SMA_at_entry
    atr_multiple_from_sma_current DECIMAL(10, 4),  -- "ATR/% Multiple from SMA Current" = CP / SMA_current

    -- ===== CALCULATED: Stop Levels (3-Stop System) =====
    stop_3 DECIMAL(12, 4),  -- "Stop3 (zone)" = entry_day_low OR stop_override
    stop_2 DECIMAL(12, 4),  -- "Stop2 (2/3)" = PP - (2/3 * (PP - Stop3))
    stop_1 DECIMAL(12, 4),  -- "Stop1 (1/3)" = PP - (1/3 * (PP - Stop3))
    entry_pct_above_stop3 DECIMAL(10, 4),  -- "Entry% Above Stop3" = (PP - Stop3) / Stop3 * 100
    one_r DECIMAL(12, 4),  -- Distance from PP to Stop3 (1R risk unit)

    -- ===== CALCULATED: Take Profit Levels =====
    tp_1x DECIMAL(12, 4),  -- "TP @ 1X" = PP + (1 * one_r)
    tp_2x DECIMAL(12, 4),  -- "TP @ 2X" = PP + (2 * one_r)
    tp_3x DECIMAL(12, 4),  -- "TP @ 3X" = PP + (3 * one_r)

    -- ===== CALCULATED: Sale/Exit Info =====
    sell_price_at_entry DECIMAL(12, 4),  -- "Sell Price at Entry" (SP) - first exit price?

    -- ===== TRANSACTION ROLLUPS =====
    shares_exited INTEGER DEFAULT 0,  -- "Exited Shares"
    shares_remaining INTEGER,  -- "Remaining Shares" = shares - shares_exited
    total_proceeds DECIMAL(15, 2) DEFAULT 0,  -- "Total Proceeds" = SUM(proceeds)
    total_fees DECIMAL(15, 2) DEFAULT 0,  -- "Total Fees" = SUM(fees)
    avg_exit_price DECIMAL(12, 4),  -- "Avg Exit Price" = weighted average

    -- ===== CALCULATED: PnL =====
    realized_pnl DECIMAL(15, 2) DEFAULT 0,  -- "Realized PnL ($)"
    unrealized_pnl DECIMAL(15, 2) DEFAULT 0,  -- "Unrealized PnL ($)"
    total_pnl DECIMAL(15, 2) DEFAULT 0,  -- "Total PnL ($)" = realized + unrealized

    -- ===== CALCULATED: Status =====
    status VARCHAR(20),  -- "Status" = OPEN / PARTIAL / CLOSED

    -- ===== AUDIT =====
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- ===== CONSTRAINTS =====
    CHECK (shares > 0),
    CHECK (purchase_price > 0),
    CHECK (shares_remaining >= 0)
);

CREATE INDEX idx_trades_ticker ON trades(ticker);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_purchase_date ON trades(purchase_date);
```

---

## Updated Transactions Table Schema

```sql
CREATE TABLE transactions (
    -- ===== IDENTITY =====
    id SERIAL PRIMARY KEY,

    -- ===== FOREIGN KEY =====
    trade_id VARCHAR(50) NOT NULL,

    -- ===== TRANSACTION DETAILS =====
    exit_date DATE NOT NULL,  -- "Exit Date"
    action VARCHAR(20) NOT NULL,  -- "Action" - ENUM: Stop1, Stop2, Stop3, TP1, TP2, TP3, Manual, Other
    ticker VARCHAR(20),  -- "Ticker" (copied from trade for display)
    shares INTEGER NOT NULL,  -- "Shares"
    price DECIMAL(12, 4) NOT NULL,  -- "Price"

    -- ===== CALCULATED =====
    proceeds DECIMAL(15, 2),  -- "Proceeds" = (shares * price) - fees

    -- ===== OPTIONAL =====
    fees DECIMAL(10, 2) DEFAULT 0,  -- "Fees (optional)"
    notes TEXT,  -- "Notes"

    -- ===== AUDIT =====
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- ===== CONSTRAINTS =====
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE,
    CHECK (shares > 0),
    CHECK (price > 0),
    CHECK (action IN ('Stop1', 'Stop2', 'Stop3', 'TP1', 'TP2', 'TP3', 'Manual', 'Other'))
);

CREATE INDEX idx_transactions_trade_id ON transactions(trade_id);
CREATE INDEX idx_transactions_exit_date ON transactions(exit_date);
CREATE INDEX idx_transactions_action ON transactions(action);
```

---

## Calculation Formulas (Row 6 Logic)

### Basic Price Calculations
```python
# Day % Moved
day_pct_moved = ((current_price - entry_day_low) / entry_day_low) * 100 if entry_day_low else None

# % Gain/Loss vs PP
gain_loss_pct_vs_pp = ((current_price - purchase_price) / purchase_price) * 100

# Entry% Above Stop3
entry_pct_above_stop3 = ((purchase_price - stop_3) / stop_3) * 100 if stop_3 else None
```

### Stop Levels (3-Stop System)
```python
# Stop3 (base level)
stop_3 = stop_override if stop_override else entry_day_low

# Stop2 (2/3 of the way from PP to Stop3)
distance_to_stop3 = purchase_price - stop_3
stop_2 = purchase_price - (2/3 * distance_to_stop3)

# Stop1 (1/3 of the way from PP to Stop3)
stop_1 = purchase_price - (1/3 * distance_to_stop3)

# 1R (risk unit)
one_r = distance_to_stop3
```

### Take Profit Levels
```python
tp_1x = purchase_price + (1 * one_r)
tp_2x = purchase_price + (2 * one_r)
tp_3x = purchase_price + (3 * one_r)
```

### ATR/SMA Multiples
```python
# Multiple from SMA at Entry
multiple_from_sma_at_entry = purchase_price / sma_at_entry if sma_at_entry else None

# ATR Multiple from SMA Current
atr_multiple_from_sma_current = current_price / sma_50 if sma_50 else None

# Risk/ATR % above Low
risk_atr_pct_above_low = ((purchase_price - entry_day_low) / atr_at_entry) * 100 if atr_at_entry and entry_day_low else None
```

### Portfolio Allocation
```python
# Assuming portfolio_size is available (from user settings or AsOfDate sheet)
initial_position_value = shares * purchase_price
pct_portfolio_invested_at_entry = (initial_position_value / portfolio_size) * 100 if portfolio_size else None

current_position_value = shares_remaining * current_price
pct_portfolio_current = (current_position_value / portfolio_size) * 100 if portfolio_size else None
```

### Transaction Rollups
```python
# Shares
shares_exited = SUM(transactions.shares WHERE trade_id = X)
shares_remaining = shares - shares_exited

# Proceeds and Fees
total_proceeds = SUM(transactions.proceeds WHERE trade_id = X)
total_fees = SUM(transactions.fees WHERE trade_id = X)

# Weighted Average Exit Price
avg_exit_price = SUM(transactions.shares * transactions.price) / shares_exited if shares_exited > 0 else None

# PnL
realized_pnl = total_proceeds - (shares_exited * purchase_price)
unrealized_pnl = shares_remaining * (current_price - purchase_price) if shares_remaining > 0 else 0
total_pnl = realized_pnl + unrealized_pnl
```

### Trading Days Open
```python
# Count only trading days (weekdays, excluding market holidays)
# Use Polygon.io market calendar or business day calculation
from pandas.tseries.offsets import BDay
trading_days_open = len(pd.bdate_range(purchase_date, today))
```

### Status
```python
if shares_remaining == shares:
    status = "OPEN"
elif shares_remaining == 0:
    status = "CLOSED"
else:
    status = "PARTIAL"
```

---

## Data Dependencies

### Required from Polygon.io API
1. **Current Price (CP)** - Latest close or real-time quote
2. **Historical OHLC** - For ATR and SMA calculations
3. **ATR(14)** - 14-period Average True Range
4. **SMA(50)** - 50-period Simple Moving Average
5. **SMA(10)** - 10-period Simple Moving Average
6. **Market Calendar** - For trading days calculation
7. **Entry Date Snapshot** - Historical ATR and SMA values at purchase_date

### Entry Snapshot Fields
These must be captured and stored when trade is created:
- `atr_at_entry` - ATR(14) on purchase_date
- `sma_at_entry` - SMA(50) on purchase_date

---

## Named Ranges Mapping

| Named Range | Column | Database Field |
|-------------|--------|----------------|
| TradeID | A | trade_id |
| Ticker | B | ticker |
| CP | D | current_price |
| CpPctFromPP | E | gain_loss_pct_vs_pp |
| SP | G | sell_price_at_entry |
| PP | H | purchase_price |
| PortfolioInvestedAtEntry | I | pct_portfolio_invested_at_entry |
| PurchaseDate | K | purchase_date |
| Shares | L | shares |
| AtrMultMAEntry | O | multiple_from_sma_at_entry |
| AtrMultMACurrent | P | atr_multiple_from_sma_current |
| OneR | - | one_r |
| ATR | Z | atr_14 |
| SMA | AA | sma_50 |
| AtrEntry | - | atr_at_entry |
| SMAEntry | - | sma_at_entry |
| RemainingShares | AC | shares_remaining |
| AvgExitPrice | AF | avg_exit_price |
| Status | AJ | status |

---

## Migration Path

From current schema to v2:
```sql
-- Add all new columns to existing trades table
ALTER TABLE trades
  ADD COLUMN day_pct_moved DECIMAL(10, 4),
  ADD COLUMN gain_loss_pct_vs_pp DECIMAL(10, 4),
  ADD COLUMN sell_price_at_entry DECIMAL(12, 4),
  ADD COLUMN entry_day_low DECIMAL(12, 4),
  ADD COLUMN stop_override DECIMAL(12, 4),
  ADD COLUMN trading_days_open INTEGER,
  ADD COLUMN risk_atr_pct_above_low DECIMAL(10, 4),
  ADD COLUMN multiple_from_sma_at_entry DECIMAL(10, 4),
  ADD COLUMN atr_multiple_from_sma_current DECIMAL(10, 4),
  ADD COLUMN tp_1x DECIMAL(12, 4),
  ADD COLUMN tp_2x DECIMAL(12, 4),
  ADD COLUMN tp_3x DECIMAL(12, 4),
  ADD COLUMN entry_pct_above_stop3 DECIMAL(10, 4),
  ADD COLUMN atr_at_entry DECIMAL(12, 4),
  ADD COLUMN sma_at_entry DECIMAL(12, 4),
  ADD COLUMN pct_portfolio_invested_at_entry DECIMAL(10, 4),
  ADD COLUMN pct_portfolio_current DECIMAL(10, 4),
  ADD COLUMN shares_exited INTEGER DEFAULT 0,
  ADD COLUMN total_proceeds DECIMAL(15, 2) DEFAULT 0,
  ADD COLUMN total_fees DECIMAL(15, 2) DEFAULT 0,
  ADD COLUMN avg_exit_price DECIMAL(12, 4),
  ADD COLUMN one_r DECIMAL(12, 4);

-- Rename existing columns to match sheet
ALTER TABLE trades
  RENAME COLUMN entry_date TO purchase_date,
  RENAME COLUMN entry_price TO purchase_price,
  RENAME COLUMN entry_shares TO shares,
  RENAME COLUMN low_of_day TO entry_day_low,
  RENAME COLUMN stop3_override TO stop_override,
  RENAME COLUMN total_shares_exited TO shares_exited,
  RENAME COLUMN shares_remaining TO shares_remaining,
  RENAME COLUMN weighted_avg_exit_price TO avg_exit_price;

-- Update transactions table
ALTER TABLE transactions
  ADD COLUMN ticker VARCHAR(20),
  RENAME COLUMN transaction_date TO exit_date;

-- Update action constraint to include TP1, TP2, TP3, Manual
ALTER TABLE transactions
  DROP CONSTRAINT check_valid_action,
  ADD CONSTRAINT check_valid_action
    CHECK (action IN ('Stop1', 'Stop2', 'Stop3', 'TP1', 'TP2', 'TP3', 'Manual', 'Other'));
```
