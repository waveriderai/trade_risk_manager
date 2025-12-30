/**
 * Transactions Page - Exit Transactions
 * Matches screenshot UI with dark theme
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Transaction, TransactionCreate, Trade } from '../types/index_v2';
import { tradesApi } from '../services/api';
import { formatCurrency, formatDate } from '../utils/formatters';

const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [tradeFilter, setTradeFilter] = useState<string>('All Trades');
  const [loading, setLoading] = useState(false);

  const loadTransactions = useCallback(async () => {
    try {
      setLoading(true);
      // Load all transactions
      const allTrades = await tradesApi.list({});
      const allTransactions: Transaction[] = [];
      
      for (const trade of allTrades) {
        // Fetch transactions for each trade (assuming API endpoint exists)
        // For now, we'll just show placeholder
      }
      
      setTransactions(allTransactions);
    } catch (error) {
      console.error('Error loading transactions:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadTrades = useCallback(async () => {
    try {
      const data = await tradesApi.list({});
      setTrades(data);
    } catch (error) {
      console.error('Error loading trades:', error);
    }
  }, []);

  useEffect(() => {
    loadTransactions();
    loadTrades();
  }, [loadTransactions, loadTrades]);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-[1800px] mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">Exit Transactions</h1>
              <p className="text-sm text-gray-400">
                Track partial and full exits from your positions
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-100 rounded transition"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload CSV
              </button>
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Transaction
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-6 py-6">
        {/* Filter */}
        <div className="mb-4">
          <label className="text-sm text-gray-400 mr-2">Filter by Trade:</label>
          <select
            value={tradeFilter}
            onChange={(e) => setTradeFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option>All Trades</option>
            {trades.map((trade) => (
              <option key={trade.trade_id} value={trade.trade_id}>
                {trade.trade_id} - {trade.ticker}
              </option>
            ))}
          </select>
        </div>

        {/* Transactions Table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-700 text-gray-300 text-sm">
                  <th className="px-4 py-3 text-left font-medium">DATE</th>
                  <th className="px-4 py-3 text-left font-medium">TRADE ID</th>
                  <th className="px-4 py-3 text-left font-medium">ACTION</th>
                  <th className="px-4 py-3 text-right font-medium">SHARES</th>
                  <th className="px-4 py-3 text-right font-medium">PRICE</th>
                  <th className="px-4 py-3 text-right font-medium">FEES</th>
                  <th className="px-4 py-3 text-right font-medium">PROCEEDS</th>
                  <th className="px-4 py-3 text-left font-medium">NOTES</th>
                  <th className="px-4 py-3 text-center font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {loading ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-gray-400">
                      Loading transactions...
                    </td>
                  </tr>
                ) : transactions.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-gray-400">
                      No exit transactions yet. Add your first transaction to get started.
                    </td>
                  </tr>
                ) : (
                  transactions.map((txn) => (
                    <TransactionRow key={txn.id} transaction={txn} />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Add Transaction Modal */}
      {showAddModal && (
        <AddTransactionModal
          trades={trades}
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            loadTransactions();
          }}
        />
      )}

      {/* Upload CSV Modal */}
      {showUploadModal && (
        <UploadCSVModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            loadTransactions();
          }}
        />
      )}
    </div>
  );
};

