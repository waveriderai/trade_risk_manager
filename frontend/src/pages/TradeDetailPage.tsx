/**
 * Trade Detail Page - Comprehensive view of a single trade.
 * Shows entry details, linked transactions, and computed summary.
 */
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Trade, Transaction } from '../types';
import { tradesApi, transactionsApi } from '../services/api';
import {
  formatCurrency,
  formatPercent,
  formatRMultiple,
  formatDate,
  formatDateTime,
  getStatusColor,
} from '../utils/formatters';

const TradeDetailPage: React.FC = () => {
  const { tradeId } = useParams<{ tradeId: string }>();
  const [trade, setTrade] = useState<Trade | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [tradeId]);

  const loadData = async () => {
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
  };

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
              <dt className="text-gray-600">Entry Date:</dt>
              <dd className="font-medium">{formatDate(trade.entry_date)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Entry Price:</dt>
              <dd className="font-medium">{formatCurrency(trade.entry_price)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Entry Shares:</dt>
              <dd className="font-medium">{trade.entry_shares}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Shares Remaining:</dt>
              <dd className="font-medium">{trade.shares_remaining}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Shares Exited:</dt>
              <dd className="font-medium">{trade.total_shares_exited}</dd>
            </div>
            {trade.low_of_day && (
              <div className="flex justify-between">
                <dt className="text-gray-600">Low of Day:</dt>
                <dd className="font-medium">{formatCurrency(trade.low_of_day)}</dd>
              </div>
            )}
            {trade.portfolio_size && (
              <div className="flex justify-between">
                <dt className="text-gray-600">Portfolio Size:</dt>
                <dd className="font-medium">{formatCurrency(trade.portfolio_size)}</dd>
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
            <div className="flex justify-between">
              <dt className="text-gray-600">Last Updated:</dt>
              <dd className="font-medium text-sm">{formatDateTime(trade.market_data_updated_at)}</dd>
            </div>
          </dl>
        </div>

        {/* Stop Levels */}
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
              <dd className="font-medium">{formatCurrency(trade.one_r_distance)}</dd>
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
            <div className="flex justify-between">
              <dt className="text-gray-600">% Gain/Loss:</dt>
              <dd className={`font-medium ${trade.percent_gain_loss && trade.percent_gain_loss > 0 ? 'text-green-600' : trade.percent_gain_loss && trade.percent_gain_loss < 0 ? 'text-red-600' : ''}`}>
                {formatPercent(trade.percent_gain_loss)}
              </dd>
            </div>
            <div className="flex justify-between bg-blue-50 p-2 rounded">
              <dt className="font-bold">R-Multiple:</dt>
              <dd className={`font-bold text-lg ${trade.r_multiple && trade.r_multiple > 0 ? 'text-green-600' : trade.r_multiple && trade.r_multiple < 0 ? 'text-red-600' : ''}`}>
                {formatRMultiple(trade.r_multiple)}
              </dd>
            </div>
            {trade.weighted_avg_exit_price && (
              <div className="flex justify-between mt-4 pt-4 border-t">
                <dt className="text-gray-600">Weighted Avg Exit:</dt>
                <dd className="font-medium">{formatCurrency(trade.weighted_avg_exit_price)}</dd>
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
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Shares</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Fees</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Proceeds</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">PnL</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((txn) => (
                  <tr key={txn.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm">{formatDate(txn.transaction_date)}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded text-xs ${getActionColor(txn.action)}`}>{txn.action}</span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">{txn.shares}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">{formatCurrency(txn.price)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">{formatCurrency(txn.fees)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">{formatCurrency(txn.proceeds)}</td>
                    <td className={`px-4 py-3 whitespace-nowrap text-sm text-right font-medium ${txn.pnl && txn.pnl > 0 ? 'text-green-600' : txn.pnl && txn.pnl < 0 ? 'text-red-600' : ''}`}>
                      {formatCurrency(txn.pnl)}
                    </td>
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
    Profit: 'bg-green-100 text-green-800',
    Other: 'bg-gray-100 text-gray-800',
  };
  return colors[action] || '';
};

export default TradeDetailPage;
