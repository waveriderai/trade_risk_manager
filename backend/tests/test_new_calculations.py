"""
Unit tests for newly implemented WaveRider calculations.

Tests cover:
- Gain/Loss % Portfolio Impact
- Risk / ATR (R units)
- R-Multiple
- Edge cases (NULL handling, missing inputs)
"""
import pytest
from decimal import Decimal
from datetime import date

from app.services.calculations_v2 import WaveRiderCalculations


class TestGainLossPortfolioImpact:
    """Test Gain/Loss % Portfolio Impact calculation."""

    def test_gain_loss_portfolio_impact_positive(self):
        """Test positive gain impact on portfolio."""
        # Setup: 10% gain on 5% portfolio allocation = 0.5% portfolio impact
        pct_gain_loss_trade = Decimal("0.10")  # 10% gain
        pct_portfolio_at_entry = Decimal("5.0")  # 5% of portfolio
        
        result = WaveRiderCalculations.calculate_portfolio_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            shares=100,
            shares_remaining=100,
            portfolio_size=Decimal("200000.00"),
            pct_gain_loss_trade=pct_gain_loss_trade
        )
        
        assert result["gain_loss_pct_portfolio_impact"] is not None
        # 10% * 5% = 0.5%
        expected = pct_gain_loss_trade * pct_portfolio_at_entry
        assert result["gain_loss_pct_portfolio_impact"] == expected.quantize(Decimal("0.0001"))

    def test_gain_loss_portfolio_impact_negative(self):
        """Test negative loss impact on portfolio."""
        pct_gain_loss_trade = Decimal("-0.05")  # -5% loss
        
        result = WaveRiderCalculations.calculate_portfolio_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("95.00"),
            shares=100,
            shares_remaining=100,
            portfolio_size=Decimal("200000.00"),
            pct_gain_loss_trade=pct_gain_loss_trade
        )
        
        assert result["gain_loss_pct_portfolio_impact"] is not None
        assert result["gain_loss_pct_portfolio_impact"] < 0

    def test_gain_loss_portfolio_impact_null_when_no_gain_loss(self):
        """Test NULL when pct_gain_loss_trade is None."""
        result = WaveRiderCalculations.calculate_portfolio_metrics(
            purchase_price=Decimal("100.00"),
            current_price=None,  # No current price
            shares=100,
            shares_remaining=100,
            portfolio_size=Decimal("200000.00"),
            pct_gain_loss_trade=None
        )
        
        assert result["gain_loss_pct_portfolio_impact"] is None

    def test_gain_loss_portfolio_impact_null_when_no_portfolio_size(self):
        """Test NULL when portfolio_size is missing."""
        result = WaveRiderCalculations.calculate_portfolio_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            shares=100,
            shares_remaining=100,
            portfolio_size=None,  # No portfolio size
            pct_gain_loss_trade=Decimal("0.10")
        )
        
        assert result["gain_loss_pct_portfolio_impact"] is None


class TestRiskATRRUnits:
    """Test Risk / ATR (R units) calculation."""

    def test_risk_atr_r_units_basic(self):
        """Test basic Risk/ATR calculation."""
        # OneR = 5.00, ATR_Entry = 2.50 => 5.00 / 2.50 = 2.00
        one_r = Decimal("5.00")
        atr_at_entry = Decimal("2.50")
        
        result = WaveRiderCalculations.calculate_atr_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            entry_day_low=Decimal("95.00"),
            atr_at_entry=atr_at_entry,
            atr_14=Decimal("3.00"),
            sma_at_entry=Decimal("98.00"),
            sma_50=Decimal("102.00"),
            one_r=one_r
        )
        
        assert result["risk_atr_r_units"] is not None
        expected = one_r / atr_at_entry
        assert result["risk_atr_r_units"] == expected.quantize(Decimal("0.0001"))

    def test_risk_atr_r_units_high_volatility(self):
        """Test with high ATR (low volatility stock)."""
        # OneR = 3.00, ATR_Entry = 10.00 => 3.00 / 10.00 = 0.30 R units
        one_r = Decimal("3.00")
        atr_at_entry = Decimal("10.00")
        
        result = WaveRiderCalculations.calculate_atr_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            entry_day_low=Decimal("97.00"),
            atr_at_entry=atr_at_entry,
            atr_14=Decimal("12.00"),
            sma_at_entry=Decimal("98.00"),
            sma_50=Decimal("102.00"),
            one_r=one_r
        )
        
        assert result["risk_atr_r_units"] is not None
        assert result["risk_atr_r_units"] < 1  # Less than 1R

    def test_risk_atr_r_units_null_when_no_atr(self):
        """Test NULL when ATR_Entry is missing."""
        result = WaveRiderCalculations.calculate_atr_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            entry_day_low=Decimal("95.00"),
            atr_at_entry=None,  # No ATR at entry
            atr_14=Decimal("3.00"),
            sma_at_entry=Decimal("98.00"),
            sma_50=Decimal("102.00"),
            one_r=Decimal("5.00")
        )
        
        assert result["risk_atr_r_units"] is None

    def test_risk_atr_r_units_null_when_no_one_r(self):
        """Test NULL when OneR is missing."""
        result = WaveRiderCalculations.calculate_atr_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            entry_day_low=Decimal("95.00"),
            atr_at_entry=Decimal("2.50"),
            atr_14=Decimal("3.00"),
            sma_at_entry=Decimal("98.00"),
            sma_50=Decimal("102.00"),
            one_r=None  # No OneR
        )
        
        assert result["risk_atr_r_units"] is None


