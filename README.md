# WaveRider 3-Stop Trading Journal

A production-ready, Docker-deployable web application that replaces Excel-based trading journals with a deterministic, spreadsheet-parity system for tracking ATR-based 3-stop trades.

## 🎯 Purpose

This application digitizes an Excel trading journal that tracks:
- Trade entries with ATR-based stop levels (Stop 1, Stop 2, Stop 3)
- Partial exits and complete exits
- Realized and unrealized PnL
- R-multiples and performance metrics
- Trade lifecycle status (OPEN, PARTIAL, CLOSED)

**This is NOT:**
- An execution platform
- A social trading app
- A predictive analytics tool

**This IS:**
- A deterministic trade journal
- A spreadsheet replacement
- A calculation engine with exact Excel parity

## 🏗️ Architecture

```
waverider/
├── backend/          # FastAPI + Python
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── models/   # SQLAlchemy models
│   │   ├── services/ # Business logic
│   │   └── core/     # Configuration
│   └── Dockerfile
├── frontend/         # React + TypeScript
│   ├── src/
│   │   ├── pages/    # Main UI pages
│   │   ├── services/ # API client
│   │   ├── types/    # TypeScript definitions
│   │   └── utils/    # Formatters
│   └── Dockerfile
├── database/         # PostgreSQL
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

### Trade Entry

- User-provided Trade ID (manual, not auto-generated)
- Ticker symbol
- Entry date, price, shares
- Optional Low-of-Day for Stop3 calculation
- Optional Stop3 override
- Optional portfolio size snapshot

**Auto-calculated on creation:**
- Current price (from Polygon.io)
- ATR(14), SMA(50), SMA(10)
- Stop levels (Stop 1, Stop 2, Stop 3)
- 1R distance
- Initial status (OPEN)

### Stop Level Calculations

```
Stop3 = stop3_override OR low_of_day
Stop2 = entry_price - (2/3 * (entry_price - Stop3))
Stop1 = entry_price - (1/3 * (entry_price - Stop3))
1R    = entry_price - Stop3
```

### Exit Transactions

Manual journal entries for exits:
- Transaction date
- Trade ID (references existing trade)
- Action: Stop1 / Stop2 / Stop3 / Profit / Other
- Shares (validated against available)
- Exit price
- Optional fees
- Optional notes

**Supports:**
- Manual single-entry form
- CSV bulk upload

CSV format:
```csv
trade_id,transaction_date,action,shares,price,fees,notes
AAPL-001,2024-01-20,Stop2,50,190.25,1.00,Partial exit
```

### Trade Rollups (Auto-calculated)

For each trade:
- Total shares exited
- Shares remaining
- Weighted average exit price
- Realized PnL (from closed positions)
- Unrealized PnL (from remaining shares)
- Total PnL
- Percent gain/loss
- R-multiple: `total_pnl / (entry_shares * 1R)`
- Status: OPEN / PARTIAL / CLOSED

**Rollups update automatically on:**
- Transaction insert
- Transaction update
- Transaction delete
- Market data refresh

### Market Data Refresh

- Manual refresh per trade
- Fetches latest price, ATR, SMAs
- Updates unrealized PnL
- Timestamp tracked

## 🖥️ User Interface

### Entries Page

Spreadsheet-style grid showing all trades:
- One row per Trade ID
- All calculated fields visible
- Filter by status (OPEN, PARTIAL, CLOSED)
- Click Trade ID to view details
- Create new trades
- Refresh market data

### Transactions Page

List of all exit transactions:
- Filter by Trade ID
- Manual entry form
- CSV upload
- View proceeds and PnL per transaction

### Trade Detail Page

Comprehensive single-trade view:
- Entry details
- Market data
- Stop levels
- Performance summary
- List of all exit transactions
- Refresh market data button

## 🔧 API Endpoints

### Trades

```
POST   /api/v1/trades              # Create trade
GET    /api/v1/trades              # List trades (with filters)
GET    /api/v1/trades/summary      # Get summary stats
GET    /api/v1/trades/{trade_id}   # Get single trade
PATCH  /api/v1/trades/{trade_id}   # Update user fields
POST   /api/v1/trades/{trade_id}/refresh  # Refresh market data
DELETE /api/v1/trades/{trade_id}   # Delete trade
```

### Transactions

```
POST   /api/v1/transactions              # Create transaction
GET    /api/v1/transactions              # List transactions (with filters)
GET    /api/v1/transactions/{id}         # Get single transaction
PATCH  /api/v1/transactions/{id}         # Update transaction
DELETE /api/v1/transactions/{id}         # Delete transaction
POST   /api/v1/transactions/upload-csv   # Bulk upload CSV
```

## 🗄️ Database

PostgreSQL with two main tables:

**trades**
- Primary key: `trade_id` (user-provided)
- Entry details + user inputs
- Market data (refreshed)
- Calculated stops
- Rollup calculations

**transactions**
- Auto-increment ID
- Foreign key: `trade_id` (CASCADE delete)
- Transaction details
- Calculated proceeds and PnL

See [SCHEMA.md](SCHEMA.md) for complete schema documentation.

## 🔒 Data Validation

**Backend enforces:**
- Trade ID uniqueness
- Positive prices and shares
- Sufficient shares for exits
- Valid action types
- Stop3 must be below entry price
- No over-exiting (total exits ≤ entry shares)

**Frontend provides:**
- Form validation
- Type checking (TypeScript)
- User feedback
- Error messages

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

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

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

## 🧮 Calculation Logic

All calculations preserve **exact spreadsheet behavior**.

### ATR Calculation

```python
# True Range = max(high - low, |high - prev_close|, |low - prev_close|)
# ATR = 14-period simple moving average of True Range
# Uses trading days only (not calendar days)
```

### R-Multiple Calculation

```python
# R-Multiple = total_pnl / (entry_shares * 1R_distance)
# Where 1R = entry_price - Stop3
```

### Transaction PnL

```python
# Proceeds = (shares * exit_price) - fees
# PnL = proceeds - (shares * entry_price)
```

### Weighted Average Exit Price

```python
# Weighted_Avg_Exit = SUM(shares * price) / SUM(shares)
```

## 📝 CSV Upload Format

Template for bulk transaction upload:

```csv
trade_id,transaction_date,action,shares,price,fees,notes
AAPL-001,2024-01-15,Stop1,30,185.00,0.50,Hit Stop1
AAPL-001,2024-01-20,Stop2,30,182.50,0.50,Hit Stop2
TSLA-002,2024-01-22,Profit,100,250.00,2.00,Full exit profit
```

**Required columns:**
- `trade_id` - Must exist in trades table
- `transaction_date` - Format: YYYY-MM-DD
- `action` - Must be: Stop1, Stop2, Stop3, Profit, or Other
- `shares` - Positive integer
- `price` - Positive decimal

**Optional columns:**
- `fees` - Default: 0
- `notes` - Free text

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check database connection
docker-compose logs db

# Check backend logs
docker-compose logs backend
```

### Frontend build errors

```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Market data not loading

- Verify `POLYGON_API_KEY` is set in `.env`
- Check API rate limits (free tier: 5 requests/minute)
- View backend logs: `docker-compose logs backend`

### Database connection issues

```bash
# Restart database
docker-compose restart db

# Check database is healthy
docker-compose ps
```

## 🔄 Migrating from Excel

1. Export trades from Excel as CSV
2. Map columns to match trade schema
3. Use API or bulk import to create trades
4. Export transactions from Excel as CSV
5. Use CSV upload feature for transactions
6. Verify rollup calculations match Excel

## 📄 License

[Your License Here]

## 🤝 Contributing

This is a deterministic trading journal. Contributions must:
- Preserve exact spreadsheet behavior
- Not simplify calculations
- Not reinterpret formulas
- Maintain backward compatibility

## 📞 Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review API docs: http://localhost:8000/docs
- Check backend logs: `docker-compose logs backend`
- Check frontend console: Browser DevTools

---

**Built with accuracy, precision, and spreadsheet parity in mind.**
