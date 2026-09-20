import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import Overview from './pages/Overview';
import Keys from './pages/Keys';
import Users from './pages/Users';
import Billing from './pages/Billing';
import Settings from './pages/Settings';
import { LayoutDashboard, Key, Users as UsersIcon, CreditCard, Settings as SettingsIcon, Search, ChevronRight, Activity, Shield } from 'lucide-react';

function TopHeader() {
  const location = useLocation();
  const getPageName = () => {
    switch (location.pathname) {
      case '/': return 'Overview';
      case '/keys': return 'Authentication';
      case '/users': return 'Users';
      case '/billing': return 'Billing';
      case '/settings': return 'Settings';
      default: return '';
    }
  };

  return (
    <header className="h-14 border-b border-white/10 flex items-center px-6 bg-black sticky top-0 z-10">
      <div className="text-sm font-medium flex items-center text-white/90">
        <span className="opacity-60">LoomHash</span> 
        <span className="text-white/40 mx-2">/</span> 
        <span>{getPageName()}</span>
      </div>
    </header>
  );
}

function App() {
  const navItems = [
    { to: "/", icon: LayoutDashboard, label: "Overview" },
    { to: "/keys", icon: Key, label: "Authentication" },
    { to: "/users", icon: UsersIcon, label: "Users" },
    { to: "/billing", icon: CreditCard, label: "Billing" },
    { to: "/settings", icon: SettingsIcon, label: "Settings" }
  ];

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-black text-white flex font-sans selection:bg-white/30">
        
        {/* Sidebar */}
        <aside className="w-[240px] border-r border-white/10 flex flex-col h-screen sticky top-0 bg-[#0a0a0a] shrink-0">
          
          {/* User / Team switcher */}
          <div className="p-4 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-500 to-orange-700 shadow-inner"></div>
            <div className="flex flex-col overflow-hidden">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium truncate">LoomHash Admin</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white/40 shrink-0"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </div>
              <span className="text-[11px] font-medium text-white/60 bg-white/10 rounded px-1.5 py-0.5 mt-1 w-fit border border-white/5">Hobby</span>
            </div>
          </div>
          
          {/* Search */}
          <div className="px-3 pb-3">
            <div className="relative group">
              <Search className="absolute left-2.5 top-2 h-4 w-4 text-white/40 group-focus-within:text-white/70 transition-colors" />
              <input 
                className="w-full bg-white/5 border border-white/10 rounded-md pl-9 pr-8 py-1.5 text-sm text-white/90 placeholder:text-white/40 focus:outline-none focus:border-white/20 focus:ring-1 focus:ring-white/20 transition-all"
                placeholder="Find"
              />
              <div className="absolute right-2 top-2 text-[10px] font-medium text-white/40 border border-white/10 rounded px-1.5 bg-white/5">F</div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5 custom-scrollbar">
            {navItems.map((item) => (
              <NavLink 
                key={item.to} 
                to={item.to} 
                className={({ isActive }) => 
                  `flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-all ${
                    isActive 
                      ? 'bg-white/10 text-white font-medium' 
                      : 'text-white/60 hover:text-white/90 hover:bg-white/5'
                  }`
                }
              >
                <item.icon className="w-4 h-4 shrink-0" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-h-screen bg-black overflow-hidden relative">
          <TopHeader />
          <main className="flex-1 p-6 md:p-8 lg:p-10 w-full mx-auto max-w-6xl overflow-y-auto">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/keys" element={<Keys />} />
              <Route path="/users" element={<Users />} />
              <Route path="/billing" element={<Billing />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
