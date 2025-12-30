/**
 * Transactions Page - List and manage exit transactions.
 * Supports manual entry and CSV upload.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

import { Transaction, TransactionCreate, ActionType } from '../types';
import { transactionsApi } from '../services/api';
import { formatCurrency, formatDate } from '../utils/formatters';

const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [tradeIdFilter, setTradeIdFilter] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load transactions
  const loadTransactions = useCallback(async () => {
    try {
      const params = tradeIdFilter ? { trade_id: tradeIdFilter } : {};
      const data = await transactionsApi.list(params);
      setTransactions(data);
    } catch (error) {
      console.error('Error loading transactions:', error);
      alert('Failed to load transactions');
    }
  }, [tradeIdFilter]);

  useEffect(() => {
    loadTransactions();
  }, [loadTransactions]);

  // Handle CSV upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await transactionsApi.uploadCsv(file);
      alert(`Successfully uploaded ${file.name}`);
      loadTransactions();
    } catch (error: any) {
      console.error('Error uploading CSV:', error);
      alert(error.response?.data?.detail || 'Failed to upload CSV');
    } finally {
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Column definitions
  const columnDefs: ColDef[] = [
    { headerName: 'ID', field: 'id', width: 80 },
    {
      headerName: 'Trade ID',
      field: 'trade_id',
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
      headerName: 'Date',
      field: 'transaction_date',
      width: 120,
      valueFormatter: (params) => formatDate(params.value),
    },
    {
      headerName: 'Action',
      field: 'action',
      width: 100,
      cellRenderer: (params: any) => {
        const colors: Record<string, string> = {
          Stop1: 'bg-yellow-100 text-yellow-800',
          Stop2: 'bg-orange-100 text-orange-800',
          Stop3: 'bg-red-100 text-red-800',
          Profit: 'bg-green-100 text-green-800',
          Other: 'bg-gray-100 text-gray-800',
        };
        return (
          <span className={`px-2 py-1 rounded text-xs ${colors[params.value] || ''}`}>
            {params.value}
          </span>
        );
      },
    },
    { headerName: 'Shares', field: 'shares', width: 100 },
    {
      headerName: 'Price',
      field: 'price',
      width: 110,
      valueFormatter: (params) => formatCurrency(params.value),
    },
    {
      headerName: 'Fees',
      field: 'fees',
      width: 100,
      valueFormatter: (params) => formatCurrency(params.value),
    },
    {
      headerName: 'Proceeds',
      field: 'proceeds',
      width: 120,
      valueFormatter: (params) => formatCurrency(params.value),
    },
    {
      headerName: 'PnL',
      field: 'pnl',
      width: 120,
      valueFormatter: (params) => formatCurrency(params.value),
      cellClass: (params) =>
        params.value > 0 ? 'text-green-600 font-bold' : params.value < 0 ? 'text-red-600 font-bold' : 'font-bold',
    },
    {
      headerName: 'Notes',
      field: 'notes',
      width: 200,
      cellClass: 'text-sm',
    },
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-4">Exit Transactions</h1>

        <div className="flex gap-4 mb-4">
          <input
            type="text"
            placeholder="Filter by Trade ID"
            value={tradeIdFilter}
            onChange={(e) => setTradeIdFilter(e.target.value)}
            className="border rounded px-3 py-2 w-64"
          />

          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            + Add Transaction
          </button>

          <button
            onClick={() => fileInputRef.current?.click()}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Upload CSV
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="hidden"
          />

          <button onClick={loadTransactions} className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300">
            Refresh
          </button>
        </div>

        {/* CSV Format Help */}
        <div className="bg-blue-50 border border-blue-200 rounded p-4 text-sm">
          <p className="font-medium mb-2">CSV Format:</p>
          <code className="block bg-white p-2 rounded">
            trade_id,transaction_date,action,shares,price,fees,notes
            <br />
            AAPL-001,2024-01-20,Stop2,50,190.25,1.00,Partial exit
          </code>
        </div>
      </div>

      {/* AG Grid */}
      <div className="ag-theme-alpine" style={{ height: '600px', width: '100%' }}>
        <AgGridReact
          rowData={transactions}
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

      {/* Create Form Modal */}
      {showCreateForm && (
        <CreateTransactionModal
          onClose={() => setShowCreateForm(false)}
          onSuccess={() => {
            setShowCreateForm(false);
            loadTransactions();
          }}
        />
      )}
    </div>
  );
};

// Simple create transaction modal
const CreateTransactionModal: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<TransactionCreate>({
    trade_id: '',
    transaction_date: new Date().toISOString().split('T')[0],
    action: 'Profit',
    shares: 0,
    price: 0,
    fees: 0,
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      await transactionsApi.create(formData);
      alert('Transaction created successfully!');
      onSuccess();
    } catch (error: any) {
      console.error('Error creating transaction:', error);
      alert(error.response?.data?.detail || 'Failed to create transaction');
    } finally {
      setSubmitting(false);
    }
  };

  const actions: ActionType[] = ['Stop1', 'Stop2', 'Stop3', 'Profit', 'Other'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">Add Exit Transaction</h2>

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
            <label className="block text-sm font-medium mb-1">Transaction Date *</label>
            <input
              type="date"
              required
              value={formData.transaction_date}
              onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Action *</label>
            <select
              required
              value={formData.action}
              onChange={(e) => setFormData({ ...formData, action: e.target.value })}
              className="w-full border rounded px-3 py-2"
            >
              {actions.map((action) => (
                <option key={action} value={action}>
                  {action}
                </option>
              ))}
            </select>
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
            <label className="block text-sm font-medium mb-1">Exit Price *</label>
            <input
              type="number"
              step="0.01"
              required
              value={formData.price || ''}
              onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Fees</label>
            <input
              type="number"
              step="0.01"
              value={formData.fees || ''}
              onChange={(e) => setFormData({ ...formData, fees: parseFloat(e.target.value) || 0 })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Notes</label>
            <textarea
              value={formData.notes || ''}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full border rounded px-3 py-2"
              rows={3}
            />
          </div>

          <div className="flex gap-2 pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {submitting ? 'Creating...' : 'Create Transaction'}
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

export default TransactionsPage;
