#!/bin/bash
# WaveRider Troubleshooting Script

echo "=== WaveRider Trading Journal - Diagnostic Check ==="
echo ""

echo "1. Checking Docker containers..."
docker-compose ps
echo ""

echo "2. Checking backend logs (last 30 lines)..."
docker-compose logs backend --tail 30
echo ""

echo "3. Checking frontend logs (last 30 lines)..."
docker-compose logs frontend --tail 30
echo ""

echo "4. Checking database logs (last 30 lines)..."
docker-compose logs db --tail 30
echo ""

echo "5. Testing backend API directly..."
curl -v http://localhost:8000/health 2>&1 | grep -E "HTTP|status|healthy"
echo ""

echo "6. Testing backend API /trades endpoint..."
curl -v http://localhost:8000/api/v1/trades 2>&1 | head -20
echo ""

echo "7. Checking if ports are listening..."
netstat -tuln | grep -E "8000|3000|5432"
echo ""

echo "=== Diagnostic complete ==="
echo ""
echo "Common fixes:"
echo "  - Backend not starting: Check POLYGON_API_KEY in .env"
echo "  - Connection refused: Restart containers with 'docker-compose restart'"
echo "  - Database errors: Check 'docker-compose logs db'"
echo "  - CORS errors: Check ALLOWED_ORIGINS in backend/.env.example"
