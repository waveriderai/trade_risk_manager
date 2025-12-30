/**
 * TypeScript type definitions for WaveRider Trading Journal.
 * Matches backend Pydantic schemas.
 */

export interface Trade {
  // Identity
  trade_id: string;
  ticker: string;

  // Entry Details
  entry_date: string;
  entry_price: number;
  entry_shares: number;

  // User Inputs
  low_of_day?: number;
  stop3_override?: number;
  portfolio_size?: number;

  // Market Data
  current_price?: number;
  atr_14?: number;
  sma_50?: number;
  sma_10?: number;
  market_data_updated_at?: string;

  // Calculated Stops
  stop_3?: number;
  stop_2?: number;
  stop_1?: number;
  one_r_distance?: number;

  // Trade Status
  status?: string;
  shares_remaining?: number;

  // Rollup Calculations
  total_shares_exited: number;
  weighted_avg_exit_price?: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  percent_gain_loss?: number;
  r_multiple?: number;

  // Audit
  created_at: string;
  updated_at: string;
}

export interface TradeCreate {
  trade_id: string;
  ticker: string;
  entry_date: string;
  entry_price: number;
  entry_shares: number;
  low_of_day?: number;
  stop3_override?: number;
  portfolio_size?: number;
}

export interface TradeUpdate {
  low_of_day?: number;
  stop3_override?: number;
  portfolio_size?: number;
}

export interface Transaction {
  id: number;
  trade_id: string;
  transaction_date: string;
  action: string;
  shares: number;
  price: number;
  fees: number;
  notes?: string;
  proceeds?: number;
  pnl?: number;
  created_at: string;
  updated_at: string;
}

export interface TransactionCreate {
  trade_id: string;
  transaction_date: string;
  action: string;
  shares: number;
  price: number;
  fees?: number;
  notes?: string;
}

export interface TradeSummary {
  total_trades: number;
  open_trades: number;
  partial_trades: number;
  closed_trades: number;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  total_pnl: number;
  average_r_multiple?: number;
}

export type ActionType = 'Stop1' | 'Stop2' | 'Stop3' | 'Profit' | 'Other';
export type TradeStatus = 'OPEN' | 'PARTIAL' | 'CLOSED';
