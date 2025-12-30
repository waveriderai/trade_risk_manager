/**
 * Entries Page - Complete WaveRider 3-Stop Trading Journal with ALL 36 columns.
 * Matches Google Sheet layout with color-coded column groups.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, ColGroupDef } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

import { Trade, TradeCreate, COLUMN_LABELS } from '../types';
import { tradesApi } from '../services/api';
import {
  formatCurrency,
  formatPercent,
  formatNumber,
  formatDate,
  formatDateTime,
  getStatusColor,
} from '../utils/formatters';

const EntriesPage: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Load trades
  const loadTrades = useCallback(async () => {
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const data = await tradesApi.list(params);
      setTrades(data);
    } catch (error) {
      console.error('Error loading trades:', error);
      alert('Failed to load trades');
    }
  }, [statusFilter]);

  useEffect(() => {
    loadTrades();
  }, [loadTrades]);

  // Helper to get color class for column groups
  const getGroupColor = (color: string): string => {
    const colors: Record<string, string> = {
      green: 'bg-green-100',
      gray: 'bg-gray-100',
      cyan: 'bg-cyan-100',
      orange: 'bg-orange-100',
      yellow: 'bg-yellow-100',
    };
    return colors[color] || 'bg-white';
  };

  // Complete column definitions - ALL 36 COLUMNS in groups
  const columnDefs: (ColDef | ColGroupDef)[] = [
    // ===== ENTRY GROUP (Green) =====
    {
      headerName: 'Entry',
      headerClass: 'bg-green-200 font-bold',
      children: [
        {
          headerName: COLUMN_LABELS.trade_id,
          field: 'trade_id',
          pinned: 'left',
          width: 120,
          cellRenderer: (params: any) => (
            <a
              href={`/trades/${params.value}`}
              className="text-blue-600 hover:underline font-medium"
              onClick={(e) => {
                e.preventDefault();
                window.location.href = `/trades/${params.value}`;
              }}
            >
              {params.value}
            </a>
          ),
        },
        {
          headerName: COLUMN_LABELS.ticker,
          field: 'ticker',
          width: 80,
          cellClass: 'font-semibold',
        },
        {
          headerName: COLUMN_LABELS.day_pct_moved,
          field: 'day_pct_moved',
          width: 120,
          valueFormatter: (params) => formatPercent(params.value),
          cellClass: (params) => params.value > 0 ? 'text-green-600' : params.value < 0 ? 'text-red-600' : '',
        },
        {
          headerName: COLUMN_LABELS.current_price,
          field: 'current_price',
          width: 120,
          valueFormatter: (params) => formatCurrency(params.value),
        },
        {
          headerName: COLUMN_LABELS.cp_pct_diff_from_entry,
          field: 'cp_pct_diff_from_entry',
          width: 160,
          valueFormatter: (params) => formatPercent(params.value),
          cellClass: (params) => params.value > 0 ? 'text-green-600 font-semibold' : params.value < 0 ? 'text-red-600 font-semibold' : '',
        },
        {
          headerName: COLUMN_LABELS.pct_gain_loss_trade,
          field: 'pct_gain_loss_trade',
          width: 160,
          valueFormatter: (params) => formatPercent(params.value),
          cellClass: (params) => params.value > 0 ? 'text-green-600 font-semibold' : params.value < 0 ? 'text-red-600 font-semibold' : '',
        },
        {
          headerName: COLUMN_LABELS.sold_price,
          field: 'sold_price',
          width: 140,
          valueFormatter: (params) => formatCurrency(params.value),
        },
        {
          headerName: COLUMN_LABELS.purchase_price,
          field: 'purchase_price',
          width: 160,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: 'bg-green-50 font-semibold',
        },
        {
          headerName: COLUMN_LABELS.pct_portfolio_invested_at_entry,
          field: 'pct_portfolio_invested_at_entry',
          width: 200,
          valueFormatter: (params) => formatPercent(params.value),
        },
        {
          headerName: COLUMN_LABELS.pct_portfolio_current,
          field: 'pct_portfolio_current',
          width: 180,
          valueFormatter: (params) => formatPercent(params.value),
        },
        {
          headerName: COLUMN_LABELS.purchase_date,
          field: 'purchase_date',
          width: 130,
          valueFormatter: (params) => formatDate(params.value),
        },
        {
          headerName: COLUMN_LABELS.shares,
          field: 'shares',
          width: 100,
        },
      ],
    },

    // ===== ENTRY/CLOSE DATES GROUP (Gray) =====
    {
      headerName: 'Entry/Close Dates',
      headerClass: 'bg-gray-200 font-bold',
      children: [
        {
          headerName: COLUMN_LABELS.entry_day_low,
          field: 'entry_day_low',
          width: 120,
          valueFormatter: (params) => formatCurrency(params.value),
        },
        {
          headerName: COLUMN_LABELS.trading_days_open,
          field: 'trading_days_open',
          width: 140,
        },
      ],
    },

    // ===== RISK/ATR GROUP (Cyan) =====
    {
      headerName: 'Risk/ATR',
      headerClass: 'bg-cyan-200 font-bold',
      children: [
        {
          headerName: COLUMN_LABELS.risk_atr_pct_above_low,
          field: 'risk_atr_pct_above_low',
          width: 180,
          valueFormatter: (params) => formatPercent(params.value),
        },
        {
          headerName: COLUMN_LABELS.atr_pct_multiple_from_ma_at_entry,
          field: 'atr_pct_multiple_from_ma_at_entry',
          width: 200,
          valueFormatter: (params) => formatNumber(params.value, 2),
        },
        {
          headerName: COLUMN_LABELS.atr_pct_multiple_from_ma,
          field: 'atr_pct_multiple_from_ma',
          width: 220,
          valueFormatter: (params) => formatNumber(params.value, 2),
        },
      ],
    },

    // ===== TAKE PROFIT GROUP (Orange) =====
    {
      headerName: 'Take Profit',
      headerClass: 'bg-orange-200 font-bold',
      children: [
        {
          headerName: COLUMN_LABELS.tp_1r,
          field: 'tp_1r',
          width: 100,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: 'bg-orange-50',
        },
        {
          headerName: COLUMN_LABELS.tp_2r,
          field: 'tp_2r',
          width: 100,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: 'bg-orange-50',
        },
        {
          headerName: COLUMN_LABELS.tp_3r,
          field: 'tp_3r',
          width: 100,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: 'bg-orange-50',
        },
        {
          headerName: COLUMN_LABELS.sma_10,
          field: 'sma_10',
          width: 100,
          valueFormatter: (params) => formatCurrency(params.value),
        },
      ],
    },

    // ===== STOPS GROUP (Orange) =====
    {
      headerName: 'Stops',
      headerClass: 'bg-orange-200 font-bold',
      children: [
        {
          headerName: COLUMN_LABELS.stop_override,
          field: 'stop_override',
          width: 100,
          valueFormatter: (params) => formatCurrency(params.value),
          editable: true,
        },
        {
          headerName: COLUMN_LABELS.stop_3,
          field: 'stop_3',
          width: 110,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: 'bg-red-50',
        },
        {
          headerName: COLUMN_LABELS.stop_2,
          field: 'stop_2',
          width: 110,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: 'bg-orange-50',
        },
        {
          headerName: COLUMN_LABELS.stop_1,
          field: 'stop_1',
          width: 110,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: 'bg-yellow-50',
        },
        {
          headerName: COLUMN_LABELS.entry_pct_above_stop3,
          field: 'entry_pct_above_stop3',
          width: 160,
          valueFormatter: (params) => formatPercent(params.value),
        },
      ],
    },

    // ===== INDICATORS GROUP (Cyan) =====
    {
      headerName: 'Indicators',
      headerClass: 'bg-cyan-200 font-bold',
      children: [
        {
          headerName: COLUMN_LABELS.atr_14,
          field: 'atr_14',
          width: 100,
          valueFormatter: (params) => formatCurrency(params.value),
        },
        {
          headerName: COLUMN_LABELS.sma_50,
          field: 'sma_50',
          width: 100,
          valueFormatter: (params) => formatCurrency(params.value),
        },
      ],
    },

    // ===== EXITS GROUP (Yellow) =====
    {
      headerName: 'Exits',
      headerClass: 'bg-yellow-200 font-bold',
      children: [
        {
          headerName: COLUMN_LABELS.shares_exited,
          field: 'shares_exited',
          width: 120,
        },
        {
          headerName: COLUMN_LABELS.shares_remaining,
          field: 'shares_remaining',
          width: 140,
        },
        {
          headerName: COLUMN_LABELS.total_proceeds,
          field: 'total_proceeds',
          width: 130,
          valueFormatter: (params) => formatCurrency(params.value),
        },
        {
          headerName: COLUMN_LABELS.total_fees,
          field: 'total_fees',
          width: 100,
          valueFormatter: (params) => formatCurrency(params.value),
        },
        {
          headerName: COLUMN_LABELS.avg_exit_price,
          field: 'avg_exit_price',
          width: 130,
          valueFormatter: (params) => formatCurrency(params.value),
        },
      ],
    },

    // ===== PNL GROUP (Yellow) =====
    {
      headerName: 'PnL',
      headerClass: 'bg-yellow-200 font-bold',
      children: [
        {
          headerName: COLUMN_LABELS.realized_pnl,
          field: 'realized_pnl',
          width: 130,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: (params) => params.value > 0 ? 'text-green-600 font-semibold' : params.value < 0 ? 'text-red-600 font-semibold' : '',
        },
        {
          headerName: COLUMN_LABELS.unrealized_pnl,
          field: 'unrealized_pnl',
          width: 140,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: (params) => params.value > 0 ? 'text-green-600 font-semibold' : params.value < 0 ? 'text-red-600 font-semibold' : '',
        },
        {
          headerName: COLUMN_LABELS.total_pnl,
          field: 'total_pnl',
          width: 130,
          valueFormatter: (params) => formatCurrency(params.value),
          cellClass: (params) => params.value > 0 ? 'text-green-600 font-bold' : params.value < 0 ? 'text-red-600 font-bold' : 'font-bold',
        },
        {
          headerName: COLUMN_LABELS.status,
          field: 'status',
          width: 100,
          cellRenderer: (params: any) => (
            <span className={`px-2 py-1 rounded text-xs ${getStatusColor(params.value)}`}>
              {params.value}
            </span>
          ),
        },
      ],
    },
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Trade Entries</h1>
        <p className="text-gray-600 mb-4">Complete WaveRider 3-Stop System - 36 Columns</p>

        <div className="flex gap-4 mb-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="">All Trades</option>
            <option value="OPEN">Open</option>
            <option value="PARTIAL">Partial</option>
            <option value="CLOSED">Closed</option>
          </select>

          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            + New Trade
          </button>

          <button
            onClick={loadTrades}
            className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* AG Grid with all 36 columns */}
      <div className="ag-theme-alpine" style={{ height: '700px', width: '100%' }}>
        <AgGridReact
          rowData={trades}
          columnDefs={columnDefs}
          defaultColDef={{
            sortable: true,
            filter: true,
            resizable: true,
          }}
          pagination={true}
          paginationPageSize={20}
          animateRows={true}
          suppressColumnVirtualisation={false}
        />
      </div>

      {/* Create Form Modal */}
      {showCreateForm && (
        <CreateTradeModal
          onClose={() => setShowCreateForm(false)}
          onSuccess={() => {
            setShowCreateForm(false);
            loadTrades();
          }}
        />
      )}
    </div>
  );
};

