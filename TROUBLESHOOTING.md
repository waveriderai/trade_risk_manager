# WaveRider Trading Journal - Troubleshooting Guide

## Quick Diagnosis

Run this command to see container status:
```bash
docker-compose ps
```

All containers should show "Up" status. If not, proceed below.

---

## Issue 1: Backend Connection Error (ERR_CONNECTION_RESET)

**Symptoms:**
- Frontend shows "Error loading trades: AxiosError"
- Browser console shows `net::ERR_CONNECTION_RESET` for API calls
- Cannot reach http://localhost:8000

**Diagnosis:**
```bash
# Check backend logs
docker-compose logs backend

# Test backend directly
curl http://localhost:8000/health
```

**Causes & Fixes:**

### A. Backend crashed on startup

**Check logs:**
```bash
docker-compose logs backend --tail 50
```

**Common errors:**

1. **Missing POLYGON_API_KEY** (won't crash, but market data won't work)
   ```bash
   # Edit .env file
   nano .env
   # Add: POLYGON_API_KEY=your_key_here
   ```

2. **Database connection failed**
   ```bash
   # Check database logs
   docker-compose logs db

   # Restart database
   docker-compose restart db

   # Wait 10 seconds, then restart backend
   docker-compose restart backend
   ```

3. **Import errors or Python syntax errors**
   ```bash
   # View full backend logs
   docker-compose logs backend

   # Look for "ModuleNotFoundError" or "SyntaxError"
   ```

### B. Port already in use

**Check if port 8000 is already taken:**
```bash
# On Linux/Mac
lsof -i :8000

# On Windows
netstat -ano | findstr :8000
```

**Fix:**
```bash
# Kill process using port 8000, or
# Change backend port in docker-compose.yml:
#   ports:
#     - "8001:8000"  # Changed from 8000:8000
```

### C. CORS issues

