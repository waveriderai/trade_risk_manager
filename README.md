# WaveRider 3-Stop Trading Journal - V2 (Complete)

A production-ready, Docker-deployable web application that replaces Excel-based trading journals with a deterministic, spreadsheet-parity system featuring the complete WaveRider 3-Stop methodology.

## 🎯 Purpose

This application digitizes the complete WaveRider 3-Stop Trading Journal Excel spreadsheet with **36 calculated columns** including:
- **ATR-based 3-stop system** (Stop 1, Stop 2, Stop 3)
- **Take Profit levels** (TP @1X, TP @2X, TP @3X)
- **Portfolio allocation tracking** (% invested at entry and current)
- **ATR/SMA multiples and risk metrics**
- **Trading days calculations** (business days only)
- **Exit transactions** with 7 action types (Stop1/2/3, TP1/2/3, Manual, Other)
- **Realized and unrealized PnL** with complete rollups
- **Historical snapshots** (ATR and SMA at entry preserved)
- **Market data integration** (Polygon.io API)

**This is NOT:**
- An execution platform
- A social trading app
- A predictive analytics tool

**This IS:**
- A deterministic trade journal
- A complete spreadsheet replacement
- A calculation engine with exact Excel parity
- A production-grade risk management system

## 🏗️ Architecture

```
trade_risk_manager/
├── backend/          # FastAPI + Python
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   │   ├── trades_v2.py  # Complete 36-column trade management
│   │   │   └── transactions_v2.py  # 9-column exit tracking
│   │   ├── models/
│   │   │   ├── trade_v2.py   # Complete SQLAlchemy models
│   │   │   └── schemas_v2.py # Pydantic validation
│   │   ├── services/
│   │   │   ├── calculations_v2.py  # Complete WaveRider calculations
│   │   │   └── market_data_v2.py   # Polygon.io integration + historical snapshots
│   │   └── core/             # Configuration
│   └── Dockerfile
├── frontend/         # React + TypeScript
│   ├── src/
│   │   ├── pages/
│   │   │   ├── EntriesPage.tsx      # 36-column grid with color-coded groups
│   │   │   ├── TransactionsPage.tsx # 9-column transaction grid
│   │   │   └── TradeDetailPage.tsx  # Complete trade view
│   │   ├── services/         # API client
│   │   ├── types/            # Complete TypeScript definitions (36 fields)
│   │   └── utils/            # Formatters
│   └── Dockerfile
├── SCHEMA_V2.md      # Complete database schema documentation
├── MIGRATION_TO_V2.md  # Migration guide
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Polygon.io API key (free tier: https://polygon.io/)

### 1. Clone Repository

```bash
git clone <repository-url>
cd trade_risk_manager
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Polygon.io API key
nano .env
```

Required environment variables:
```env
POLYGON_API_KEY=your_polygon_api_key_here
```

### 3. Start Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 5. Stop Application

```bash
docker-compose down

# To also remove database data:
docker-compose down -v
```

## 📊 Features

### Complete WaveRider 3-Stop System (36 Columns)

#### **Column Groups:**

1. **Entry (11 columns)** - Green
   - Trade ID, Ticker, Day % Moved, Current Price
   - % Gain/Loss vs. LoD (PP), Sell Price at Entry
   - Entry/Purchase Price, % Portfolio Invested at Entry
   - % Portfolio Current $, Purchase Date, Shares (Qty)

2. **Entry/Close Dates (2 columns)** - Gray
   - Entry-day Low, Trading Days Open

3. **Risk/ATR (3 columns)** - Cyan
   - Risk/ATR (% above Low Exit)
   - Multiple from SMA at Entry
   - ATR/% Multiple from SMA Current

4. **Take Profit (4 columns)** - Orange
   - TP @ 1X, TP @ 2X, TP @ 3X, SMA10

5. **Stops (5 columns)** - Orange
   - Override, Stop3 (zone), Stop2 (2/3), Stop1 (1/3)
   - Entry% Above Stop3

6. **Indicators (2 columns)** - Cyan
   - ATR(14) (sm), SMA50

7. **Exits (5 columns)** - Yellow
   - Exited Shares, Remaining Shares
   - Total Proceeds, Total Fees, Avg Exit Price

8. **PnL (4 columns)** - Yellow
   - Realized PnL ($), Unrealized PnL ($)
   - Total PnL ($), Status

### Trade Entry

User provides:
- Trade ID (manual, not auto-generated)
- Ticker symbol
- Purchase date, price, shares
- Entry-day low (optional, for Stop3)
- Stop override (optional, overrides Stop3)
- Portfolio size snapshot (optional)

**Auto-calculated on creation (36 fields total):**
- Current market data (price, ATR, SMAs)
- Entry snapshot (ATR at entry, SMA at entry) - **never refreshed**
- 3-stop levels (Stop1, Stop2, Stop3)
- 3 take profit levels (TP @1X/2X/3X)
- Portfolio allocation percentages
- ATR/SMA multiples
- Trading days open
- All risk metrics
- Initial status (OPEN)

### Complete Calculation Formulas

**Stop Levels:**
```
Stop3 = stop_override OR entry_day_low
Distance = purchase_price - Stop3
1R = Distance

