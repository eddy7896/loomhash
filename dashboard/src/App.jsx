import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Overview from './pages/Overview';
import Keys from './pages/Keys';
import Users from './pages/Users';
import Billing from './pages/Billing';
import Settings from './pages/Settings';
import { LayoutDashboard, Key, Users as UsersIcon, CreditCard, Settings as SettingsIcon } from 'lucide-react';

function App() {
  return (
    <BrowserRouter>
      <div className="dashboard-layout">
        <header className="header">
          <div className="header-brand">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="3" y1="9" x2="21" y2="9"></line>
              <line x1="9" y1="21" x2="9" y2="9"></line>
            </svg>
            LoomHash
          </div>
          <nav className="nav-links">
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Overview
            </NavLink>
            <NavLink to="/keys" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Authentication
            </NavLink>
            <NavLink to="/users" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Users
            </NavLink>
            <NavLink to="/billing" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Billing
            </NavLink>
            <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Settings
            </NavLink>
          </nav>
        </header>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/keys" element={<Keys />} />
            <Route path="/users" element={<Users />} />
            <Route path="/billing" element={<Billing />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
