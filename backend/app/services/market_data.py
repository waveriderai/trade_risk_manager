"""
Market data service using Polygon.io API.
Fetches current price, ATR, SMA data.

IMPORTANT: All calculations preserve Excel spreadsheet behavior.
DO NOT simplify or reinterpret formulas.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional, List
import requests
import pandas as pd
import numpy as np

from app.core.config import settings


class MarketDataService:
    """Service for fetching and calculating market data."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Polygon.io API key."""
        self.api_key = api_key or settings.POLYGON_API_KEY
        self.base_url = "https://api.polygon.io"

    def get_current_price(self, ticker: str) -> Optional[Decimal]:
        """
        Fetch current/latest price for a ticker.
        Uses previous close if market is closed.
        """
        try:
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/prev"
            params = {"apiKey": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("results"):
                close_price = data["results"][0]["c"]
                return Decimal(str(close_price))

        except Exception as e:
            print(f"Error fetching current price for {ticker}: {e}")
            return None

        return None

    def get_historical_data(
        self,
        ticker: str,
        from_date: datetime,
        to_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical daily OHLCV data.
        Returns DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            # Format dates for API
            from_str = from_date.strftime("%Y-%m-%d")
            to_str = to_date.strftime("%Y-%m-%d")

            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{from_str}/{to_str}"
            params = {
                "apiKey": self.api_key,
                "adjusted": "true",
                "sort": "asc",
                "limit": 50000
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data.get("results"):
                print(f"No historical data for {ticker}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data["results"])
            df["date"] = pd.to_datetime(df["t"], unit="ms")
            df = df.rename(columns={
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume"
            })

            # Select and order columns
            df = df[["date", "open", "high", "low", "close", "volume"]]
            df = df.sort_values("date").reset_index(drop=True)

            return df

        except Exception as e:
            print(f"Error fetching historical data for {ticker}: {e}")
            return None

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[Decimal]:
        """
        Calculate Average True Range (ATR).

        Formula (matches Excel ATR calculation):
        1. True Range (TR) = max(high - low, abs(high - prev_close), abs(low - prev_close))
        2. ATR = average of TR over period

        IMPORTANT: Uses trading days only (not calendar days).

        Args:
            df: DataFrame with columns: high, low, close
            period: ATR period (default 14)

        Returns:
            ATR value as Decimal, or None if insufficient data
        """
        if df is None or len(df) < period + 1:
            print(f"Insufficient data for ATR calculation (need {period + 1}, got {len(df) if df is not None else 0})")
            return None

        try:
            # Calculate True Range
            df = df.copy()
            df["prev_close"] = df["close"].shift(1)

            df["tr1"] = df["high"] - df["low"]
            df["tr2"] = abs(df["high"] - df["prev_close"])
            df["tr3"] = abs(df["low"] - df["prev_close"])

            df["true_range"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

            # Calculate ATR as simple moving average of TR
            # (First ATR is SMA, subsequent values use Wilder's smoothing in real-time systems,
            # but for snapshot calculation, SMA matches Excel behavior)
            atr_series = df["true_range"].rolling(window=period).mean()

            # Get most recent ATR
            atr_value = atr_series.iloc[-1]

            if pd.isna(atr_value):
                return None

            return Decimal(str(round(atr_value, 4)))

        except Exception as e:
            print(f"Error calculating ATR: {e}")
            return None

    def calculate_sma(self, df: pd.DataFrame, period: int) -> Optional[Decimal]:
        """
        Calculate Simple Moving Average.

        Args:
            df: DataFrame with 'close' column
            period: SMA period (e.g., 50 for SMA50)

        Returns:
            SMA value as Decimal, or None if insufficient data
        """
        if df is None or len(df) < period:
            print(f"Insufficient data for SMA{period} calculation (need {period}, got {len(df) if df is not None else 0})")
            return None

        try:
            sma_series = df["close"].rolling(window=period).mean()
            sma_value = sma_series.iloc[-1]

            if pd.isna(sma_value):
                return None

            return Decimal(str(round(sma_value, 4)))

        except Exception as e:
            print(f"Error calculating SMA{period}: {e}")
            return None

    def get_market_data_for_trade(
        self,
        ticker: str,
        entry_date: datetime
    ) -> Dict[str, Optional[Decimal]]:
        """
        Fetch all market data needed for a trade.

        Returns:
            Dictionary with keys: current_price, atr_14, sma_50, sma_10
        """
        result = {
            "current_price": None,
            "atr_14": None,
            "sma_50": None,
            "sma_10": None,
        }

        # Get current price
        result["current_price"] = self.get_current_price(ticker)

        # Get historical data (need ~60 trading days for SMA50 + ATR14)
        # Account for weekends/holidays: fetch 90 calendar days to be safe
        to_date = datetime.now()
        from_date = entry_date - timedelta(days=90)

        df = self.get_historical_data(ticker, from_date, to_date)

        if df is not None and len(df) > 0:
            # Calculate ATR(14)
            result["atr_14"] = self.calculate_atr(df, period=14)

            # Calculate SMA(50)
            result["sma_50"] = self.calculate_sma(df, period=50)

            # Calculate SMA(10)
            result["sma_10"] = self.calculate_sma(df, period=10)

        return result


# Global instance
market_data_service = MarketDataService()
