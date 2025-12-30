/**
 * Formatting utilities for display.
 */

/**
 * Format number as currency (USD)
 */
export const formatCurrency = (value?: number | null): string => {
  if (value === null || value === undefined) return '-';
  const num = typeof value === 'number' ? value : parseFloat(String(value));
  if (isNaN(num)) return '-';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
};

/**
 * Format number as percentage
 */
export const formatPercent = (value?: number | null, decimals: number = 2): string => {
  if (value === null || value === undefined) return '-';
  const num = typeof value === 'number' ? value : parseFloat(String(value));
  if (isNaN(num)) return '-';
  return `${num.toFixed(decimals)}%`;
};

/**
 * Format number with specified decimal places
 */
export const formatNumber = (value?: number | null, decimals: number = 2): string => {
  if (value === null || value === undefined) return '-';
  const num = typeof value === 'number' ? value : parseFloat(String(value));
  if (isNaN(num)) return '-';
  return num.toFixed(decimals);
};

/**
 * Format R-multiple
 */
export const formatRMultiple = (value?: number | null): string => {
  if (value === null || value === undefined) return '-';
  const num = typeof value === 'number' ? value : parseFloat(String(value));
  if (isNaN(num)) return '-';
  return `${num > 0 ? '+' : ''}${num.toFixed(2)}R`;
};

/**
 * Format date string
 */
export const formatDate = (dateString?: string | null): string => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

/**
 * Format datetime string
 */
export const formatDateTime = (dateString?: string | null): string => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Get color class for PnL values
 */
export const getPnLColorClass = (value?: number | null): string => {
  if (value === null || value === undefined) return '';
  if (value > 0) return 'text-green-600';
  if (value < 0) return 'text-red-600';
  return 'text-gray-600';
};

/**
 * Get status badge color
 */
export const getStatusColor = (status?: string): string => {
  switch (status) {
    case 'OPEN':
      return 'bg-blue-100 text-blue-800';
    case 'PARTIAL':
      return 'bg-yellow-100 text-yellow-800';
    case 'CLOSED':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-600';
  }
};
