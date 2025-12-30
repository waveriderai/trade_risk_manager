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
        Calculate Simple Moving Average locally from DataFrame.
        DEPRECATED: Prefer get_sma_from_api for accuracy.

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

    def get_sma_from_api(
        self,
        ticker: str,
        window: int,
        timestamp: Optional[date] = None
    ) -> Optional[Decimal]:
        """
        Fetch SMA directly from Polygon.io SMA endpoint.

        Uses: GET /v1/indicators/sma/{stockTicker}

        Args:
            ticker: Stock ticker symbol
            window: SMA period (e.g., 10, 50)
            timestamp: Optional date for historical SMA (default: current)

        Returns:
            SMA value as Decimal, or None if unavailable
        """
        try:
            url = f"{self.base_url}/v1/indicators/sma/{ticker}"
            params = {
                "apiKey": self.api_key,
                "timespan": "day",
                "series_type": "close",
                "adjusted": "true",
                "window": window,
                "limit": 1,
            }

            # Add timestamp for historical SMA
            if timestamp:
                params["timestamp.lte"] = timestamp.strftime("%Y-%m-%d")

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            # Extract SMA value from results.values[0].value
            if data.get("results") and data["results"].get("values"):
                values = data["results"]["values"]
                if len(values) > 0:
                    sma_value = values[0].get("value")
                    if sma_value is not None:
                        return Decimal(str(round(sma_value, 4)))

            print(f"No SMA{window} data for {ticker} at {timestamp}")
            return None

        except Exception as e:
            print(f"Error fetching SMA{window} from API for {ticker}: {e}")
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
        result = {
            "atr_14": None,
            "sma_50": None,
            "sma_10": None,
        }

        # Use Polygon SMA API endpoint for SMAs
        result["sma_50"] = self.get_sma_from_api(ticker, window=50, timestamp=target_date)
        result["sma_10"] = self.get_sma_from_api(ticker, window=10, timestamp=target_date)

        # For ATR, still need historical data calculation
        from_date = target_date - timedelta(days=lookback_days)
        to_date = target_date

        df = self.get_historical_data(ticker, from_date, to_date)

        if df is not None and len(df) > 0:
            # Filter to data up to and including target_date
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df = df[df["date"] <= target_date]

            if len(df) > 0:
                result["atr_14"] = self.calculate_atr(df, period=14)

        return result

    def get_current_indicators(
        self,
        ticker: str,
        entry_date: datetime
    ) -> Dict[str, Optional[Decimal]]:
        """
        Fetch current market data and indicators.

        Uses Polygon.io SMA endpoint for SMA values.

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

        # Use Polygon SMA API endpoint for SMAs (current = no timestamp)
        result["sma_50"] = self.get_sma_from_api(ticker, window=50)
        result["sma_10"] = self.get_sma_from_api(ticker, window=10)

        # Get historical data for ATR calculation only
        to_date = datetime.now()
        from_date = entry_date - timedelta(days=30)  # Only need ~20 trading days for ATR14

        df = self.get_historical_data(ticker, from_date, to_date)

        if df is not None and len(df) > 0:
            result["atr_14"] = self.calculate_atr(df, period=14)

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
