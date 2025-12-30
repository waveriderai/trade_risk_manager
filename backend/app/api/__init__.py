"""
API routes package - Using V2 (Complete WaveRider 3-Stop).
"""
from fastapi import APIRouter
from app.api import trades_v2, transactions_v2

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(trades_v2.router)
api_router.include_router(transactions_v2.router)

__all__ = ["api_router"]
