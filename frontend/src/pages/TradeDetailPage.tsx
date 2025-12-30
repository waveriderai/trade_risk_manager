/**
 * Trade Detail Page - Comprehensive V2 view of a single trade.
 * Shows entry details, linked transactions, and computed summary.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Trade, Transaction } from '../types';
import { tradesApi, transactionsApi } from '../services/api';
import {
  formatCurrency,
  formatPercent,
  formatDate,
  formatDateTime,
  getStatusColor,
} from '../utils/formatters';

const TradeDetailPage: React.FC = () => {
  const { tradeId } = useParams<{ tradeId: string }>();
  const [trade, setTrade] = useState<Trade | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!tradeId) return;

    setLoading(true);
    try {
      const [tradeData, transactionsData] = await Promise.all([
        tradesApi.get(tradeId),
        transactionsApi.list({ trade_id: tradeId }),
      ]);
      setTrade(tradeData);
      setTransactions(transactionsData);
    } catch (error) {
      console.error('Error loading trade:', error);
      alert('Failed to load trade details');
    } finally {
      setLoading(false);
    }
  }, [tradeId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = async () => {
    if (!tradeId) return;
    try {
      await tradesApi.refresh(tradeId);
      loadData();
      alert('Market data refreshed');
    } catch (error) {
      console.error('Error refreshing:', error);
      alert('Failed to refresh market data');
    }
  };

  if (loading) {
    return <div className="container mx-auto p-6">Loading...</div>;
  }

  if (!trade) {
    return <div className="container mx-auto p-6">Trade not found</div>;
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {trade.trade_id} - {trade.ticker}
          </h1>
          <span className={`inline-block px-3 py-1 rounded text-sm mt-2 ${getStatusColor(trade.status)}`}>
            {trade.status}
          </span>
        </div>
        <div className="flex gap-2">
          <button onClick={handleRefresh} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Refresh Market Data
          </button>
          <button
            onClick={() => (window.location.href = '/entries')}
            className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300"
          >
            Back to Entries
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Entry Details */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Entry Details</h2>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-gray-600">Purchase Date:</dt>
              <dd className="font-medium">{formatDate(trade.purchase_date)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Purchase Price:</dt>
              <dd className="font-medium">{formatCurrency(trade.purchase_price)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Shares:</dt>
              <dd className="font-medium">{trade.shares}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Shares Remaining:</dt>
              <dd className="font-medium">{trade.shares_remaining}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Shares Exited:</dt>
              <dd className="font-medium">{trade.shares_exited}</dd>
            </div>
            {trade.entry_day_low && (
              <div className="flex justify-between">
                <dt className="text-gray-600">Entry-day Low:</dt>
                <dd className="font-medium">{formatCurrency(trade.entry_day_low)}</dd>
              </div>
            )}
            {trade.portfolio_size && (
              <div className="flex justify-between">
                <dt className="text-gray-600">Portfolio Size:</dt>
                <dd className="font-medium">{formatCurrency(trade.portfolio_size)}</dd>
              </div>
            )}
            {trade.trading_days_open != null && (
              <div className="flex justify-between">
                <dt className="text-gray-600">Trading Days Open:</dt>
                <dd className="font-medium">{trade.trading_days_open}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Market Data */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Market Data</h2>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-gray-600">Current Price:</dt>
              <dd className="font-medium">{formatCurrency(trade.current_price)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">ATR(14):</dt>
              <dd className="font-medium">{formatCurrency(trade.atr_14)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">SMA(50):</dt>
              <dd className="font-medium">{formatCurrency(trade.sma_50)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">SMA(10):</dt>
              <dd className="font-medium">{formatCurrency(trade.sma_10)}</dd>
            </div>
            {trade.atr_at_entry && (
              <div className="flex justify-between border-t pt-2 mt-2">
                <dt className="text-gray-600 text-sm">ATR at Entry:</dt>
                <dd className="font-medium text-sm">{formatCurrency(trade.atr_at_entry)}</dd>
              </div>
            )}
            {trade.sma_at_entry && (
              <div className="flex justify-between">
                <dt className="text-gray-600 text-sm">SMA at Entry:</dt>
                <dd className="font-medium text-sm">{formatCurrency(trade.sma_at_entry)}</dd>
              </div>
            )}
            <div className="flex justify-between border-t pt-2 mt-2">
              <dt className="text-gray-600 text-xs">Last Updated:</dt>
              <dd className="font-medium text-xs">{formatDateTime(trade.market_data_updated_at)}</dd>
            </div>
          </dl>
        </div>

        {/* Stop Levels & Take Profit */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Stop Levels</h2>
          <dl className="space-y-2">
            <div className="flex justify-between bg-red-50 p-2 rounded">
              <dt className="font-medium">Stop 3:</dt>
              <dd className="font-bold text-red-700">{formatCurrency(trade.stop_3)}</dd>
            </div>
            <div className="flex justify-between bg-orange-50 p-2 rounded">
              <dt className="font-medium">Stop 2:</dt>
              <dd className="font-bold text-orange-700">{formatCurrency(trade.stop_2)}</dd>
            </div>
            <div className="flex justify-between bg-yellow-50 p-2 rounded">
              <dt className="font-medium">Stop 1:</dt>
              <dd className="font-bold text-yellow-700">{formatCurrency(trade.stop_1)}</dd>
            </div>
            <div className="flex justify-between mt-4 pt-4 border-t">
              <dt className="text-gray-600">1R Distance:</dt>
              <dd className="font-medium">{formatCurrency(trade.one_r)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Entry % Above Stop3:</dt>
              <dd className="font-medium">{formatPercent(trade.entry_pct_above_stop3)}</dd>
            </div>
          </dl>

          <h3 className="text-lg font-bold mt-6 mb-2">Take Profit Levels</h3>
          <dl className="space-y-2">
            <div className="flex justify-between bg-green-50 p-2 rounded">
              <dt className="font-medium">TP @1X:</dt>
              <dd className="font-bold text-green-700">{formatCurrency(trade.tp_1x)}</dd>
            </div>
            <div className="flex justify-between bg-green-100 p-2 rounded">
              <dt className="font-medium">TP @2X:</dt>
              <dd className="font-bold text-green-800">{formatCurrency(trade.tp_2x)}</dd>
            </div>
            <div className="flex justify-between bg-green-200 p-2 rounded">
              <dt className="font-medium">TP @3X:</dt>
              <dd className="font-bold text-green-900">{formatCurrency(trade.tp_3x)}</dd>
            </div>
          </dl>
        </div>

        {/* Performance Summary */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Performance</h2>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-gray-600">Realized PnL:</dt>
              <dd className={`font-medium ${trade.realized_pnl > 0 ? 'text-green-600' : trade.realized_pnl < 0 ? 'text-red-600' : ''}`}>
                {formatCurrency(trade.realized_pnl)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Unrealized PnL:</dt>
              <dd className={`font-medium ${trade.unrealized_pnl > 0 ? 'text-green-600' : trade.unrealized_pnl < 0 ? 'text-red-600' : ''}`}>
                {formatCurrency(trade.unrealized_pnl)}
              </dd>
            </div>
            <div className="flex justify-between bg-gray-50 p-2 rounded">
              <dt className="font-bold">Total PnL:</dt>
              <dd className={`font-bold text-lg ${trade.total_pnl > 0 ? 'text-green-600' : trade.total_pnl < 0 ? 'text-red-600' : ''}`}>
                {formatCurrency(trade.total_pnl)}
              </dd>
            </div>
            {trade.gain_loss_pct_vs_pp != null && (
              <div className="flex justify-between">
                <dt className="text-gray-600">% Gain/Loss vs PP:</dt>
                <dd className={`font-medium ${trade.gain_loss_pct_vs_pp > 0 ? 'text-green-600' : trade.gain_loss_pct_vs_pp < 0 ? 'text-red-600' : ''}`}>
                  {formatPercent(trade.gain_loss_pct_vs_pp)}
                </dd>
              </div>
            )}
            {trade.day_pct_moved != null && (
              <div className="flex justify-between">
                <dt className="text-gray-600">Day % Moved:</dt>
                <dd className={`font-medium ${trade.day_pct_moved > 0 ? 'text-green-600' : trade.day_pct_moved < 0 ? 'text-red-600' : ''}`}>
                  {formatPercent(trade.day_pct_moved)}
                </dd>
              </div>
            )}
            {trade.avg_exit_price && (
              <div className="flex justify-between mt-4 pt-4 border-t">
                <dt className="text-gray-600">Avg Exit Price:</dt>
                <dd className="font-medium">{formatCurrency(trade.avg_exit_price)}</dd>
              </div>
            )}
            {trade.total_proceeds > 0 && (
              <div className="flex justify-between">
                <dt className="text-gray-600">Total Proceeds:</dt>
                <dd className="font-medium">{formatCurrency(trade.total_proceeds)}</dd>
              </div>
            )}
            {trade.total_fees > 0 && (
              <div className="flex justify-between">
                <dt className="text-gray-600">Total Fees:</dt>
                <dd className="font-medium">{formatCurrency(trade.total_fees)}</dd>
              </div>
            )}
          </dl>
        </div>
      </div>

      {/* Transactions List */}
      <div className="mt-6 bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Exit Transactions ({transactions.length})</h2>

        {transactions.length === 0 ? (
          <p className="text-gray-500">No exit transactions yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Exit Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ticker</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Shares</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Fees</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Proceeds</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((txn) => (
                  <tr key={txn.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm">{formatDate(txn.exit_date)}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded text-xs ${getActionColor(txn.action)}`}>{txn.action}</span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold">{txn.ticker || trade.ticker}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">{txn.shares}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">{formatCurrency(txn.price)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">{formatCurrency(txn.fees)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium">{formatCurrency(txn.proceeds)}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{txn.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

const getActionColor = (action: string): string => {
  const colors: Record<string, string> = {
    Stop1: 'bg-yellow-100 text-yellow-800',
    Stop2: 'bg-orange-100 text-orange-800',
    Stop3: 'bg-red-100 text-red-800',
    TP1: 'bg-green-100 text-green-800',
    TP2: 'bg-green-200 text-green-900',
    TP3: 'bg-green-300 text-green-900',
    Manual: 'bg-blue-100 text-blue-800',
    Other: 'bg-gray-100 text-gray-800',
  };
  return colors[action] || '';
};

export default TradeDetailPage;
