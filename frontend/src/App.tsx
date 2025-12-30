/**
 * Main App component with routing - Dark theme UI
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import EntriesPage from './pages/EntriesPage_New';
import TransactionsPage from './pages/TransactionsPage_New';
import SettingsPage from './pages/SettingsPage';
import TradeDetailPage from './pages/TradeDetailPage';

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-900">
        {/* Navigation */}
        <Navigation />

        {/* Routes */}
        <Routes>
          <Route path="/" element={<EntriesPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/trades/:tradeId" element={<TradeDetailPage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
