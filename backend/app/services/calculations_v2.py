"""
Complete calculation service for WaveRider 3-Stop system.
Implements ALL formulas from Google Sheet Row 6.

CRITICAL: Preserves exact spreadsheet formulas.
DO NOT simplify or reinterpret logic.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple, Dict
from datetime import datetime, date
from sqlalchemy.orm import Session
import pandas as pd

from app.models.trade_v2 import Trade, Transaction


class WaveRiderCalculations:
    """Complete calculation engine for WaveRider 3-Stop system."""

    @staticmethod
    def calculate_stops_and_targets(
        purchase_price: Decimal,
        entry_day_low: Optional[Decimal],
        stop_override: Optional[Decimal]
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate 3-Stop levels and Take Profit targets.

        Returns dictionary with:
        - stop_3, stop_2, stop_1
        - one_r (risk unit)
        - tp_1x, tp_2x, tp_3x
        - entry_pct_above_stop3
        """
        # Determine Stop3
        if stop_override is not None:
            stop_3 = stop_override
        elif entry_day_low is not None:
            stop_3 = entry_day_low
        else:
            # Cannot calculate without either value
            return {
                "stop_3": None,
                "stop_2": None,
                "stop_1": None,
                "one_r": None,
                "tp_1x": None,
                "tp_2x": None,
                "tp_3x": None,
                "entry_pct_above_stop3": None,
            }

        # Validate Stop3 is below entry
        if stop_3 >= purchase_price:
            raise ValueError(f"Stop3 ({stop_3}) must be below purchase price ({purchase_price})")

        # Calculate distance (1R risk unit)
        distance = purchase_price - stop_3
        one_r = distance

        # Calculate Stop2 (2/3 of the way from PP to Stop3)
        stop_2 = purchase_price - (Decimal("2") / Decimal("3") * distance)

        # Calculate Stop1 (1/3 of the way from PP to Stop3)
        stop_1 = purchase_price - (Decimal("1") / Decimal("3") * distance)

        # Calculate Take Profit levels (1R, 2R, 3R above entry)
        tp_1x = purchase_price + one_r
        tp_2x = purchase_price + (Decimal("2") * one_r)
        tp_3x = purchase_price + (Decimal("3") * one_r)

        # Entry % above Stop3
        entry_pct_above_stop3 = (distance / stop_3) * 100

        # Round all values to 4 decimal places
        return {
            "stop_3": stop_3.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "stop_2": stop_2.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "stop_1": stop_1.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "one_r": one_r.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "tp_1x": tp_1x.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "tp_2x": tp_2x.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "tp_3x": tp_3x.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "entry_pct_above_stop3": entry_pct_above_stop3.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        }

    @staticmethod
    def calculate_price_metrics(
        current_price: Optional[Decimal],
        purchase_price: Decimal,
        entry_day_low: Optional[Decimal]
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate price-based metrics.

        Returns:
        - day_pct_moved: (CP - LoD) / LoD * 100
        - gain_loss_pct_vs_pp: (CP - PP) / PP * 100
        """
        if not current_price:
            return {
                "day_pct_moved": None,
                "gain_loss_pct_vs_pp": None,
            }

        # Day % Moved (from entry day low to current)
        day_pct_moved = None
        if entry_day_low and entry_day_low > 0:
            day_pct_moved = ((current_price - entry_day_low) / entry_day_low) * 100
            day_pct_moved = day_pct_moved.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # % Gain/Loss vs Purchase Price
        gain_loss_pct_vs_pp = ((current_price - purchase_price) / purchase_price) * 100
        gain_loss_pct_vs_pp = gain_loss_pct_vs_pp.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        return {
            "day_pct_moved": day_pct_moved,
            "gain_loss_pct_vs_pp": gain_loss_pct_vs_pp,
        }

    @staticmethod
    def calculate_portfolio_metrics(
        purchase_price: Decimal,
        current_price: Optional[Decimal],
        shares: int,
        shares_remaining: int,
        portfolio_size: Optional[Decimal]
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate portfolio allocation percentages.

        Returns:
        - pct_portfolio_invested_at_entry
        - pct_portfolio_current
        """
        if not portfolio_size or portfolio_size <= 0:
            return {
                "pct_portfolio_invested_at_entry": None,
                "pct_portfolio_current": None,
            }

        # % of Portfolio Invested at Entry
        initial_position_value = shares * purchase_price
        pct_portfolio_invested_at_entry = (initial_position_value / portfolio_size) * 100
        pct_portfolio_invested_at_entry = pct_portfolio_invested_at_entry.quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        # % of Portfolio Current $
        pct_portfolio_current = None
        if current_price and shares_remaining > 0:
            current_position_value = shares_remaining * current_price
            pct_portfolio_current = (current_position_value / portfolio_size) * 100
            pct_portfolio_current = pct_portfolio_current.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        return {
            "pct_portfolio_invested_at_entry": pct_portfolio_invested_at_entry,
            "pct_portfolio_current": pct_portfolio_current,
        }

    @staticmethod
    def calculate_atr_metrics(
        purchase_price: Decimal,
        current_price: Optional[Decimal],
        entry_day_low: Optional[Decimal],
        atr_at_entry: Optional[Decimal],
        sma_at_entry: Optional[Decimal],
        sma_50: Optional[Decimal]
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate ATR and SMA-based metrics.

        Returns:
        - risk_atr_pct_above_low
        - multiple_from_sma_at_entry
        - atr_multiple_from_sma_current
        """
        # Risk/ATR (% above Low Exit)
        # Formula: (PP - LoD) / ATR_at_entry * 100
        risk_atr_pct_above_low = None
        if atr_at_entry and atr_at_entry > 0 and entry_day_low:
            risk_atr_pct_above_low = ((purchase_price - entry_day_low) / atr_at_entry) * 100
            risk_atr_pct_above_low = risk_atr_pct_above_low.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        # Multiple from SMA at Entry
        # Formula: PP / SMA_at_entry
        multiple_from_sma_at_entry = None
        if sma_at_entry and sma_at_entry > 0:
            multiple_from_sma_at_entry = purchase_price / sma_at_entry
            multiple_from_sma_at_entry = multiple_from_sma_at_entry.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        # ATR/% Multiple from SMA Current
        # Formula: CP / SMA_current
        atr_multiple_from_sma_current = None
        if current_price and sma_50 and sma_50 > 0:
            atr_multiple_from_sma_current = current_price / sma_50
            atr_multiple_from_sma_current = atr_multiple_from_sma_current.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        return {
            "risk_atr_pct_above_low": risk_atr_pct_above_low,
            "multiple_from_sma_at_entry": multiple_from_sma_at_entry,
            "atr_multiple_from_sma_current": atr_multiple_from_sma_current,
        }

    @staticmethod
    def calculate_trading_days(purchase_date: date, as_of_date: Optional[date] = None) -> int:
        """
        Calculate number of trading days between purchase and current/as_of date.
        Uses business day calculation (excludes weekends).

        NOTE: Does not account for market holidays. For perfect accuracy,
        use Polygon.io market calendar API.
        """
        if as_of_date is None:
            as_of_date = datetime.now().date()

        # Use pandas business day range
        trading_days = pd.bdate_range(start=purchase_date, end=as_of_date)
        return len(trading_days) - 1  # Exclude the purchase date itself

    @staticmethod
    def calculate_transaction_proceeds(
        shares: int,
        price: Decimal,
        fees: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Calculate proceeds from a transaction.
        Formula: (shares * price) - fees
        """
        proceeds = (shares * price) - fees
        return proceeds.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_trade_rollups(trade: Trade, db: Session) -> Dict:
        """
        Calculate ALL rollup values from transactions.

        Computes:
        - shares_exited, shares_remaining
        - total_proceeds, total_fees
        - avg_exit_price
        - realized_pnl, unrealized_pnl, total_pnl
        - status
        """
        # Fetch all transactions
        transactions = db.query(Transaction).filter(
            Transaction.trade_id == trade.trade_id
        ).all()

        # Initialize
        shares_exited = 0
        total_exit_value = Decimal("0")  # Sum of (shares * price)
        total_proceeds = Decimal("0")
        total_fees = Decimal("0")

        # Aggregate transactions
        for txn in transactions:
            shares_exited += txn.shares
            total_exit_value += (txn.shares * txn.price)
            if txn.proceeds:
                total_proceeds += txn.proceeds
            if txn.fees:
                total_fees += txn.fees

        # Shares remaining
        shares_remaining = trade.shares - shares_exited

        # Validate
        if shares_remaining < 0:
            raise ValueError(
                f"Over-exit detected: Entry shares={trade.shares}, Exited={shares_exited}"
            )

        # Weighted average exit price
        avg_exit_price = None
        if shares_exited > 0:
            avg_exit_price = total_exit_value / shares_exited
            avg_exit_price = avg_exit_price.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Realized PnL
        # Formula: total_proceeds - (shares_exited * purchase_price)
        cost_basis_exited = shares_exited * trade.purchase_price
        realized_pnl = total_proceeds - cost_basis_exited
        realized_pnl = realized_pnl.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Unrealized PnL
        # Formula: shares_remaining * (current_price - purchase_price)
        unrealized_pnl = Decimal("0")
        if shares_remaining > 0 and trade.current_price:
            unrealized_pnl = shares_remaining * (trade.current_price - trade.purchase_price)
            unrealized_pnl = unrealized_pnl.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Total PnL
        total_pnl = realized_pnl + unrealized_pnl

        # Status
        if shares_remaining == trade.shares:
            status = "OPEN"
        elif shares_remaining == 0:
            status = "CLOSED"
        else:
            status = "PARTIAL"

        return {
            "shares_exited": shares_exited,
            "shares_remaining": shares_remaining,
            "total_proceeds": total_proceeds,
            "total_fees": total_fees,
            "avg_exit_price": avg_exit_price,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "status": status,
        }

    @staticmethod
    def update_all_calculations(trade: Trade, db: Session) -> None:
        """
        Update ALL calculated fields on a trade.

        Call this after:
        - Trade creation
        - Market data refresh
        - Transaction insert/update/delete

        Modifies trade in-place (caller must commit).
        """
        # 1. Calculate stops and targets
        stops_and_targets = WaveRiderCalculations.calculate_stops_and_targets(
            trade.purchase_price,
            trade.entry_day_low,
            trade.stop_override
        )
        trade.stop_3 = stops_and_targets["stop_3"]
        trade.stop_2 = stops_and_targets["stop_2"]
        trade.stop_1 = stops_and_targets["stop_1"]
        trade.one_r = stops_and_targets["one_r"]
        trade.tp_1x = stops_and_targets["tp_1x"]
        trade.tp_2x = stops_and_targets["tp_2x"]
        trade.tp_3x = stops_and_targets["tp_3x"]
        trade.entry_pct_above_stop3 = stops_and_targets["entry_pct_above_stop3"]

        # 2. Calculate price metrics
        price_metrics = WaveRiderCalculations.calculate_price_metrics(
            trade.current_price,
            trade.purchase_price,
            trade.entry_day_low
        )
        trade.day_pct_moved = price_metrics["day_pct_moved"]
        trade.gain_loss_pct_vs_pp = price_metrics["gain_loss_pct_vs_pp"]

        # 3. Calculate transaction rollups FIRST (needed for shares_remaining)
        rollups = WaveRiderCalculations.calculate_trade_rollups(trade, db)
        trade.shares_exited = rollups["shares_exited"]
        trade.shares_remaining = rollups["shares_remaining"]
        trade.total_proceeds = rollups["total_proceeds"]
        trade.total_fees = rollups["total_fees"]
        trade.avg_exit_price = rollups["avg_exit_price"]
        trade.realized_pnl = rollups["realized_pnl"]
        trade.unrealized_pnl = rollups["unrealized_pnl"]
        trade.total_pnl = rollups["total_pnl"]
        trade.status = rollups["status"]

        # 4. Calculate portfolio metrics (needs shares_remaining)
        portfolio_metrics = WaveRiderCalculations.calculate_portfolio_metrics(
            trade.purchase_price,
            trade.current_price,
            trade.shares,
            trade.shares_remaining,
            trade.portfolio_size
        )
        trade.pct_portfolio_invested_at_entry = portfolio_metrics["pct_portfolio_invested_at_entry"]
        trade.pct_portfolio_current = portfolio_metrics["pct_portfolio_current"]

        # 5. Calculate ATR/SMA metrics
        atr_metrics = WaveRiderCalculations.calculate_atr_metrics(
            trade.purchase_price,
            trade.current_price,
            trade.entry_day_low,
            trade.atr_at_entry,
            trade.sma_at_entry,
            trade.sma_50
        )
        trade.risk_atr_pct_above_low = atr_metrics["risk_atr_pct_above_low"]
        trade.multiple_from_sma_at_entry = atr_metrics["multiple_from_sma_at_entry"]
        trade.atr_multiple_from_sma_current = atr_metrics["atr_multiple_from_sma_current"]

        # 6. Calculate trading days open
        trade.trading_days_open = WaveRiderCalculations.calculate_trading_days(
            trade.purchase_date
        )


# Global instance
waverider_calc = WaveRiderCalculations()
