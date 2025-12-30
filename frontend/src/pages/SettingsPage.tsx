/**
 * Settings Page - Configure portfolio settings
 */
import React, { useState, useEffect } from 'react';

const SettingsPage: React.FC = () => {
  const [portfolioSize, setPortfolioSize] = useState('300000');
  const [bufferPct, setBufferPct] = useState('0.50');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    // Simulate save
    await new Promise((resolve) => setTimeout(resolve, 500));
    setSaving(false);
    alert('Settings saved successfully!');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-[1800px] mx-auto">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">Settings</h1>
            <p className="text-sm text-gray-400">
              Configure default values for new trades
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-6 py-6">
        <div className="max-w-2xl">
          {/* Settings Form */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Default Portfolio Size ($)
                </label>
                <input
                  type="number"
                  value={portfolioSize}
                  onChange={(e) => setPortfolioSize(e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Used for calculating portfolio percentage metrics on new trades
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Default Buffer % for Stop3
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    step="0.01"
                    value={bufferPct}
                    onChange={(e) => setBufferPct(e.target.value)}
                    className="flex-1 bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-gray-400">%</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Stop3 = Low of Day - (Low of Day × Buffer %)
                </p>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-700">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </div>

          {/* 3-Stop System Explanation */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-lg font-bold text-white mb-4">About the 3-Stop System</h2>
            
            <div className="space-y-4 text-sm text-gray-300">
              <p>
                The 3-Stop system uses three progressive stop levels based on the Low of Day (LoD) 
                from your entry day:
              </p>

              <div className="space-y-2">
                <div className="flex items-start gap-3">
                  <div className="bg-red-600 text-white px-2 py-1 rounded text-xs font-medium mt-0.5">
                    Stop 1
                  </div>
                  <div>
                    <p className="font-medium text-white">1/3 of the way from Entry to Stop3</p>
                    <p className="text-xs text-gray-400">First warning level. Consider reducing position.</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="bg-orange-600 text-white px-2 py-1 rounded text-xs font-medium mt-0.5">
                    Stop 2
                  </div>
                  <div>
                    <p className="font-medium text-white">2/3 of the way from Entry to Stop3</p>
                    <p className="text-xs text-gray-400">Second warning. Strongly consider reducing position size.</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="bg-yellow-600 text-white px-2 py-1 rounded text-xs font-medium mt-0.5">
                    Stop 3
                  </div>
                  <div>
                    <p className="font-medium text-white">Full stop level at LoD minus buffer</p>
                    <p className="text-xs text-gray-400">Exit remaining position to preserve capital.</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-900 rounded p-4 mt-4">
                <p className="text-xs text-gray-400 mb-2">
                  <strong className="text-white">1R</strong> (Risk) = Entry Price - Stop3
                </p>
                <p className="text-xs text-gray-400">
                  This represents your maximum risk per share and is used to calculate R-multiples 
                  for risk-adjusted performance measurement.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default SettingsPage;
