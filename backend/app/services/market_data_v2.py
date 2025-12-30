"""
Enhanced market data service for WaveRider 3-Stop system.
Fetches current price, ATR, SMA50, SMA10, and historical snapshots.

Uses Polygon.io API for all market data.
"""
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, Optional, List, Tuple
import requests
import pandas as pd
import numpy as np

from app.core.config import settings


class MarketDataService:
    """Enhanced service for fetching and calculating market data."""

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

        Uses trading days only (not calendar days).
        """
        if df is None or len(df) < period + 1:
            return None

        try:
            df = df.copy()
            df["prev_close"] = df["close"].shift(1)

            df["tr1"] = df["high"] - df["low"]
            df["tr2"] = abs(df["high"] - df["prev_close"])
            df["tr3"] = abs(df["low"] - df["prev_close"])

            df["true_range"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

            # Calculate ATR as simple moving average of TR
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
            period: SMA period (e.g., 10, 50)

        Returns:
            SMA value as Decimal, or None if insufficient data
        """
        if df is None or len(df) < period:
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

    def get_historical_indicators_at_date(
        self,
        ticker: str,
        target_date: date,
        lookback_days: int = 100
    ) -> Dict[str, Optional[Decimal]]:
        """
        Get ATR and SMA values as of a specific historical date.

        This is used to capture entry snapshots (atr_at_entry, sma_at_entry).

        Args:
            ticker: Stock ticker
            target_date: The date to get indicators for
            lookback_days: How many days before target_date to fetch (for calculations)

        Returns:
            Dictionary with: atr_14, sma_50, sma_10
        """
        # Fetch historical data up to target date
        from_date = target_date - timedelta(days=lookback_days)
        to_date = target_date

        df = self.get_historical_data(ticker, from_date, to_date)

        if df is None or len(df) == 0:
            return {
                "atr_14": None,
                "sma_50": None,
                "sma_10": None,
            }

        # Filter to data up to and including target_date
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df[df["date"] <= target_date]

        if len(df) == 0:
            return {
                "atr_14": None,
                "sma_50": None,
                "sma_10": None,
            }

        # Calculate indicators as of target_date
        return {
            "atr_14": self.calculate_atr(df, period=14),
            "sma_50": self.calculate_sma(df, period=50),
            "sma_10": self.calculate_sma(df, period=10),
        }

    def get_current_indicators(
        self,
        ticker: str,
        entry_date: datetime
    ) -> Dict[str, Optional[Decimal]]:
        """
        Fetch current market data and indicators.

        Returns:
            Dictionary with: current_price, atr_14, sma_50, sma_10
        """
        result = {
            "current_price": None,
            "atr_14": None,
            "sma_50": None,
            "sma_10": None,
        }

        # Get current price
        result["current_price"] = self.get_current_price(ticker)

        # Get historical data (need ~70 trading days for SMA50 + ATR14)
        # Account for weekends/holidays: fetch 110 calendar days to be safe
        to_date = datetime.now()
        from_date = entry_date - timedelta(days=110)

        df = self.get_historical_data(ticker, from_date, to_date)

        if df is not None and len(df) > 0:
            # Calculate indicators
            result["atr_14"] = self.calculate_atr(df, period=14)
            result["sma_50"] = self.calculate_sma(df, period=50)
            result["sma_10"] = self.calculate_sma(df, period=10)

        return result

    def get_complete_market_data(
        self,
        ticker: str,
        entry_date: date
    ) -> Tuple[Dict, Dict]:
        """
        Fetch complete market data for a new trade.

        Returns TWO dictionaries:
        1. current_data: Current price, ATR, SMAs
        2. entry_snapshot: ATR and SMA values at entry_date

        This allows capturing both current market state and entry-date snapshot.
        """
        # Convert date to datetime for API calls
        entry_dt = datetime.combine(entry_date, datetime.min.time())

        # Get current indicators
        current_data = self.get_current_indicators(ticker, entry_dt)

        # Get entry snapshot
        entry_snapshot = self.get_historical_indicators_at_date(ticker, entry_date)

        return current_data, entry_snapshot


# Global instance
market_data_service = MarketDataService()
