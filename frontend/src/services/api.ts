/**
 * API service for WaveRider Trading Journal.
 * Communicates with FastAPI backend.
 */
import axios, { AxiosInstance } from 'axios';
import {
  Trade,
  TradeCreate,
  TradeUpdate,
  Transaction,
  TransactionCreate,
  TradeSummary,
} from '../types';

// Get API URL from environment or use default
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== Trades API ====================

export const tradesApi = {
  /**
   * Create a new trade
   */
  create: async (data: TradeCreate): Promise<Trade> => {
    const response = await apiClient.post<Trade>('/trades', data);
    return response.data;
  },

  /**
   * List all trades with optional filters
   */
  list: async (params?: { status?: string; ticker?: string }): Promise<Trade[]> => {
    const response = await apiClient.get<Trade[]>('/trades', { params });
    return response.data;
  },

  /**
   * Get a single trade by ID
   */
  get: async (tradeId: string): Promise<Trade> => {
    const response = await apiClient.get<Trade>(`/trades/${tradeId}`);
    return response.data;
  },

  /**
   * Update user-editable fields on a trade
   */
  update: async (tradeId: string, data: TradeUpdate): Promise<Trade> => {
    const response = await apiClient.patch<Trade>(`/trades/${tradeId}`, data);
    return response.data;
  },

  /**
   * Refresh market data for a trade
   */
  refresh: async (tradeId: string): Promise<Trade> => {
    const response = await apiClient.post<Trade>(`/trades/${tradeId}/refresh`);
    return response.data;
  },

  /**
   * Delete a trade
   */
  delete: async (tradeId: string): Promise<void> => {
    await apiClient.delete(`/trades/${tradeId}`);
  },

  /**
   * Get summary statistics
   */
  summary: async (): Promise<TradeSummary> => {
    const response = await apiClient.get<TradeSummary>('/trades/summary');
    return response.data;
  },
};

// ==================== Transactions API ====================

export const transactionsApi = {
  /**
   * Create a new transaction
   */
  create: async (data: TransactionCreate): Promise<Transaction> => {
    const response = await apiClient.post<Transaction>('/transactions', data);
    return response.data;
  },

  /**
   * List all transactions with optional filters
   */
  list: async (params?: { trade_id?: string; action?: string }): Promise<Transaction[]> => {
    const response = await apiClient.get<Transaction[]>('/transactions', { params });
    return response.data;
  },

  /**
   * Get a single transaction by ID
   */
  get: async (transactionId: number): Promise<Transaction> => {
    const response = await apiClient.get<Transaction>(`/transactions/${transactionId}`);
    return response.data;
  },

  /**
   * Update a transaction
   */
  update: async (transactionId: number, data: Partial<TransactionCreate>): Promise<Transaction> => {
    const response = await apiClient.patch<Transaction>(`/transactions/${transactionId}`, data);
    return response.data;
  },

  /**
   * Delete a transaction
   */
  delete: async (transactionId: number): Promise<void> => {
    await apiClient.delete(`/transactions/${transactionId}`);
  },

  /**
   * Upload transactions from CSV file
   */
  uploadCsv: async (file: File): Promise<Transaction[]> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<Transaction[]>('/transactions/upload-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Export configured client for custom requests
export default apiClient;
