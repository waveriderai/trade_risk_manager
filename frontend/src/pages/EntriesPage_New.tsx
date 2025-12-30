/**
 * Entries Page - WaveRider 3-Stop Trading Journal
 * Matches screenshot UI exactly with dark theme
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Trade, TradeCreate, TradeSummary } from '../types/index_v2';
import { tradesApi } from '../services/api';
import {
  formatCurrency,
  formatPercent,
  formatNumber,
  formatDate,
} from '../utils/formatters';

const EntriesPage: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [summary, setSummary] = useState<TradeSummary | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load trades
  const loadTrades = useCallback(async () => {
    try {
      setLoading(true);
      const params = statusFilter !== 'ALL' ? { status: statusFilter } : {};
      const data = await tradesApi.list(params);
      setTrades(data);
    } catch (error) {
      console.error('Error loading trades:', error);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  // Load summary
  const loadSummary = useCallback(async () => {
    try {
      const data = await tradesApi.summary();
      setSummary(data);
    } catch (error) {
      console.error('Error loading summary:', error);
    }
  }, []);

  useEffect(() => {
    loadTrades();
    loadSummary();
  }, [loadTrades, loadSummary]);

  const handleRefreshAll = async () => {
    setLoading(true);
    await Promise.all([loadTrades(), loadSummary()]);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-[1800px] mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">
                <span className="text-blue-400">3-Stop</span> Trading Journal
              </h1>
              <p className="text-sm text-gray-400">
                Manage your trade positions and track performance
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleRefreshAll}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-100 rounded transition disabled:opacity-50"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh All
              </button>
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Trade
              </button>
            </div>
          </div>

          {/* Summary Stats */}
          {summary && (
            <div className="grid grid-cols-7 gap-4 mb-4">
              <StatCard label="Total Trades" value={summary.total_trades} />
              <StatCard label="Open" value={summary.open_trades} color="blue" />
              <StatCard label="Partial" value={summary.partial_trades} color="yellow" />
              <StatCard label="Closed" value={summary.closed_trades} color="gray" />
              <StatCard
                label="Realized P&L"
                value={formatCurrency(summary.total_realized_pnl)}
                color={summary.total_realized_pnl >= 0 ? 'green' : 'red'}
              />
              <StatCard
                label="Unrealized P&L"
                value={formatCurrency(summary.total_unrealized_pnl)}
                color={summary.total_unrealized_pnl >= 0 ? 'green' : 'red'}
              />
              <StatCard
                label="Total P&L"
                value={formatCurrency(summary.total_pnl)}
                color={summary.total_pnl >= 0 ? 'green' : 'red'}
                large
              />
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-6 py-6">
        {/* Filters */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-sm text-gray-400">Filter:</span>
          {['ALL', 'OPEN', 'PARTIAL', 'CLOSED'].map((filter) => (
            <button
              key={filter}
              onClick={() => setStatusFilter(filter)}
              className={`px-4 py-1.5 text-sm rounded transition ${
                statusFilter === filter
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {filter}
            </button>
          ))}
        </div>

        {/* Trades Table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-700 text-gray-300 text-sm">
                  <th className="px-4 py-3 text-left font-medium">ID</th>
                  <th className="px-4 py-3 text-left font-medium">TICKER</th>
                  <th className="px-4 py-3 text-left font-medium">ENTRY DATE</th>
                  <th className="px-4 py-3 text-right font-medium">ENTRY</th>
                  <th className="px-4 py-3 text-right font-medium">SHARES</th>
                  <th className="px-4 py-3 text-right font-medium">CURRENT</th>
                  <th className="px-4 py-3 text-right font-medium">% CHG</th>
                  <th className="px-4 py-3 text-right font-medium">STOP3</th>
                  <th className="px-4 py-3 text-right font-medium">STOP2</th>
                  <th className="px-4 py-3 text-right font-medium">STOP1</th>
                  <th className="px-4 py-3 text-right font-medium">1R</th>
                  <th className="px-4 py-3 text-right font-medium">REMAINING</th>
                  <th className="px-4 py-3 text-right font-medium">REALIZED</th>
                  <th className="px-4 py-3 text-right font-medium">UNREALIZED</th>
                  <th className="px-4 py-3 text-right font-medium">TOTAL P&L</th>
                  <th className="px-4 py-3 text-right font-medium">R-MULT</th>
                  <th className="px-4 py-3 text-center font-medium">STATUS</th>
                  <th className="px-4 py-3 text-center font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {loading ? (
                  <tr>
                    <td colSpan={18} className="px-4 py-8 text-center text-gray-400">
                      Loading trades...
                    </td>
                  </tr>
                ) : trades.length === 0 ? (
                  <tr>
                    <td colSpan={18} className="px-4 py-8 text-center text-gray-400">
                      No trades found. Create your first trade to get started.
                    </td>
                  </tr>
                ) : (
                  trades.map((trade) => (
                    <TradeRow key={trade.trade_id} trade={trade} />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Create Trade Modal */}
      {showCreateModal && (
        <CreateTradeModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            handleRefreshAll();
          }}
        />
      )}
    </div>
  );
};

// Stat Card Component
const StatCard: React.FC<{
  label: string;
  value: string | number;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'gray';
  large?: boolean;
}> = ({ label, value, color = 'gray', large = false }) => {
  const colorClasses = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    red: 'text-red-400',
    yellow: 'text-yellow-400',
    gray: 'text-gray-300',
  };

  return (
    <div className="bg-gray-700 rounded-lg px-4 py-3">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className={`${large ? 'text-2xl' : 'text-xl'} font-bold ${colorClasses[color]}`}>
        {value}
      </div>
    </div>
  );
};

// Trade Row Component
const TradeRow: React.FC<{ trade: Trade }> = ({ trade }) => {
  const pnlColor = (val: number) => {
    if (val > 0) return 'text-green-400';
    if (val < 0) return 'text-red-400';
    return 'text-gray-300';
  };

  const statusColor = (status: string) => {
    if (status === 'OPEN') return 'bg-blue-600 text-white';
    if (status === 'PARTIAL') return 'bg-yellow-600 text-white';
    if (status === 'CLOSED') return 'bg-gray-600 text-white';
    return 'bg-gray-600 text-white';
  };

  return (
    <tr className="hover:bg-gray-750 transition text-sm">
      <td className="px-4 py-3">
        <a
          href={`/trades/${trade.trade_id}`}
          className="text-blue-400 hover:text-blue-300 font-medium"
        >
          {trade.trade_id}
        </a>
      </td>
      <td className="px-4 py-3 font-semibold text-white">{trade.ticker}</td>
      <td className="px-4 py-3 text-gray-300">{formatDate(trade.purchase_date)}</td>
      <td className="px-4 py-3 text-right text-gray-300">
        {formatCurrency(trade.purchase_price)}
      </td>
      <td className="px-4 py-3 text-right text-gray-300">{trade.shares}</td>
      <td className="px-4 py-3 text-right text-white font-medium">
        {formatCurrency(trade.current_price)}
      </td>
      <td className={`px-4 py-3 text-right font-semibold ${pnlColor(trade.cp_pct_diff_from_entry || 0)}`}>
        {formatPercent(trade.cp_pct_diff_from_entry, 2)}
      </td>
      <td className="px-4 py-3 text-right text-red-400">
        {formatCurrency(trade.stop_3)}
      </td>
      <td className="px-4 py-3 text-right text-orange-400">
        {formatCurrency(trade.stop_2)}
      </td>
      <td className="px-4 py-3 text-right text-yellow-400">
        {formatCurrency(trade.stop_1)}
      </td>
      <td className="px-4 py-3 text-right text-gray-300">
        {formatCurrency(trade.one_r)}
      </td>
      <td className="px-4 py-3 text-right text-gray-300">
        {trade.shares_remaining}
      </td>
      <td className={`px-4 py-3 text-right font-medium ${pnlColor(trade.realized_pnl)}`}>
        {formatCurrency(trade.realized_pnl)}
      </td>
      <td className={`px-4 py-3 text-right font-medium ${pnlColor(trade.unrealized_pnl)}`}>
        {formatCurrency(trade.unrealized_pnl)}
      </td>
      <td className={`px-4 py-3 text-right font-bold ${pnlColor(trade.total_pnl)}`}>
        {formatCurrency(trade.total_pnl)}
      </td>
      <td className={`px-4 py-3 text-right font-bold ${pnlColor(trade.r_multiple || 0)}`}>
        {trade.r_multiple ? formatNumber(trade.r_multiple, 2) + 'R' : '—'}
      </td>
      <td className="px-4 py-3 text-center">
        <span className={`inline-block px-2 py-1 text-xs rounded ${statusColor(trade.status || '')}`}>
          {trade.status}
        </span>
      </td>
      <td className="px-4 py-3 text-center">
        <button className="text-gray-400 hover:text-white transition">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </td>
    </tr>
  );
};

// Create Trade Modal Component
const CreateTradeModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
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
      onSuccess();
    } catch (error: any) {
      console.error('Error creating trade:', error);
      alert(error.response?.data?.detail || 'Failed to create trade');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">New Trade</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Trade ID *
            </label>
            <input
              type="text"
              required
              value={formData.trade_id}
              onChange={(e) => setFormData({ ...formData, trade_id: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., AAPL01"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Ticker *
            </label>
            <input
              type="text"
              required
              value={formData.ticker}
              onChange={(e) => setFormData({ ...formData, ticker: e.target.value.toUpperCase() })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., AAPL"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Purchase Date *
            </label>
            <input
              type="date"
              required
              value={formData.purchase_date}
              onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Purchase Price *
            </label>
            <input
              type="number"
              step="0.01"
              required
              value={formData.purchase_price || ''}
              onChange={(e) => setFormData({ ...formData, purchase_price: parseFloat(e.target.value) })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="0.00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Shares *
            </label>
            <input
              type="number"
              required
              value={formData.shares || ''}
              onChange={(e) => setFormData({ ...formData, shares: parseInt(e.target.value) })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="100"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Entry Day Low (optional)
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.entry_day_low || ''}
              onChange={(e) => setFormData({ ...formData, entry_day_low: parseFloat(e.target.value) || undefined })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="0.00"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Add Transaction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EntriesPage;
