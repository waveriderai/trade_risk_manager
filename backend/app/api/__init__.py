"""
API routes package.
"""
from fastapi import APIRouter
from app.api import trades, transactions

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(trades.router)
api_router.include_router(transactions.router)

__all__ = ["api_router"]