class TestRMultiple:
    """Test R-Multiple calculation."""

    def test_r_multiple_winning_trade(self):
        """Test R-Multiple for winning trade."""
        # Total PnL = $1000, Shares = 100, OneR = $5 => Initial Risk = $500
        # R-Multiple = $1000 / $500 = 2.00R
        total_pnl = Decimal("1000.00")
        shares = 100
        one_r = Decimal("5.00")
        
        result = WaveRiderCalculations.calculate_r_multiple(total_pnl, shares, one_r)
        
        assert result is not None
        expected = total_pnl / (shares * one_r)
        assert result == expected.quantize(Decimal("0.0001"))
        assert result == Decimal("2.00")

    def test_r_multiple_losing_trade(self):
        """Test R-Multiple for losing trade."""
        # Total PnL = -$300, Shares = 100, OneR = $3 => Initial Risk = $300
        # R-Multiple = -$300 / $300 = -1.00R
        total_pnl = Decimal("-300.00")
        shares = 100
        one_r = Decimal("3.00")
        
        result = WaveRiderCalculations.calculate_r_multiple(total_pnl, shares, one_r)
        
        assert result is not None
        assert result == Decimal("-1.00")

    def test_r_multiple_partial_exit(self):
        """Test R-Multiple with partial exit."""
        # Total PnL = $250, Shares = 100, OneR = $2.50 => Initial Risk = $250
        # R-Multiple = $250 / $250 = 1.00R
        total_pnl = Decimal("250.00")
        shares = 100
        one_r = Decimal("2.50")
        
        result = WaveRiderCalculations.calculate_r_multiple(total_pnl, shares, one_r)
        
        assert result is not None
        assert result == Decimal("1.00")

    def test_r_multiple_null_when_no_one_r(self):
        """Test NULL when OneR is missing."""
        result = WaveRiderCalculations.calculate_r_multiple(
            total_pnl=Decimal("1000.00"),
            shares=100,
            one_r=None
        )
        
        assert result is None

    def test_r_multiple_null_when_one_r_zero(self):
        """Test NULL when OneR is zero."""
        result = WaveRiderCalculations.calculate_r_multiple(
            total_pnl=Decimal("1000.00"),
            shares=100,
            one_r=Decimal("0.00")
        )
        
        assert result is None

    def test_r_multiple_breakeven_trade(self):
        """Test R-Multiple for breakeven trade."""
        # Total PnL = $0, R-Multiple = 0.00R
        result = WaveRiderCalculations.calculate_r_multiple(
            total_pnl=Decimal("0.00"),
            shares=100,
            one_r=Decimal("5.00")
        )
        
        assert result is not None
        assert result == Decimal("0.00")


class TestManualStop3Override:
    """Test that manual Stop3 override is used in risk calculations."""

    def test_manual_stop3_override_used(self):
        """Test that manual override takes precedence over entry_day_low."""
        # Manual override should be used instead of entry_day_low
        manual_override = Decimal("95.00")
        entry_day_low = Decimal("97.00")  # Higher, should be ignored
        
        result = WaveRiderCalculations.calculate_stops_and_targets(
            purchase_price=Decimal("100.00"),
            entry_day_low=entry_day_low,
            stop_override=manual_override,
            buffer_pct=Decimal("0.005")
        )
        
        assert result["stop_3"] == manual_override
        assert result["one_r"] == Decimal("100.00") - manual_override
        
    def test_entry_day_low_with_buffer_when_no_override(self):
        """Test that entry_day_low with buffer is used when no override."""
        entry_day_low = Decimal("97.00")
        buffer_pct = Decimal("0.005")  # 0.5%
        
        result = WaveRiderCalculations.calculate_stops_and_targets(
            purchase_price=Decimal("100.00"),
            entry_day_low=entry_day_low,
            stop_override=None,
            buffer_pct=buffer_pct
        )
        
        expected_stop3 = entry_day_low * (Decimal("1") - buffer_pct)
        assert result["stop_3"] == expected_stop3.quantize(Decimal("0.0001"))


class TestMissingInputsNullHandling:
    """Test NULL handling when required inputs are missing."""

    def test_portfolio_metrics_null_when_no_portfolio_size(self):
        """Test all portfolio metrics return NULL when portfolio_size is missing."""
        result = WaveRiderCalculations.calculate_portfolio_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            shares=100,
            shares_remaining=100,
            portfolio_size=None,
            pct_gain_loss_trade=Decimal("0.10")
        )
        
        assert result["pct_portfolio_invested_at_entry"] is None
        assert result["pct_portfolio_current"] is None
        assert result["gain_loss_pct_portfolio_impact"] is None

    def test_atr_metrics_partial_null(self):
        """Test that only calculable metrics are returned when some inputs missing."""
        result = WaveRiderCalculations.calculate_atr_metrics(
            purchase_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            entry_day_low=None,  # Missing
            atr_at_entry=Decimal("2.50"),
            atr_14=Decimal("3.00"),
            sma_at_entry=Decimal("98.00"),
            sma_50=Decimal("102.00"),
            one_r=Decimal("5.00")
        )
        
        # risk_atr_pct_above_low should be NULL (needs entry_day_low)
        assert result["risk_atr_pct_above_low"] is None
        
        # risk_atr_r_units should be calculated (has one_r and atr_at_entry)
        assert result["risk_atr_r_units"] is not None

    def test_stops_null_when_no_inputs(self):
        """Test stops return NULL when neither entry_day_low nor override provided."""
        result = WaveRiderCalculations.calculate_stops_and_targets(
            purchase_price=Decimal("100.00"),
            entry_day_low=None,
            stop_override=None,
            buffer_pct=Decimal("0.005")
        )
        
        assert result["stop_3"] is None
        assert result["stop_2"] is None
        assert result["stop_1"] is None
        assert result["one_r"] is None
        assert result["tp_1r"] is None
        assert result["tp_2r"] is None
        assert result["tp_3r"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
