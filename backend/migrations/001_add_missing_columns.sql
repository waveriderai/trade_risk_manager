-- Migration: Add missing columns for WaveRider 3-Stop Trading Journal
-- Date: 2025-01-XX
-- Description: Adds gain_loss_pct_portfolio_impact, r_multiple columns
--              Renames risk_atr_pct_above_low to risk_atr_r_units

-- Add gain_loss_pct_portfolio_impact column (if not exists)
ALTER TABLE trades ADD COLUMN IF NOT EXISTS gain_loss_pct_portfolio_impact NUMERIC(10, 4);

-- Add r_multiple column (if not exists)
ALTER TABLE trades ADD COLUMN IF NOT EXISTS r_multiple NUMERIC(10, 4);

-- Rename risk_atr_pct_above_low to risk_atr_r_units (if column exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trades' AND column_name = 'risk_atr_pct_above_low'
    ) THEN
        ALTER TABLE trades RENAME COLUMN risk_atr_pct_above_low TO risk_atr_r_units;
    ELSIF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trades' AND column_name = 'risk_atr_r_units'
    ) THEN
        ALTER TABLE trades ADD COLUMN risk_atr_r_units NUMERIC(10, 4);
    END IF;
END $$;

-- Add comment on new columns
COMMENT ON COLUMN trades.gain_loss_pct_portfolio_impact IS 'Gain/Loss % Portfolio Impact = GainLossPctTrade * PortfolioInvestedAtEntry';
COMMENT ON COLUMN trades.r_multiple IS 'R-Multiple = Total PnL / (OneR * Shares)';
COMMENT ON COLUMN trades.risk_atr_r_units IS 'Risk / ATR (R units) = OneR / ATR_Entry';