// Transaction Row Component
const TransactionRow: React.FC<{ transaction: Transaction }> = ({ transaction }) => {
  const getActionColor = (action: string) => {
    if (action.startsWith('Stop')) return 'bg-red-600 text-white';
    if (action.startsWith('TP')) return 'bg-green-600 text-white';
    return 'bg-gray-600 text-white';
  };

  return (
    <tr className="hover:bg-gray-750 transition text-sm">
      <td className="px-4 py-3 text-gray-300">{formatDate(transaction.exit_date)}</td>
      <td className="px-4 py-3">
        <a
          href={`/trades/${transaction.trade_id}`}
          className="text-blue-400 hover:text-blue-300 font-medium"
        >
          {transaction.trade_id}
        </a>
      </td>
      <td className="px-4 py-3">
        <span className={`inline-block px-2 py-1 text-xs rounded ${getActionColor(transaction.action)}`}>
          {transaction.action}
        </span>
      </td>
      <td className="px-4 py-3 text-right text-gray-300">{transaction.shares}</td>
      <td className="px-4 py-3 text-right text-white font-medium">
        {formatCurrency(transaction.price)}
      </td>
      <td className="px-4 py-3 text-right text-gray-300">
        {formatCurrency(transaction.fees)}
      </td>
      <td className="px-4 py-3 text-right text-green-400 font-medium">
        {formatCurrency(transaction.proceeds)}
      </td>
      <td className="px-4 py-3 text-gray-400 text-xs">{transaction.notes || '—'}</td>
      <td className="px-4 py-3 text-center">
        <button className="text-red-400 hover:text-red-300 transition">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </td>
    </tr>
  );
};

// Add Transaction Modal
const AddTransactionModal: React.FC<{
  trades: Trade[];
  onClose: () => void;
  onSuccess: () => void;
}> = ({ trades, onClose, onSuccess }) => {
  const [formData, setFormData] = useState<TransactionCreate>({
    trade_id: '',
    exit_date: new Date().toISOString().split('T')[0],
    action: 'Profit',
    shares: 0,
    price: 0,
    fees: 0,
    notes: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      // Call API to create transaction
      // await tradesApi.createTransaction(formData);
      onSuccess();
    } catch (error: any) {
      console.error('Error creating transaction:', error);
      alert(error.response?.data?.detail || 'Failed to create transaction');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 max-w-lg w-full">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">Add Exit Transaction</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Trade ID *
              </label>
              <select
                required
                value={formData.trade_id}
                onChange={(e) => setFormData({ ...formData, trade_id: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select trade...</option>
                {trades.map((trade) => (
                  <option key={trade.trade_id} value={trade.trade_id}>
                    {trade.trade_id} - {trade.ticker}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Action *
              </label>
              <select
                required
                value={formData.action}
                onChange={(e) => setFormData({ ...formData, action: e.target.value as any })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Profit">Profit</option>
                <option value="Stop1">Stop1</option>
                <option value="Stop2">Stop2</option>
                <option value="Stop3">Stop3</option>
                <option value="TP1">TP1</option>
                <option value="TP2">TP2</option>
                <option value="TP3">TP3</option>
                <option value="Manual">Manual</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Date *
            </label>
            <input
              type="date"
              required
              value={formData.exit_date}
              onChange={(e) => setFormData({ ...formData, exit_date: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
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
                Price *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.price || ''}
                onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0.00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Fees
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.fees || ''}
                onChange={(e) => setFormData({ ...formData, fees: parseFloat(e.target.value) || 0 })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Notes
            </label>
            <textarea
              value={formData.notes || ''}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Optional notes..."
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
              {submitting ? 'Adding...' : 'Add Transaction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Upload CSV Modal
const UploadCSVModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 max-w-2xl w-full">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">Upload Transactions from CSV</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="text-center py-12">
          <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-gray-400 mb-4">Drop CSV file here or click to upload</p>
          <p className="text-xs text-gray-500 mb-6">
            Columns: trade_id, transaction_date, action, shares, price, fees, notes
          </p>
          <input
            type="file"
            accept=".csv"
            className="hidden"
            id="csv-upload"
          />
          <label
            htmlFor="csv-upload"
            className="inline-block px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded cursor-pointer transition"
          >
            Choose File
          </label>
        </div>

        <div className="bg-gray-900 rounded p-4 mt-4">
          <p className="text-sm text-gray-400 font-mono mb-2">CSV Format Example:</p>
          <pre className="text-xs text-gray-500 overflow-x-auto">
{`trade_id,transaction_date,action,shares,price,fees,notes
1,2024-01-15,Stop1,100,55.50,0,First stop hit
1,2024-01-20,Profit,50,60.00,1.50,Taking profits
2,2024-01-22,Stop3,200,45.00,1.50,Full exit`}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default TransactionsPage;
