/**
 * Entries Page - Spreadsheet-style grid of all trades.
 * Shows one row per Trade ID with calculated fields.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

import { Trade, TradeCreate } from '../types';
import { tradesApi } from '../services/api';
import {
  formatCurrency,
  formatPercent,
  formatRMultiple,
  formatDate,
  formatDateTime,
  getStatusColor,
} from '../utils/formatters';

const EntriesPage: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Load trades
  const loadTrades = useCallback(async () => {
    setLoading(true);
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const data = await tradesApi.list(params);
      setTrades(data);
    } catch (error) {
      console.error('Error loading trades:', error);
      alert('Failed to load trades');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadTrades();
  }, [loadTrades]);

  // Column definitions
  const columnDefs: ColDef[] = [
    {
      headerName: 'Trade ID',
      field: 'trade_id',
      pinned: 'left',
      width: 120,
      cellRenderer: (params: any) => (
        <a
          href={`/trades/${params.value}`}
          className="text-blue-600 hover:underline"
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
      headerName: 'Status',
      field: 'status',
      width: 100,
      cellRenderer: (params: any) => (
        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(params.value)}`}>
          {params.value}
        </span>
      ),
    },
    { headerName: 'Ticker', field: 'ticker', width: 80 },
    {
      headerName: 'Entry Date',
      field: 'entry_date',
      width: 120,
      valueFormatter: (params) => formatDate(params.value),
    },
    {
      headerName: 'Entry Price',
      field: 'entry_price',
      width: 110,
      valueFormatter: (params) => formatCurrency(params.value),
    },
    { headerName: 'Entry Shares', field: 'entry_shares', width: 120 },
    { headerName: 'Shares Remaining', field: 'shares_remaining', width: 140 },
    {
      headerName: 'Current Price',
      field: 'current_price',
      width: 120,
      valueFormatter: (params) => formatCurrency(params.value),
    },
    {
      headerName: 'Stop 3',
      field: 'stop_3',
      width: 100,
      valueFormatter: (params) => formatCurrency(params.value),
      cellClass: 'bg-red-50',
    },
    {
      headerName: 'Stop 2',
      field: 'stop_2',
      width: 100,
      valueFormatter: (params) => formatCurrency(params.value),
      cellClass: 'bg-orange-50',
    },
    {
      headerName: 'Stop 1',
      field: 'stop_1',
      width: 100,
      valueFormatter: (params) => formatCurrency(params.value),
      cellClass: 'bg-yellow-50',
    },
    {
      headerName: '1R Distance',
      field: 'one_r_distance',
      width: 120,
      valueFormatter: (params) => formatCurrency(params.value),
    },
    {
      headerName: 'Realized PnL',
      field: 'realized_pnl',
      width: 130,
      valueFormatter: (params) => formatCurrency(params.value),
      cellClass: (params) => (params.value > 0 ? 'text-green-600' : params.value < 0 ? 'text-red-600' : ''),
    },
    {
      headerName: 'Unrealized PnL',
      field: 'unrealized_pnl',
      width: 140,
      valueFormatter: (params) => formatCurrency(params.value),
      cellClass: (params) => (params.value > 0 ? 'text-green-600' : params.value < 0 ? 'text-red-600' : ''),
    },
    {
      headerName: 'Total PnL',
      field: 'total_pnl',
      width: 130,
      valueFormatter: (params) => formatCurrency(params.value),
      cellClass: (params) => (params.value > 0 ? 'text-green-600 font-bold' : params.value < 0 ? 'text-red-600 font-bold' : 'font-bold'),
    },
    {
      headerName: '% Gain/Loss',
      field: 'percent_gain_loss',
      width: 120,
      valueFormatter: (params) => formatPercent(params.value),
      cellClass: (params) => (params.value > 0 ? 'text-green-600' : params.value < 0 ? 'text-red-600' : ''),
    },
    {
      headerName: 'R-Multiple',
      field: 'r_multiple',
      width: 120,
      valueFormatter: (params) => formatRMultiple(params.value),
      cellClass: (params) => (params.value > 0 ? 'text-green-600' : params.value < 0 ? 'text-red-600' : ''),
    },
    {
      headerName: 'ATR(14)',
      field: 'atr_14',
      width: 100,
      valueFormatter: (params) => formatCurrency(params.value),
    },
    {
      headerName: 'Market Data Updated',
      field: 'market_data_updated_at',
      width: 180,
      valueFormatter: (params) => formatDateTime(params.value),
    },
  ];

  // Refresh market data for selected trade
  const handleRefresh = async (tradeId: string) => {
    try {
      await tradesApi.refresh(tradeId);
      loadTrades();
      alert('Market data refreshed');
    } catch (error) {
      console.error('Error refreshing:', error);
      alert('Failed to refresh market data');
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-4">Trade Entries</h1>

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

      {/* AG Grid */}
      <div className="ag-theme-alpine" style={{ height: '600px', width: '100%' }}>
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
        />
      </div>

      {/* Create Form Modal (simplified - would be a proper modal in production) */}
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

// Simple create trade modal component
const CreateTradeModal: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<TradeCreate>({
    trade_id: '',
    ticker: '',
    entry_date: new Date().toISOString().split('T')[0],
    entry_price: 0,
    entry_shares: 0,
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
            <label className="block text-sm font-medium mb-1">Entry Date *</label>
            <input
              type="date"
              required
              value={formData.entry_date}
              onChange={(e) => setFormData({ ...formData, entry_date: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Entry Price *</label>
            <input
              type="number"
              step="0.01"
              required
              value={formData.entry_price || ''}
              onChange={(e) => setFormData({ ...formData, entry_price: parseFloat(e.target.value) })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Entry Shares *</label>
            <input
              type="number"
              required
              value={formData.entry_shares || ''}
              onChange={(e) => setFormData({ ...formData, entry_shares: parseInt(e.target.value) })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Low of Day (optional)</label>
            <input
              type="number"
              step="0.01"
              value={formData.low_of_day || ''}
              onChange={(e) => setFormData({ ...formData, low_of_day: parseFloat(e.target.value) || undefined })}
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
