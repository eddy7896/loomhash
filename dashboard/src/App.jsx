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
      <div className="min-h-screen bg-background flex flex-col font-sans">
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto flex h-14 items-center px-4 md:px-8">
            <div className="mr-6 flex items-center space-x-2 font-bold tracking-tight">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-foreground">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="3" y1="9" x2="21" y2="9"></line>
                <line x1="9" y1="21" x2="9" y2="9"></line>
              </svg>
              <span>LoomHash</span>
            </div>
            
            <nav className="flex items-center space-x-6 text-sm font-medium">
              <NavLink to="/" className={({ isActive }) => `transition-colors hover:text-foreground/80 ${isActive ? 'text-foreground' : 'text-foreground/60'}`}>
                Overview
              </NavLink>
              <NavLink to="/keys" className={({ isActive }) => `transition-colors hover:text-foreground/80 ${isActive ? 'text-foreground' : 'text-foreground/60'}`}>
                Authentication
              </NavLink>
              <NavLink to="/users" className={({ isActive }) => `transition-colors hover:text-foreground/80 ${isActive ? 'text-foreground' : 'text-foreground/60'}`}>
                Users
              </NavLink>
              <NavLink to="/billing" className={({ isActive }) => `transition-colors hover:text-foreground/80 ${isActive ? 'text-foreground' : 'text-foreground/60'}`}>
                Billing
              </NavLink>
              <NavLink to="/settings" className={({ isActive }) => `transition-colors hover:text-foreground/80 ${isActive ? 'text-foreground' : 'text-foreground/60'}`}>
                Settings
              </NavLink>
            </nav>
            
            <div className="ml-auto flex items-center space-x-4">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 ring-2 ring-background"></div>
            </div>
          </div>
        </header>
        
        <main className="flex-1 container mx-auto px-4 md:px-8 py-8">
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
