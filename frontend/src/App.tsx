/**
 * Main App component with routing.
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import EntriesPage from './pages/EntriesPage';
import TransactionsPage from './pages/TransactionsPage';
import TradeDetailPage from './pages/TradeDetailPage';

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {/* Navigation */}
        <nav className="bg-white shadow-lg">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <h1 className="text-2xl font-bold text-blue-600">WaveRider</h1>
                <span className="text-gray-600">Trading Journal</span>
              </div>
              <div className="flex space-x-6">
                <Link
                  to="/entries"
                  className="text-gray-700 hover:text-blue-600 font-medium transition"
                >
                  Entries
                </Link>
                <Link
                  to="/transactions"
                  className="text-gray-700 hover:text-blue-600 font-medium transition"
                >
                  Transactions
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<EntriesPage />} />
          <Route path="/entries" element={<EntriesPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/trades/:tradeId" element={<TradeDetailPage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
