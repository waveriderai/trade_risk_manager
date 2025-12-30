/**
 * Navigation Component - Dark theme navigation bar
 */
import React from 'react';
import { useLocation, Link } from 'react-router-dom';

const Navigation: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="max-w-[1800px] mx-auto px-6">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center py-4">
            <span className="text-xl font-bold">
              <span className="text-blue-400">3-Stop</span>{' '}
              <span className="text-white">Trading Journal</span>
            </span>
          </Link>

          <div className="flex gap-1">
            <NavLink to="/" active={isActive('/')}>
              Entries
            </NavLink>
            <NavLink to="/transactions" active={isActive('/transactions')}>
              Transactions
            </NavLink>
            <NavLink to="/settings" active={isActive('/settings')}>
              Settings
            </NavLink>
          </div>
        </div>
      </div>
    </nav>
  );
};

const NavLink: React.FC<{
  to: string;
  active: boolean;
  children: React.ReactNode;
}> = ({ to, active, children }) => {
  return (
    <Link
      to={to}
      className={`px-4 py-4 text-sm font-medium transition ${
        active
          ? 'text-blue-400 border-b-2 border-blue-400'
          : 'text-gray-400 hover:text-gray-200'
      }`}
    >
      {children}
    </Link>
  );
};

export default Navigation;