// Create trade modal component
const CreateTradeModal: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<TradeCreate>({
    trade_id: '',
    ticker: '',
    purchase_date: new Date().toISOString().split('T')[0],
    purchase_price: 0,
    shares: 0,
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      await tradesApi.create(formData);
      alert('Trade created successfully!');
      onSuccess();
    } catch (error: any) {
      console.error('Error creating trade:', error);
      alert(error.response?.data?.detail || 'Failed to create trade');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">Create New Trade</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Trade ID *</label>
            <input
              type="text"
              required
              value={formData.trade_id}
              onChange={(e) => setFormData({ ...formData, trade_id: e.target.value })}
              className="w-full border rounded px-3 py-2"
              placeholder="e.g., AAPL-001"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Ticker *</label>
            <input
              type="text"
              required
              value={formData.ticker}
              onChange={(e) => setFormData({ ...formData, ticker: e.target.value.toUpperCase() })}
              className="w-full border rounded px-3 py-2"
              placeholder="e.g., AAPL"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Purchase Date *</label>
            <input
              type="date"
              required
              value={formData.purchase_date}
              onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Purchase Price *</label>
            <input
              type="number"
              step="0.01"
              required
              value={formData.purchase_price || ''}
              onChange={(e) => setFormData({ ...formData, purchase_price: parseFloat(e.target.value) })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Shares *</label>
            <input
              type="number"
              required
              value={formData.shares || ''}
              onChange={(e) => setFormData({ ...formData, shares: parseInt(e.target.value) })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Entry Day Low (optional)</label>
            <input
              type="number"
              step="0.01"
              value={formData.entry_day_low || ''}
              onChange={(e) => setFormData({ ...formData, entry_day_low: parseFloat(e.target.value) || undefined })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Stop Override (optional)</label>
            <input
              type="number"
              step="0.01"
              value={formData.stop_override || ''}
              onChange={(e) => setFormData({ ...formData, stop_override: parseFloat(e.target.value) || undefined })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Portfolio Size (optional)</label>
            <input
              type="number"
              step="0.01"
              value={formData.portfolio_size || ''}
              onChange={(e) => setFormData({ ...formData, portfolio_size: parseFloat(e.target.value) || undefined })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div className="flex gap-2 pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {submitting ? 'Creating...' : 'Create Trade'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 px-4 py-2 rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EntriesPage;
