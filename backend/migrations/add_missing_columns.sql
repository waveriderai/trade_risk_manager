-- Migration: Add missing WaveRider 3-Stop columns
-- Date: 2025-01-30
-- Description: Adds Gain/Loss % Portfolio Impact, Risk/ATR (R units), and R-Multiple fields

-- Add new calculated fields to trades table
ALTER TABLE trades
  ADD COLUMN IF NOT EXISTS gain_loss_pct_portfolio_impact NUMERIC(10, 4),
  ADD COLUMN IF NOT EXISTS risk_atr_r_units NUMERIC(10, 4),
  ADD COLUMN IF NOT EXISTS r_multiple NUMERIC(10, 4);

-- Add comments for documentation
COMMENT ON COLUMN trades.gain_loss_pct_portfolio_impact IS 'Gain/Loss % Portfolio Impact = GainLossPctTrade * PortfolioInvestedAtEntry';
COMMENT ON COLUMN trades.risk_atr_r_units IS 'Risk / ATR (R units) = OneR / ATR_Entry';
COMMENT ON COLUMN trades.r_multiple IS 'R-Multiple = Total PnL / (Initial Risk)';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_trades_r_multiple ON trades(r_multiple);
CREATE INDEX IF NOT EXISTS idx_trades_gain_loss_portfolio ON trades(gain_loss_pct_portfolio_impact);
