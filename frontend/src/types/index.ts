/**
 * TypeScript type definitions for WaveRider 3-Stop Trading Journal - V2 (Complete).
 * Matches backend Pydantic schemas with ALL 36 columns.
 */

export interface Trade {
  // ===== IDENTITY =====
  trade_id: string;
  ticker: string;

  // ===== USER INPUT FIELDS =====
  purchase_price: number;  // PP
  purchase_date: string;
  shares: number;
  entry_day_low?: number;
  stop_override?: number;
  portfolio_size?: number;

  // ===== MARKET DATA (Current) =====
  current_price?: number;  // CP
  atr_14?: number;
  sma_50?: number;
  sma_10?: number;
  market_data_updated_at?: string;

  // ===== ENTRY SNAPSHOT =====
  atr_at_entry?: number;
  sma_at_entry?: number;

  // ===== CALCULATED: Price & Day Movement =====
  day_pct_moved?: number;
  gain_loss_pct_vs_pp?: number;

  // ===== CALCULATED: Portfolio =====
  pct_portfolio_invested_at_entry?: number;
  pct_portfolio_current?: number;

  // ===== CALCULATED: Time =====
  trading_days_open?: number;

  // ===== CALCULATED: Risk/ATR Metrics =====
  risk_atr_pct_above_low?: number;
  multiple_from_sma_at_entry?: number;
  atr_multiple_from_sma_current?: number;

  // ===== CALCULATED: Stop Levels =====
  stop_3?: number;
  stop_2?: number;
  stop_1?: number;
  entry_pct_above_stop3?: number;
  one_r?: number;

  // ===== CALCULATED: Take Profit Levels =====
  tp_1x?: number;
  tp_2x?: number;
  tp_3x?: number;

  // ===== CALCULATED: Exit Info =====
  sell_price_at_entry?: number;  // SP

  // ===== TRANSACTION ROLLUPS =====
  shares_exited: number;
  shares_remaining?: number;
  total_proceeds: number;
  total_fees: number;
  avg_exit_price?: number;

  // ===== CALCULATED: PnL =====
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;

  // ===== STATUS =====
  status?: string;  // OPEN, PARTIAL, CLOSED

  // ===== AUDIT =====
  created_at: string;
  updated_at: string;
}

export interface TradeCreate {
  trade_id: string;
  ticker: string;
  purchase_price: number;
  purchase_date: string;
  shares: number;
  entry_day_low?: number;
  stop_override?: number;
  portfolio_size?: number;
}

export interface TradeUpdate {
  entry_day_low?: number;
  stop_override?: number;
  portfolio_size?: number;
}

export interface Transaction {
  id: number;
  trade_id: string;
  exit_date: string;  // Changed from transaction_date
  action: ActionType;
  ticker?: string;
  shares: number;
  price: number;
  proceeds?: number;
  fees: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionCreate {
  trade_id: string;
  exit_date: string;
  action: ActionType;
  ticker?: string;
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
  total_portfolio_value?: number;
}

// Updated action types to include TP1, TP2, TP3, Manual
export type ActionType = 'Stop1' | 'Stop2' | 'Stop3' | 'TP1' | 'TP2' | 'TP3' | 'Manual' | 'Other';
export type TradeStatus = 'OPEN' | 'PARTIAL' | 'CLOSED';

// Helper type for column groups (used in UI)
export interface ColumnGroup {
  name: string;
  color: string;  // For header background
  columns: string[];
}

// Column configuration for Entries page
export const ENTRIES_COLUMN_GROUPS: ColumnGroup[] = [
  {
    name: 'Entry',
    color: 'green',
    columns: [
      'trade_id',
      'ticker',
      'day_pct_moved',
      'current_price',
      'gain_loss_pct_vs_pp',
      'sell_price_at_entry',
      'purchase_price',
      'pct_portfolio_invested_at_entry',
      'pct_portfolio_current',
      'purchase_date',
      'shares'
    ]
  },
  {
    name: 'Entry/Close Dates',
    color: 'gray',
    columns: [
      'entry_day_low',
      'trading_days_open'
    ]
  },
  {
    name: 'Risk/ATR',
    color: 'cyan',
    columns: [
      'risk_atr_pct_above_low',
      'multiple_from_sma_at_entry',
      'atr_multiple_from_sma_current'
    ]
  },
  {
    name: 'Take Profit',
    color: 'orange',
    columns: [
      'tp_1x',
      'tp_2x',
      'tp_3x',
      'sma_10'
    ]
  },
  {
    name: 'Stops',
    color: 'orange',
    columns: [
      'stop_override',
      'stop_3',
      'stop_2',
      'stop_1',
      'entry_pct_above_stop3'
    ]
  },
  {
    name: 'Indicators',
    color: 'cyan',
    columns: [
      'atr_14',
      'sma_50'
    ]
  },
  {
    name: 'Exits',
    color: 'yellow',
    columns: [
      'shares_exited',
      'shares_remaining',
      'total_proceeds',
      'total_fees',
      'avg_exit_price'
    ]
  },
  {
    name: 'PnL',
    color: 'yellow',
    columns: [
      'realized_pnl',
      'unrealized_pnl',
      'total_pnl',
      'status'
    ]
  }
];

// Column labels (human-readable)
export const COLUMN_LABELS: Record<string, string> = {
  trade_id: 'Trade ID',
  ticker: 'Stock',
  day_pct_moved: 'Day % Moved',
  current_price: 'Current Price',
  gain_loss_pct_vs_pp: '% Gain/Loss vs. LoD (PP)',
  sell_price_at_entry: 'Sell Price at Entry',
  purchase_price: 'Entry / Purchase Price',
  pct_portfolio_invested_at_entry: '% of Portfolio Invested at Entry',
  pct_portfolio_current: '% of Portfolio Current $',
  purchase_date: 'Purchase Date',
  shares: 'Shares (Qty)',
  entry_day_low: 'Entry-day Low',
  trading_days_open: 'Trading Days Open',
  risk_atr_pct_above_low: 'Risk/ATR (% above Low Exit)',
  multiple_from_sma_at_entry: 'Multiple from SMA at Entry',
  atr_multiple_from_sma_current: 'ATR/% Multiple from SMA Current',
  tp_1x: 'TP @ 1X',
  tp_2x: 'TP @ 2X',
  tp_3x: 'TP @ 3X',
  sma_10: 'SMA10',
  stop_override: 'Override',
  stop_3: 'Stop3 (zone)',
  stop_2: 'Stop2 (2/3)',
  stop_1: 'Stop1 (1/3)',
  entry_pct_above_stop3: 'Entry% Above Stop3',
  atr_14: 'ATR(14) (sm)',
  sma_50: 'SMA50',
  shares_exited: 'Exited Shares',
  shares_remaining: 'Remaining Shares',
  total_proceeds: 'Total Proceeds',
  total_fees: 'Total Fees',
  avg_exit_price: 'Avg Exit Price',
  realized_pnl: 'Realized PnL ($)',
  unrealized_pnl: 'Unrealized PnL ($)',
  total_pnl: 'Total PnL ($)',
  status: 'Status',
  // Additional fields
  one_r: '1R',
  atr_at_entry: 'ATR at Entry',
  sma_at_entry: 'SMA at Entry',
  portfolio_size: 'Portfolio Size',
  market_data_updated_at: 'Market Data Updated'
};