**Symptoms:**
- Backend is running (http://localhost:8000/health works)
- But frontend shows CORS errors in console

**Fix:**
```bash
# Check backend/.env.example
# Ensure ALLOWED_ORIGINS includes frontend URL
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## Issue 2: Frontend TypeScript Errors

**Symptoms:**
- `docker-compose up` fails during frontend build
- Error about TypeScript version incompatibility

**Fix:**

Already fixed in latest version. If you see this:
```bash
# Edit frontend/package.json
# Change: "typescript": "^5.3.3"
# To:     "typescript": "4.9.5"

# Rebuild
docker-compose down
docker-compose up --build
```

---

## Issue 3: Database Connection Errors

**Symptoms:**
- Backend logs show `connection refused` or `could not connect to server`
- Backend keeps restarting

**Fix:**

```bash
# 1. Stop all containers
docker-compose down

# 2. Remove volumes (WARNING: deletes all data)
docker-compose down -v

# 3. Start fresh
docker-compose up -d

# 4. Watch logs
docker-compose logs -f
```

---

## Issue 4: Frontend Build Errors

**Symptoms:**
- Frontend container exits immediately
- Logs show `npm install` or `npm start` errors

**Fix:**

```bash
# Check frontend logs
docker-compose logs frontend

# Common fixes:

# 1. Clear node_modules and rebuild
docker-compose down
docker-compose build --no-cache frontend
docker-compose up -d

# 2. Check if port 3000 is available
lsof -i :3000  # Linux/Mac
netstat -ano | findstr :3000  # Windows
```

---

## Issue 5: "No trades showing" after successful startup

**Symptoms:**
- Application loads successfully
- No errors in console
- But entries page is empty

**This is normal!** You need to create trades first.

**Steps:**

1. Click "**+ New Trade**" button on Entries page
2. Fill in:
   - Trade ID (e.g., "AAPL-001")
   - Ticker (e.g., "AAPL")
   - Entry date
   - Entry price
   - Entry shares
   - Optional: Low of Day
3. Click "Create Trade"
4. Wait for market data to load (~5-10 seconds)

---

## Issue 6: Market Data Not Loading

**Symptoms:**
- Trade created successfully
- But `current_price`, `atr_14`, `sma_50`, `sma_10` show as `-` (empty)
- "Market Data Updated" shows `-`

**Causes:**

### A. Missing or Invalid API Key

```bash
# Check .env file
cat .env | grep POLYGON_API_KEY

# Should show your actual key, not "your_polygon_api_key_here"
# Get free key at: https://polygon.io/
```

### B. API Rate Limit (Free Tier)

Free tier allows **5 requests per minute**.

**Wait 1 minute and try:**
```bash
# Refresh market data via API
curl -X POST http://localhost:8000/api/v1/trades/AAPL-001/refresh
```

Or click "Refresh" button in Trade Detail page.

### C. Invalid Ticker Symbol

Polygon.io only has data for US stocks. Verify:
- Ticker is correct (e.g., "AAPL" not "APPLE")
- Stock is publicly traded in US markets

---

## Complete Reset (Nuclear Option)

If all else fails:

```bash
# 1. Stop and remove everything
docker-compose down -v

# 2. Remove Docker images
docker-compose down --rmi all

# 3. Clean build
docker-compose build --no-cache

# 4. Start fresh
docker-compose up -d

# 5. Watch logs for errors
docker-compose logs -f
```

---

## Checking Service Health

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "api_version": "/api/v1"
}
```

### Database Health Check
```bash
docker-compose exec db psql -U waverider -d waverider_db -c "SELECT 1;"
```

Expected response:
```
 ?column?
----------
        1
```

### Frontend Health Check
Open browser to: http://localhost:3000

Should show WaveRider navigation and Entries page.

---

## Viewing Logs

### All services
```bash
docker-compose logs -f
```

### Specific service
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Last N lines
```bash
docker-compose logs backend --tail 50
```

---

## Common Docker Commands

```bash
# View running containers
docker-compose ps

# Restart a service
docker-compose restart backend

# Restart all services
docker-compose restart

# Stop all services
docker-compose stop

# Start all services
docker-compose start

# View resource usage
docker stats

# Enter backend container shell
docker-compose exec backend bash

# Enter database shell
docker-compose exec db psql -U waverider -d waverider_db
```

---

## Verifying API Endpoints

### List all trades
```bash
curl http://localhost:8000/api/v1/trades
```

### Create a test trade
```bash
curl -X POST http://localhost:8000/api/v1/trades \
  -H "Content-Type: application/json" \
  -d '{
    "trade_id": "TEST-001",
    "ticker": "AAPL",
    "entry_date": "2024-01-15",
    "entry_price": 185.50,
    "entry_shares": 100,
    "low_of_day": 184.20
  }'
```

### Get API documentation
Open: http://localhost:8000/docs

---

## Still Having Issues?

1. **Check backend logs** for detailed error messages
   ```bash
   docker-compose logs backend --tail 100
   ```

2. **Verify environment variables**
   ```bash
   cat .env
   ```

3. **Check Docker versions**
   ```bash
   docker --version
   docker-compose --version
   ```

4. **Verify ports are available**
   ```bash
   # Ports 3000, 5432, 8000 must be free
   netstat -tuln | grep -E "3000|5432|8000"
   ```

5. **Check Docker resources**
   - Ensure Docker has enough memory (minimum 2GB)
   - Ensure Docker has enough disk space

---

## Getting Help

If you're still stuck, gather this information:

```bash
# 1. Container status
docker-compose ps

# 2. Backend logs
docker-compose logs backend --tail 100 > backend_logs.txt

# 3. Frontend logs
docker-compose logs frontend --tail 100 > frontend_logs.txt

# 4. Database logs
docker-compose logs db --tail 100 > db_logs.txt

# 5. Environment check
cat .env.example
```

Then review the logs for specific error messages.
