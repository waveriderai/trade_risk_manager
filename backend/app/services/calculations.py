"""
Trade calculation service.
Implements stop levels, R-multiples, and rollup calculations.

CRITICAL: Preserves exact spreadsheet formulas.
DO NOT simplify or reinterpret logic.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.trade import Trade, Transaction


class CalculationService:
    """Service for trade calculations."""

    @staticmethod
    def calculate_stops(
        entry_price: Decimal,
        low_of_day: Optional[Decimal],
        stop3_override: Optional[Decimal]
    ) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
        """
        Calculate Stop levels and 1R distance.

        Formula (from spreadsheet):
        - Stop3 = stop3_override OR low_of_day
        - Stop2 = entry_price - (2/3 * (entry_price - Stop3))
        - Stop1 = entry_price - (1/3 * (entry_price - Stop3))
        - 1R = entry_price - Stop3

        Returns:
            (stop_3, stop_2, stop_1, one_r_distance)

        Raises:
            ValueError if Stop3 cannot be determined
        """
        # Determine Stop3
        if stop3_override is not None:
            stop_3 = stop3_override
        elif low_of_day is not None:
            stop_3 = low_of_day
        else:
            raise ValueError("Either low_of_day or stop3_override must be provided")

        # Validate Stop3 is below entry
        if stop_3 >= entry_price:
            raise ValueError(f"Stop3 ({stop_3}) must be below entry price ({entry_price})")

        # Calculate distance from entry to Stop3
        distance = entry_price - stop_3

        # Calculate Stop2 (2/3 of the way from entry to Stop3)
        # Entry - (2/3 * distance)
        stop_2 = entry_price - (Decimal("2") / Decimal("3") * distance)

        # Calculate Stop1 (1/3 of the way from entry to Stop3)
        # Entry - (1/3 * distance)
        stop_1 = entry_price - (Decimal("1") / Decimal("3") * distance)

        # 1R is the full distance
        one_r_distance = distance

        # Round to 4 decimal places
        stop_3 = stop_3.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        stop_2 = stop_2.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        stop_1 = stop_1.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        one_r_distance = one_r_distance.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        return stop_3, stop_2, stop_1, one_r_distance

    @staticmethod
    def calculate_transaction_pnl(
        shares: int,
        exit_price: Decimal,
        entry_price: Decimal,
        fees: Decimal = Decimal("0")
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate proceeds and PnL for a transaction.

        Formula:
        - Proceeds = (shares * exit_price) - fees
        - PnL = proceeds - (shares * entry_price)

        Returns:
            (proceeds, pnl)
        """
        proceeds = (shares * exit_price) - fees
        pnl = proceeds - (shares * entry_price)

        # Round to 2 decimal places
        proceeds = proceeds.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        pnl = pnl.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return proceeds, pnl

    @staticmethod
    def calculate_trade_rollups(trade: Trade, db: Session) -> dict:
        """
        Calculate rollup values from transactions.

        Computes:
        - total_shares_exited
        - shares_remaining
        - weighted_avg_exit_price
        - realized_pnl
        - unrealized_pnl
        - total_pnl
        - percent_gain_loss
        - r_multiple
        - status

        Args:
            trade: Trade model instance
            db: Database session

        Returns:
            Dictionary of calculated values
        """
        # Fetch all transactions for this trade
        transactions = db.query(Transaction).filter(
            Transaction.trade_id == trade.trade_id
        ).all()

        # Initialize
        total_shares_exited = 0
        total_exit_value = Decimal("0")  # Sum of (shares * price) for weighted avg
        realized_pnl = Decimal("0")

        # Aggregate transactions
        for txn in transactions:
            total_shares_exited += txn.shares
            total_exit_value += (txn.shares * txn.price)
            if txn.pnl:
                realized_pnl += txn.pnl

        # Calculate shares remaining
        shares_remaining = trade.entry_shares - total_shares_exited

        # Validate (prevent over-exit)
        if shares_remaining < 0:
            raise ValueError(
                f"Transaction validation failed: Cannot exit more shares than owned. "
                f"Entry shares: {trade.entry_shares}, Total exited: {total_shares_exited}"
            )

        # Calculate weighted average exit price
        weighted_avg_exit_price = None
        if total_shares_exited > 0:
            weighted_avg_exit_price = total_exit_value / total_shares_exited
            weighted_avg_exit_price = weighted_avg_exit_price.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        # Calculate unrealized PnL
        unrealized_pnl = Decimal("0")
        if shares_remaining > 0 and trade.current_price:
            unrealized_pnl = shares_remaining * (trade.current_price - trade.entry_price)
            unrealized_pnl = unrealized_pnl.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Total PnL
        total_pnl = realized_pnl + unrealized_pnl

        # Percent gain/loss (based on total PnL vs. initial investment)
        percent_gain_loss = None
        initial_investment = trade.entry_shares * trade.entry_price
        if initial_investment > 0:
            percent_gain_loss = (total_pnl / initial_investment) * 100
            percent_gain_loss = percent_gain_loss.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # R-multiple
        # R-multiple = total_pnl / (entry_shares * 1R)
        r_multiple = None
        if trade.one_r_distance and trade.one_r_distance > 0:
            risk_amount = trade.entry_shares * trade.one_r_distance
            if risk_amount > 0:
                r_multiple = total_pnl / risk_amount
                r_multiple = r_multiple.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Determine status
        if shares_remaining == trade.entry_shares:
            status = "OPEN"
        elif shares_remaining == 0:
            status = "CLOSED"
        else:
            status = "PARTIAL"

        return {
            "total_shares_exited": total_shares_exited,
            "shares_remaining": shares_remaining,
            "weighted_avg_exit_price": weighted_avg_exit_price,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "percent_gain_loss": percent_gain_loss,
            "r_multiple": r_multiple,
            "status": status,
        }

    @staticmethod
    def update_trade_calculations(trade: Trade, db: Session) -> None:
        """
        Update all calculated fields on a trade.
        Call this after:
        - Trade creation
        - Market data refresh
        - Transaction insert/update/delete

        Modifies trade in-place (caller must commit).
        """
        # Calculate stops (if possible)
        if trade.entry_price:
            try:
                stop_3, stop_2, stop_1, one_r = CalculationService.calculate_stops(
                    trade.entry_price,
                    trade.low_of_day,
                    trade.stop3_override
                )
                trade.stop_3 = stop_3
                trade.stop_2 = stop_2
                trade.stop_1 = stop_1
                trade.one_r_distance = one_r
            except ValueError as e:
                # Cannot calculate stops yet (missing low_of_day and override)
                print(f"Cannot calculate stops for {trade.trade_id}: {e}")

        # Calculate rollups
        rollups = CalculationService.calculate_trade_rollups(trade, db)

        trade.total_shares_exited = rollups["total_shares_exited"]
        trade.shares_remaining = rollups["shares_remaining"]
        trade.weighted_avg_exit_price = rollups["weighted_avg_exit_price"]
        trade.realized_pnl = rollups["realized_pnl"]
        trade.unrealized_pnl = rollups["unrealized_pnl"]
        trade.total_pnl = rollups["total_pnl"]
        trade.percent_gain_loss = rollups["percent_gain_loss"]
        trade.r_multiple = rollups["r_multiple"]
        trade.status = rollups["status"]


# Global instance
calculation_service = CalculationService()