Stop2 = purchase_price - (2/3 * Distance)
Stop1 = purchase_price - (1/3 * Distance)
Entry% Above Stop3 = (Distance / Stop3) * 100
```

**Take Profit Levels:**
```
TP @1X = purchase_price + 1R
TP @2X = purchase_price + 2R
TP @3X = purchase_price + 3R
```

**Price Movement:**
```
Day % Moved = ((current_price - purchase_price) / purchase_price) * 100
% Gain/Loss vs. LoD (PP) = ((current_price - purchase_price) / purchase_price) * 100
```

**Portfolio Metrics:**
```
% Portfolio Invested at Entry = ((shares * purchase_price) / portfolio_size) * 100
% Portfolio Current $ = ((shares_remaining * current_price) / portfolio_size) * 100
```

**ATR/SMA Metrics:**
```
Risk/ATR (% above Low Exit) = ((purchase_price - Stop3) / atr_at_entry) * 100
Multiple from SMA at Entry = (purchase_price - sma_at_entry) / atr_at_entry
ATR/% Multiple from SMA Current = (current_price - sma_50) / atr_14
```

**Trading Days:**
```
Trading Days Open = Number of business days between purchase_date and today (excludes weekends)
```

### Exit Transactions (9 Columns)

**Exact 9 columns:**
1. Exit Date
2. Trade ID
3. Action (Stop1/Stop2/Stop3/TP1/TP2/TP3/Manual/Other)
4. Ticker
5. Shares
6. Price
7. Proceeds (auto-calculated)
8. Fees
9. Notes

**Supports:**
- Manual single-entry form with all 7 action types
- CSV bulk upload

**CSV format:**
```csv
exit_date,trade_id,action,ticker,shares,price,fees,notes
2024-01-20,AAPL-001,TP1,AAPL,50,190.25,1.00,Partial exit at TP1
2024-01-21,TSLA-002,Stop2,TSLA,100,245.80,2.50,Hit Stop2
2024-01-22,NVDA-003,Manual,NVDA,75,480.00,1.50,Manual exit
```

### Trade Rollups (Auto-calculated)

For each trade, the following rollups update automatically:
- Shares exited (sum of all transaction shares)
- Shares remaining (initial shares - shares exited)
- Total proceeds (sum of all transaction proceeds)
- Total fees (sum of all transaction fees)
- Average exit price (weighted average)
- Realized PnL (from exited shares)
- Unrealized PnL (from remaining shares)
- Total PnL (realized + unrealized)
- Status: OPEN / PARTIAL / CLOSED

**Rollups update automatically on:**
- Transaction insert
- Transaction update
- Transaction delete
- Market data refresh

### Market Data Integration

**Current Data (refreshed):**
- Current price
- ATR(14), SMA(50), SMA(10)
- Market data updated timestamp

**Entry Snapshot (preserved forever):**
- ATR at entry (captured at purchase_date)
- SMA at entry (captured at purchase_date)

**These values NEVER change after trade creation**, ensuring historical accuracy.

## 🖥️ User Interface

### Entries Page (36-Column Spreadsheet View)

- **Color-coded column groups** matching Google Sheet
- One row per Trade ID
- All 36 calculated fields visible
- Filter by status (OPEN, PARTIAL, CLOSED)
- Click Trade ID to view details
- Create new trades with full optional fields
- Refresh market data
- AG Grid with sorting, filtering, resizing

### Transactions Page (9-Column Grid)

- Exactly 9 columns matching backend schema
- Filter by Trade ID
- Manual entry form with 7 action types
- CSV upload with validation
- Color-coded action badges (Stop1/2/3, TP1/2/3, Manual, Other)
- View proceeds and fees per transaction

### Trade Detail Page

Comprehensive single-trade view:
- Complete entry details (all user inputs)
- Current market data with refresh button
- Entry snapshot (ATR/SMA at entry)
- All stop levels with color coding
- All take profit levels
- Portfolio allocation metrics
- Performance summary (PnL, % gain/loss)
- Trading days open
- List of all exit transactions
- Transaction summary

## 🔧 API Endpoints

### Trades (V2)

```
POST   /api/v1/trades              # Create trade (returns all 36 fields)
GET    /api/v1/trades              # List trades (all 36 fields per trade)
GET    /api/v1/trades/summary      # Get summary stats
GET    /api/v1/trades/{trade_id}   # Get single trade (all 36 fields)
PATCH  /api/v1/trades/{trade_id}   # Update user fields (entry_day_low, stop_override, portfolio_size)
POST   /api/v1/trades/{trade_id}/refresh  # Refresh market data (preserves entry snapshot)
DELETE /api/v1/trades/{trade_id}   # Delete trade (cascades to transactions)
```

### Transactions (V2)

```
POST   /api/v1/transactions              # Create transaction (validates action type)
GET    /api/v1/transactions              # List transactions (9 fields)
GET    /api/v1/transactions/{id}         # Get single transaction
PATCH  /api/v1/transactions/{id}         # Update transaction (recalculates rollups)
DELETE /api/v1/transactions/{id}         # Delete transaction (recalculates rollups)
POST   /api/v1/transactions/upload-csv   # Bulk upload CSV (validates all rows)
```

## 🗄️ Database Schema

PostgreSQL with two main tables:

**trades (36 columns)**
- Primary key: `trade_id` (user-provided VARCHAR)
- **User inputs:** purchase_price, purchase_date, shares, entry_day_low, stop_override, portfolio_size
- **Current market data:** current_price, atr_14, sma_50, sma_10, market_data_updated_at
- **Entry snapshot:** atr_at_entry, sma_at_entry
- **Calculated price metrics:** day_pct_moved, gain_loss_pct_vs_pp, sell_price_at_entry
- **Portfolio metrics:** pct_portfolio_invested_at_entry, pct_portfolio_current
- **Time metrics:** trading_days_open
- **Risk/ATR metrics:** risk_atr_pct_above_low, multiple_from_sma_at_entry, atr_multiple_from_sma_current
- **Stop levels:** stop_3, stop_2, stop_1, entry_pct_above_stop3, one_r
- **Take profit levels:** tp_1x, tp_2x, tp_3x
- **Rollup fields:** shares_exited, shares_remaining, total_proceeds, total_fees, avg_exit_price
- **PnL fields:** realized_pnl, unrealized_pnl, total_pnl
- **Status:** status (OPEN/PARTIAL/CLOSED)
- **Audit:** created_at, updated_at

**transactions (12 columns)**
- Auto-increment ID (primary key)
- Foreign key: `trade_id` (CASCADE delete)
- **Fields:** exit_date, action, ticker, shares, price, fees, notes, proceeds
- **Audit:** created_at, updated_at

See [SCHEMA_V2.md](SCHEMA_V2.md) for complete schema documentation.

## 🔒 Data Validation

**Backend enforces:**
- Trade ID uniqueness
- Positive prices and shares
- Sufficient shares for exits
- Valid action types: Stop1, Stop2, Stop3, TP1, TP2, TP3, Manual, Other
- Stop3 must be below purchase price
- No over-exiting (total exits ≤ initial shares)
- Pydantic v2 validation with field_validator

**Frontend provides:**
- Form validation with all optional fields
- Type checking (TypeScript with 36 fields)
- User feedback for errors
- Error messages from backend

## 🧮 Calculation Engine

All calculations preserve **exact spreadsheet behavior** from the WaveRider 3-Stop Google Sheet.

### Key Principles:
1. **Spreadsheet parity** - formulas match Row 6 exactly
2. **Historical snapshots** - entry ATR/SMA never change
3. **Current data refreshable** - current price/ATR/SMA update on demand
4. **Automatic rollups** - all aggregations update on transaction changes
5. **Decimal precision** - uses Python Decimal for financial accuracy
6. **Business days only** - trading days calculation excludes weekends

### ATR Calculation
```python
# True Range = max(high - low, |high - prev_close|, |low - prev_close|)
# ATR = 14-period simple moving average of True Range
# Uses Polygon.io aggregate bars (1 day)
```

### SMA Calculation
```python
# SMA(N) = Sum of N closing prices / N
# SMA50 = 50-period simple moving average
# SMA10 = 10-period simple moving average
```

### Transaction Proceeds
```python
# Proceeds = (shares * price) - fees
```

### Weighted Average Exit Price
```python
# avg_exit_price = SUM(shares * price) / SUM(shares)
```

### PnL Calculations
```python
# Realized PnL = SUM(proceeds) - (shares_exited * purchase_price)
# Unrealized PnL = (shares_remaining * current_price) - (shares_remaining * purchase_price)
# Total PnL = realized_pnl + unrealized_pnl
```

## 📝 CSV Upload Format

Template for bulk transaction upload (9 columns):

```csv
exit_date,trade_id,action,ticker,shares,price,fees,notes
2024-01-15,AAPL-001,Stop1,AAPL,30,185.00,0.50,Hit Stop1
2024-01-20,AAPL-001,TP1,AAPL,30,192.50,0.50,Took profit at TP1
2024-01-22,TSLA-002,TP2,TSLA,50,260.00,1.00,Hit TP2
2024-01-25,NVDA-003,Manual,NVDA,100,485.00,2.00,Manual exit
```

**Required columns:**
- `exit_date` - Format: YYYY-MM-DD
- `trade_id` - Must exist in trades table
- `action` - Must be: Stop1, Stop2, Stop3, TP1, TP2, TP3, Manual, or Other
- `shares` - Positive integer
- `price` - Positive decimal

**Optional columns:**
- `ticker` - If not provided, copied from parent trade
- `fees` - Default: 0
- `notes` - Free text

## 🧪 Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally (requires PostgreSQL running)
export DATABASE_URL="postgresql://waverider:waverider_password@localhost:5432/waverider_db"
export POLYGON_API_KEY="your_key"
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run locally
export REACT_APP_API_URL="http://localhost:8000/api/v1"
npm start
```

