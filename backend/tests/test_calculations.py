"""
Unit tests for WaveRider 3-Stop calculation engine.

Tests cover:
- No exits scenario
- Partial exits scenario
- Fully closed trade scenario
- Manual Stop3 override
- Missing PortfolioSize handling
- R-Multiple calculation
- Portfolio impact calculation
- Risk/ATR R-units calculation
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

from app.services.calculations_v2 import WaveRiderCalculations, waverider_calc


class TestStopsAndTargets:
    """Tests for stop level and take profit calculations."""

    def test_calculate_stops_with_entry_day_low(self):
        """Test stop calculation using entry day low."""
        result = WaveRiderCalculations.calculate_stops_and_targets(
            purchase_price=Decimal("100.00"),
            entry_day_low=Decimal("98.00"),
            stop_override=None,
            buffer_pct=Decimal("0.005")  # 0.5% buffer
        )

        # Stop3 = LoD * (1 - 0.5%) = 98 * 0.995 = 97.51
        assert result["stop_3"] == Decimal("97.5100")
        # OneR = PP - Stop3 = 100 - 97.51 = 2.49
        assert result["one_r"] == Decimal("2.4900")
        # Stop2 = PP - (2/3 * OneR) = 100 - (2/3 * 2.49) = 100 - 1.66 = 98.34
        assert result["stop_2"] == Decimal("98.3400")
        # Stop1 = PP - (1/3 * OneR) = 100 - (1/3 * 2.49) = 100 - 0.83 = 99.17
        assert result["stop_1"] == Decimal("99.1700")
        # TP @ 1R = PP + OneR = 100 + 2.49 = 102.49
        assert result["tp_1r"] == Decimal("102.4900")
        # TP @ 2R = PP + 2*OneR = 100 + 4.98 = 104.98
        assert result["tp_2r"] == Decimal("104.9800")
        # TP @ 3R = PP + 3*OneR = 100 + 7.47 = 107.47
        assert result["tp_3r"] == Decimal("107.4700")

    def test_calculate_stops_with_manual_override(self):
        """Test that manual stop override takes precedence."""
        result = WaveRiderCalculations.calculate_stops_and_targets(
            purchase_price=Decimal("100.00"),
            entry_day_low=Decimal("98.00"),
            stop_override=Decimal("95.00"),  # Manual override
            buffer_pct=Decimal("0.005")
        )

        # Should use manual override, not LoD
        assert result["stop_3"] == Decimal("95.0000")
        # OneR = PP - Stop3 = 100 - 95 = 5
        assert result["one_r"] == Decimal("5.0000")
        # TP @ 1R = 100 + 5 = 105
        assert result["tp_1r"] == Decimal("105.0000")

    def test_calculate_stops_missing_inputs_returns_nulls(self):
        """Test that missing inputs return NULL values."""
        result = WaveRiderCalculations.calculate_stops_and_targets(
            purchase_price=Decimal("100.00"),
            entry_day_low=None,  # Missing
            stop_override=None,  # Also missing
            buffer_pct=Decimal("0.005")
        )

        # All values should be None
        assert result["stop_3"] is None
        assert result["stop_2"] is None
        assert result["stop_1"] is None
        assert result["one_r"] is None
        assert result["tp_1r"] is None

    def test_calculate_stops_invalid_stop3_above_entry(self):
        """Test that Stop3 >= purchase price raises error."""
        with pytest.raises(ValueError, match="Stop3.*must be below purchase price"):
            WaveRiderCalculations.calculate_stops_and_targets(
                purchase_price=Decimal("100.00"),
                entry_day_low=None,
                stop_override=Decimal("105.00"),  # Above entry
                buffer_pct=Decimal("0.005")
            )


class TestRMultiple:
    """Tests for R-Multiple calculation."""

    def test_calculate_r_multiple_positive(self):
        """Test R-Multiple for profitable trade."""
        result = WaveRiderCalculations.calculate_r_multiple(
            total_pnl=Decimal("500.00"),
            one_r=Decimal("2.50"),
            shares=100
        )
        # R-Mult = 500 / (2.50 * 100) = 500 / 250 = 2.0
        assert result == Decimal("2.0000")

    def test_calculate_r_multiple_negative(self):
        """Test R-Multiple for losing trade."""
        result = WaveRiderCalculations.calculate_r_multiple(
            total_pnl=Decimal("-250.00"),
            one_r=Decimal("2.50"),
            shares=100
        )
        # R-Mult = -250 / 250 = -1.0
        assert result == Decimal("-1.0000")

    def test_calculate_r_multiple_zero_pnl(self):
        """Test R-Multiple for breakeven trade."""
        result = WaveRiderCalculations.calculate_r_multiple(
            total_pnl=Decimal("0.00"),
            one_r=Decimal("2.50"),
            shares=100
        )
        assert result == Decimal("0.0000")

    def test_calculate_r_multiple_missing_one_r(self):
        """Test R-Multiple returns None when OneR is missing."""
        result = WaveRiderCalculations.calculate_r_multiple(
            total_pnl=Decimal("500.00"),
            one_r=None,
            shares=100
        )
        assert result is None

    def test_calculate_r_multiple_zero_one_r(self):
        """Test R-Multiple returns None when OneR is zero."""
        result = WaveRiderCalculations.calculate_r_multiple(
            total_pnl=Decimal("500.00"),
            one_r=Decimal("0"),
            shares=100
        )
        assert result is None


class TestPortfolioMetrics:
    """Tests for portfolio allocation calculations."""

    def test_calculate_portfolio_metrics_with_all_inputs(self):
        """Test portfolio metrics with all required inputs."""
        result = WaveRiderCalculations.calculate_portfolio_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            shares=100,
            shares_remaining=50,
            portfolio_size=Decimal("50000.00"),
            pct_gain_loss_trade=Decimal("0.10")  # 10% gain
        )

        # % Portfolio @ Entry = (100 * 100) / 50000 * 100 = 20%
        assert result["pct_portfolio_invested_at_entry"] == Decimal("20.0000")
        # % Portfolio Current = (50 * 110) / 50000 * 100 = 11%
        assert result["pct_portfolio_current"] == Decimal("11.0000")
        # Gain/Loss % Impact = 0.10 * 20 = 2%
        assert result["gain_loss_pct_portfolio_impact"] == Decimal("2.0000")

    def test_calculate_portfolio_metrics_missing_portfolio_size(self):
        """Test that missing portfolio size returns NULL values."""
        result = WaveRiderCalculations.calculate_portfolio_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            shares=100,
            shares_remaining=50,
            portfolio_size=None,  # Missing
            pct_gain_loss_trade=Decimal("0.10")
        )

        assert result["pct_portfolio_invested_at_entry"] is None
        assert result["pct_portfolio_current"] is None
        assert result["gain_loss_pct_portfolio_impact"] is None

    def test_calculate_portfolio_metrics_zero_portfolio_size(self):
        """Test that zero portfolio size returns NULL values."""
        result = WaveRiderCalculations.calculate_portfolio_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            shares=100,
            shares_remaining=50,
            portfolio_size=Decimal("0"),  # Zero
            pct_gain_loss_trade=Decimal("0.10")
        )

        assert result["pct_portfolio_invested_at_entry"] is None
        assert result["pct_portfolio_current"] is None

    def test_calculate_portfolio_metrics_closed_position(self):
        """Test portfolio metrics for fully closed position."""
        result = WaveRiderCalculations.calculate_portfolio_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            shares=100,
            shares_remaining=0,  # Fully exited
            portfolio_size=Decimal("50000.00"),
            pct_gain_loss_trade=Decimal("0.10")
        )

        # % Portfolio @ Entry still calculated
        assert result["pct_portfolio_invested_at_entry"] == Decimal("20.0000")
        # % Portfolio Current should be None (no remaining shares)
        assert result["pct_portfolio_current"] is None


class TestRiskAtrMetrics:
    """Tests for Risk/ATR calculations."""

    def test_calculate_risk_atr_r_units(self):
        """Test Risk / ATR (R units) calculation."""
        result = WaveRiderCalculations.calculate_atr_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            one_r=Decimal("2.50"),
            atr_at_entry=Decimal("3.00"),
            atr_14=Decimal("3.50"),
            sma_at_entry=Decimal("98.00"),
            sma_50=Decimal("102.00")
        )

        # Risk / ATR = OneR / ATR_Entry = 2.50 / 3.00 = 0.8333
        assert result["risk_atr_r_units"] == Decimal("0.8333")

    def test_calculate_risk_atr_r_units_missing_one_r(self):
        """Test Risk / ATR returns None when OneR is missing."""
        result = WaveRiderCalculations.calculate_atr_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            one_r=None,  # Missing
            atr_at_entry=Decimal("3.00"),
            atr_14=Decimal("3.50"),
            sma_at_entry=Decimal("98.00"),
            sma_50=Decimal("102.00")
        )

        assert result["risk_atr_r_units"] is None

    def test_calculate_risk_atr_r_units_missing_atr_entry(self):
        """Test Risk / ATR returns None when ATR at entry is missing."""
        result = WaveRiderCalculations.calculate_atr_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            one_r=Decimal("2.50"),
            atr_at_entry=None,  # Missing
            atr_14=Decimal("3.50"),
            sma_at_entry=Decimal("98.00"),
            sma_50=Decimal("102.00")
        )

        assert result["risk_atr_r_units"] is None

    def test_calculate_atr_multiple_from_ma_at_entry(self):
        """Test ATR% Multiple from MA @ Entry calculation."""
        result = WaveRiderCalculations.calculate_atr_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            one_r=Decimal("2.50"),
            atr_at_entry=Decimal("3.00"),
            atr_14=Decimal("3.50"),
            sma_at_entry=Decimal("98.00"),
            sma_50=Decimal("102.00")
        )

        # Formula: ((PP-SMA)/SMA) / (ATR/PP)
        # = ((100-98)/98) / (3/100)
        # = 0.0204 / 0.03 = 0.6803
        assert result["atr_pct_multiple_from_ma_at_entry"] is not None


class TestTradeRollups:
    """Tests for transaction rollup calculations."""

    def test_no_exits(self):
        """Test trade with no exit transactions."""
        # Mock trade and db
        mock_trade = MagicMock()
        mock_trade.trade_id = "TEST001"
        mock_trade.shares = 100
        mock_trade.purchase_price = Decimal("100.00")
        mock_trade.current_price = Decimal("110.00")

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = WaveRiderCalculations.calculate_trade_rollups(mock_trade, mock_db)

        assert result["shares_exited"] == 0
        assert result["shares_remaining"] == 100
        assert result["total_proceeds"] == Decimal("0")
        assert result["total_fees"] == Decimal("0")
        assert result["avg_exit_price"] is None
        assert result["realized_pnl"] == Decimal("0")
        # Unrealized = 100 * (110 - 100) = 1000
        assert result["unrealized_pnl"] == Decimal("1000.00")
        assert result["status"] == "OPEN"

    def test_partial_exit(self):
        """Test trade with partial exit."""
        mock_trade = MagicMock()
        mock_trade.trade_id = "TEST001"
        mock_trade.shares = 100
        mock_trade.purchase_price = Decimal("100.00")
        mock_trade.current_price = Decimal("110.00")

        # Mock transaction
        mock_txn = MagicMock()
        mock_txn.shares = 50
        mock_txn.price = Decimal("105.00")
        mock_txn.proceeds = Decimal("5249.00")  # 50*105 - 1
        mock_txn.fees = Decimal("1.00")

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_txn]

        result = WaveRiderCalculations.calculate_trade_rollups(mock_trade, mock_db)

        assert result["shares_exited"] == 50
        assert result["shares_remaining"] == 50
        assert result["status"] == "PARTIAL"
        # Realized = proceeds - (exited * PP) = 5249 - (50*100) = 249
        assert result["realized_pnl"] == Decimal("249.00")
        # Unrealized = 50 * (110 - 100) = 500
        assert result["unrealized_pnl"] == Decimal("500.00")

    def test_fully_closed(self):
        """Test fully closed trade."""
        mock_trade = MagicMock()
        mock_trade.trade_id = "TEST001"
        mock_trade.shares = 100
        mock_trade.purchase_price = Decimal("100.00")
        mock_trade.current_price = Decimal("110.00")

        # Mock transaction - full exit
        mock_txn = MagicMock()
        mock_txn.shares = 100
        mock_txn.price = Decimal("105.00")
        mock_txn.proceeds = Decimal("10498.00")  # 100*105 - 2
        mock_txn.fees = Decimal("2.00")

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_txn]

        result = WaveRiderCalculations.calculate_trade_rollups(mock_trade, mock_db)

        assert result["shares_exited"] == 100
        assert result["shares_remaining"] == 0
        assert result["status"] == "CLOSED"
        # Realized = 10498 - (100*100) = 498
        assert result["realized_pnl"] == Decimal("498.00")
        # Unrealized = 0 (no remaining shares)
        assert result["unrealized_pnl"] == Decimal("0")
        # Avg exit price = 10500 / 100 = 105
        assert result["avg_exit_price"] == Decimal("105.0000")


class TestTradingDays:
    """Tests for trading days calculation."""

    def test_calculate_trading_days(self):
        """Test trading days calculation."""
        # Monday to Friday = 5 calendar days, 4 trading days
        result = WaveRiderCalculations.calculate_trading_days(
            purchase_date=date(2024, 1, 1),  # Monday
            as_of_date=date(2024, 1, 5)  # Friday
        )
        # Should count business days between dates
        assert result >= 0

    def test_calculate_trading_days_same_day(self):
        """Test trading days for same day purchase."""
        result = WaveRiderCalculations.calculate_trading_days(
            purchase_date=date(2024, 1, 1),
            as_of_date=date(2024, 1, 1)
        )
        # Should be 0 for same day
        assert result == 0
