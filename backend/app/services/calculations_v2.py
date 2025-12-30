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
        stop_override: Optional[Decimal],
        buffer_pct: Decimal = Decimal("0.005")  # Default 0.5%
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate 3-Stop levels and Take Profit targets.

        Formula for Stop3: IF(manual_override, manual_override, LoD*(1-Buffer))
        OneR: PP - Stop3
        TP @ 1R: PP + 1*OneR
        TP @ 2R: PP + 2*OneR
        TP @ 3R: PP + 3*OneR

        Returns dictionary with:
        - stop_3, stop_2, stop_1
        - one_r (risk unit)
        - tp_1r, tp_2r, tp_3r
        - entry_pct_above_stop3
        """
        # Determine Stop3
        if stop_override is not None:
            stop_3 = stop_override
        elif entry_day_low is not None:
            # Apply buffer: LoD * (1 - Buffer%)
            stop_3 = entry_day_low * (Decimal("1") - buffer_pct)
        else:
            # Cannot calculate without either value
            return {
                "stop_3": None,
                "stop_2": None,
                "stop_1": None,
                "one_r": None,
                "tp_1r": None,
                "tp_2r": None,
                "tp_3r": None,
                "entry_pct_above_stop3": None,
            }

        # Validate Stop3 is below entry
        if stop_3 >= purchase_price:
            raise ValueError(f"Stop3 ({stop_3}) must be below purchase price ({purchase_price})")

        # Calculate distance (1R risk unit): PP - Stop3
        one_r = purchase_price - stop_3

        # Calculate Stop2 (2/3 of the way from PP to Stop3)
        stop_2 = purchase_price - (Decimal("2") / Decimal("3") * one_r)

        # Calculate Stop1 (1/3 of the way from PP to Stop3)
        stop_1 = purchase_price - (Decimal("1") / Decimal("3") * one_r)

        # Calculate Take Profit levels (1R, 2R, 3R above entry)
        tp_1r = purchase_price + one_r
        tp_2r = purchase_price + (Decimal("2") * one_r)
        tp_3r = purchase_price + (Decimal("3") * one_r)

        # Entry % above Stop3
        entry_pct_above_stop3 = (one_r / stop_3) * 100

        # Round all values to 4 decimal places
        return {
            "stop_3": stop_3.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "stop_2": stop_2.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "stop_1": stop_1.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "one_r": one_r.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "tp_1r": tp_1r.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "tp_2r": tp_2r.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "tp_3r": tp_3r.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "entry_pct_above_stop3": entry_pct_above_stop3.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        }

    @staticmethod
    def calculate_price_metrics(
        current_price: Optional[Decimal],
        purchase_price: Decimal,
        entry_day_low: Optional[Decimal],
        sold_price: Optional[Decimal],
        status: Optional[str]
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate price-based metrics.

        Returns:
        - day_pct_moved: (CP - LoD) / LoD * 100
        - cp_pct_diff_from_entry: (CP - PP) / PP
        - pct_gain_loss_trade: (SP - PP) / PP
        - sold_price: IF(Status="CLOSED", AvgExitPrice, CP)
        """
        result = {
            "day_pct_moved": None,
            "cp_pct_diff_from_entry": None,
            "pct_gain_loss_trade": None,
            "sold_price": sold_price,  # Will be calculated below
        }

        if not current_price:
            return result

        # Day % Moved (from entry day low to current)
        if entry_day_low and entry_day_low > 0:
            result["day_pct_moved"] = ((current_price - entry_day_low) / entry_day_low) * 100
            result["day_pct_moved"] = result["day_pct_moved"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # CP % Diff From Entry (PP)
        result["cp_pct_diff_from_entry"] = (current_price - purchase_price) / purchase_price
        result["cp_pct_diff_from_entry"] = result["cp_pct_diff_from_entry"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Sold Price: IF(Status="CLOSED", AvgExitPrice, CP)
        if status == "CLOSED" and sold_price:
            result["sold_price"] = sold_price
        else:
            result["sold_price"] = current_price

        # % Gain/Loss on Trade: (SP - PP) / PP
        if result["sold_price"]:
            result["pct_gain_loss_trade"] = (result["sold_price"] - purchase_price) / purchase_price
            result["pct_gain_loss_trade"] = result["pct_gain_loss_trade"].quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        return result

    @staticmethod
    def calculate_portfolio_metrics(
        purchase_price: Decimal,
        current_price: Optional[Decimal],
        shares: int,
        shares_remaining: int,
        portfolio_size: Optional[Decimal],
        pct_gain_loss_trade: Optional[Decimal]
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate portfolio allocation percentages.

        Returns:
        - pct_portfolio_invested_at_entry
        - pct_portfolio_current
        - gain_loss_pct_portfolio_impact
        """
        if not portfolio_size or portfolio_size <= 0:
            return {
                "pct_portfolio_invested_at_entry": None,
                "pct_portfolio_current": None,
                "gain_loss_pct_portfolio_impact": None,
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

        # Gain/Loss % Portfolio Impact
        # Formula: GainLossPctTrade * PortfolioInvestedAtEntry
        gain_loss_pct_portfolio_impact = None
        if pct_gain_loss_trade is not None and pct_portfolio_invested_at_entry is not None:
            # Convert % gain/loss from decimal to actual percentage for calculation
            gain_loss_pct_portfolio_impact = pct_gain_loss_trade * pct_portfolio_invested_at_entry
            gain_loss_pct_portfolio_impact = gain_loss_pct_portfolio_impact.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        return {
            "pct_portfolio_invested_at_entry": pct_portfolio_invested_at_entry,
            "pct_portfolio_current": pct_portfolio_current,
            "gain_loss_pct_portfolio_impact": gain_loss_pct_portfolio_impact,
        }

    @staticmethod
    def calculate_atr_metrics(
        purchase_price: Decimal,
        current_price: Optional[Decimal],
        one_r: Optional[Decimal],
        atr_at_entry: Optional[Decimal],
        atr_14: Optional[Decimal],
        sma_at_entry: Optional[Decimal],
        sma_50: Optional[Decimal],
        one_r: Optional[Decimal]
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate ATR and SMA-based metrics.

        Returns:
        - risk_atr_pct_above_low: (PP - LoD) / ATR_at_entry * 100
        - risk_atr_r_units: OneR / ATR_Entry
        - atr_pct_multiple_from_ma_at_entry: ((PP-SMAEntry)/SMAEntry) / (AtrEntry/PP)
        - atr_pct_multiple_from_ma: ((CP-SMA)/SMA) / (ATR/CP)
        """
        # Risk / ATR (R units)
        # Formula: OneR / ATR_Entry
        risk_atr_r_units = None
        if one_r and atr_at_entry and atr_at_entry > 0:
            risk_atr_r_units = one_r / atr_at_entry
            risk_atr_r_units = risk_atr_r_units.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        # Risk / ATR (R units)
        # Formula: OneR / ATR_Entry
        risk_atr_r_units = None
        if one_r is not None and atr_at_entry and atr_at_entry > 0:
            risk_atr_r_units = one_r / atr_at_entry
            risk_atr_r_units = risk_atr_r_units.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        # ATR% Multiple from MA @ Entry
        # Formula: ((PP-SMAEntry)/SMAEntry) / (AtrEntry/PP)
        atr_pct_multiple_from_ma_at_entry = None
        if sma_at_entry and sma_at_entry > 0 and atr_at_entry and atr_at_entry > 0:
            pct_from_sma = (purchase_price - sma_at_entry) / sma_at_entry
            atr_as_pct_of_pp = atr_at_entry / purchase_price
            if atr_as_pct_of_pp != 0:
                atr_pct_multiple_from_ma_at_entry = pct_from_sma / atr_as_pct_of_pp
                atr_pct_multiple_from_ma_at_entry = atr_pct_multiple_from_ma_at_entry.quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )

        # ATR% Multiple from MA
        # Formula: ((CP-SMA)/SMA) / (ATR/CP)
        atr_pct_multiple_from_ma = None
        if current_price and sma_50 and sma_50 > 0 and atr_14 and atr_14 > 0:
            pct_from_sma_current = (current_price - sma_50) / sma_50
            atr_as_pct_of_cp = atr_14 / current_price
            if atr_as_pct_of_cp != 0:
                atr_pct_multiple_from_ma = pct_from_sma_current / atr_as_pct_of_cp
                atr_pct_multiple_from_ma = atr_pct_multiple_from_ma.quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )

        return {
            "risk_atr_pct_above_low": risk_atr_pct_above_low,
            "risk_atr_r_units": risk_atr_r_units,
            "atr_pct_multiple_from_ma_at_entry": atr_pct_multiple_from_ma_at_entry,
            "atr_pct_multiple_from_ma": atr_pct_multiple_from_ma,
        }

    @staticmethod
    def calculate_r_multiple(
        total_pnl: Decimal,
        shares: int,
        one_r: Optional[Decimal]
    ) -> Optional[Decimal]:
        """
        Calculate R-Multiple (risk-reward ratio).

        Formula: Total PnL / (Initial Risk)
        where Initial Risk = Shares * OneR

        Returns:
            R-Multiple value or None if cannot be calculated
        """
        if one_r is None or one_r <= 0:
            return None

        initial_risk = shares * one_r

        if initial_risk == 0:
            return None

        r_multiple = total_pnl / initial_risk
        return r_multiple.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

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
    def update_all_calculations(trade: Trade, db: Session, buffer_pct: Decimal = Decimal("0.005")) -> None:
        """
        Update ALL calculated fields on a trade.

        Call this after:
        - Trade creation
        - Market data refresh
        - Transaction insert/update/delete

        Modifies trade in-place (caller must commit).
        """
        # 1. Calculate transaction rollups FIRST (needed for status, avg_exit_price)
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

        # 2. Calculate stops and targets
        stops_and_targets = WaveRiderCalculations.calculate_stops_and_targets(
            trade.purchase_price,
            trade.entry_day_low,
            trade.stop_override,
            buffer_pct
        )
        trade.stop_3 = stops_and_targets["stop_3"]
        trade.stop_2 = stops_and_targets["stop_2"]
        trade.stop_1 = stops_and_targets["stop_1"]
        trade.one_r = stops_and_targets["one_r"]
        trade.tp_1r = stops_and_targets["tp_1r"]
        trade.tp_2r = stops_and_targets["tp_2r"]
        trade.tp_3r = stops_and_targets["tp_3r"]
        trade.entry_pct_above_stop3 = stops_and_targets["entry_pct_above_stop3"]

        # 3. Calculate price metrics (needs status and avg_exit_price for sold_price)
        price_metrics = WaveRiderCalculations.calculate_price_metrics(
            trade.current_price,
            trade.purchase_price,
            trade.entry_day_low,
            trade.avg_exit_price,  # sold_price input
            trade.status
        )
        trade.day_pct_moved = price_metrics["day_pct_moved"]
        trade.cp_pct_diff_from_entry = price_metrics["cp_pct_diff_from_entry"]
        trade.pct_gain_loss_trade = price_metrics["pct_gain_loss_trade"]
        trade.sold_price = price_metrics["sold_price"]

        # 4. Calculate portfolio metrics (needs shares_remaining and pct_gain_loss_trade)
        portfolio_metrics = WaveRiderCalculations.calculate_portfolio_metrics(
            trade.purchase_price,
            trade.current_price,
            trade.shares,
            trade.shares_remaining,
            trade.portfolio_size,
            trade.pct_gain_loss_trade
        )
        trade.pct_portfolio_invested_at_entry = portfolio_metrics["pct_portfolio_invested_at_entry"]
        trade.pct_portfolio_current = portfolio_metrics["pct_portfolio_current"]
        trade.gain_loss_pct_portfolio_impact = portfolio_metrics["gain_loss_pct_portfolio_impact"]

        # 5. Calculate ATR/SMA metrics (needs one_r)
        atr_metrics = WaveRiderCalculations.calculate_atr_metrics(
            trade.purchase_price,
            trade.current_price,
            trade.one_r,  # Now uses one_r instead of entry_day_low
            trade.atr_at_entry,
            trade.atr_14,
            trade.sma_at_entry,
            trade.sma_50,
            trade.one_r
        )
        trade.risk_atr_pct_above_low = atr_metrics["risk_atr_pct_above_low"]
        trade.risk_atr_r_units = atr_metrics["risk_atr_r_units"]
        trade.atr_pct_multiple_from_ma_at_entry = atr_metrics["atr_pct_multiple_from_ma_at_entry"]
        trade.atr_pct_multiple_from_ma = atr_metrics["atr_pct_multiple_from_ma"]

        # 6. Calculate R-Multiple
        trade.r_multiple = WaveRiderCalculations.calculate_r_multiple(
            trade.total_pnl,
            trade.shares,
            trade.one_r
        )

        # 7. Calculate trading days open
        trade.trading_days_open = WaveRiderCalculations.calculate_trading_days(
            trade.purchase_date
        )

        # 7. Calculate R-Multiple
        trade.r_multiple = WaveRiderCalculations.calculate_r_multiple(
            trade.total_pnl,
            trade.one_r,
            trade.shares
        )


# Global instance
waverider_calc = WaveRiderCalculations()