**Note:** TypeScript version 4.9.5 required for react-scripts 5.0.1 compatibility.

## 📦 Production Deployment

### Docker Stack (Swarm)

```bash
docker stack deploy -c docker-compose.yml waverider
```

### Environment Variables

Required:
- `POLYGON_API_KEY` - Market data API key

Optional:
- `APP_ENV` - Environment (development/production)
- `DEBUG` - Enable debug mode (True/False)
- `ALLOWED_ORIGINS` - CORS origins (comma-separated)

## 🐛 Troubleshooting

### TypeScript Version Error

If you see TypeScript compatibility errors with react-scripts 5.0.1:

```bash
cd frontend
npm install typescript@4.9.5
```

### Backend Pydantic ValidationError

If you see `SettingsError` for ALLOWED_ORIGINS, ensure your .env file has:

```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

The Pydantic v2 validator will parse the comma-separated string.

### Database Connection Issues

```bash
# Check database is healthy
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Market Data Not Loading

- Verify `POLYGON_API_KEY` is set in `.env`
- Check API rate limits (free tier: 5 requests/minute)
- View backend logs: `docker-compose logs backend`
- Polygon.io requires historical data access for entry snapshots

## 🔄 Migration from V1 to V2

If you have an existing deployment using the initial implementation, see [MIGRATION_TO_V2.md](MIGRATION_TO_V2.md) for:
- SQL migration script (renames columns, adds 20+ new columns)
- Python data migration script (recalculates all fields)
- Step-by-step instructions
- Rollback plan

**For new installations**, V2 is the default and no migration is needed.

## 📄 License

[Your License Here]

## 🤝 Contributing

This is a deterministic trading journal. Contributions must:
- Preserve exact spreadsheet behavior
- Not simplify calculations
- Not reinterpret formulas
- Maintain all 36 columns
- Follow WaveRider 3-Stop methodology exactly
- Maintain backward compatibility

## 📞 Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review complete schema: [SCHEMA_V2.md](SCHEMA_V2.md)
- Review API docs: http://localhost:8000/docs
- Check backend logs: `docker-compose logs backend`
- Check frontend console: Browser DevTools

---

**Built with accuracy, precision, and complete spreadsheet parity.**

**Version 2 - Complete WaveRider 3-Stop Implementation with 36 Columns**
