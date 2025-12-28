
import React, { useState, useEffect } from 'react';
import LandingPage from './components/LandingPage';
import Navbar from './components/Navbar';
import GetStarted from './components/GetStarted';
import Login from './components/Login';
import ForgotPassword from './components/ForgotPassword';
import Dashboard from './components/Dashboard';
import { authService, User } from './services/authService';

type ViewType = 'landing' | 'get-started' | 'login' | 'forgot-password' | 'dashboard';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('landing');
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const loadSession = async () => {
      const session = await authService.getSession();
      if (session) {
        setUser(session);
        setCurrentView('dashboard');
      }
    };
    loadSession();
  }, []);

  useEffect(() => {
    // @ts-ignore
    const ScrollTrigger = window.ScrollTrigger;
    if (ScrollTrigger) {
      ScrollTrigger.refresh();
    }
    if (currentView !== 'dashboard') {
      window.scrollTo(0, 0);
    }
  }, [currentView]);

  const handleAuthSuccess = (userData: User) => {
    setUser(userData);
    setCurrentView('dashboard');
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setCurrentView('landing');
  };

  return (
    <div className="relative w-full min-h-screen">
      {currentView !== 'dashboard' && (
        <Navbar 
          onGetStarted={() => setCurrentView('get-started')} 
          onLogin={() => setCurrentView('login')}
          onHome={() => setCurrentView('landing')}
        />
      )}
      
      <main className="relative z-10 w-full">
        {currentView === 'landing' && (
          <LandingPage 
            onGetStarted={() => setCurrentView('get-started')} 
            onLogin={() => setCurrentView('login')}
          />
        )}
        {currentView === 'get-started' && (
          <GetStarted 
            onLogin={() => setCurrentView('login')} 
            onSuccess={handleAuthSuccess}
          />
        )}
        {currentView === 'login' && (
          <Login 
            onForgotPassword={() => setCurrentView('forgot-password')} 
            onSignUp={() => setCurrentView('get-started')}
            onDashboard={handleAuthSuccess}
          />
        )}
        {currentView === 'forgot-password' && (
          <ForgotPassword onBackToLogin={() => setCurrentView('login')} />
        )}
        {currentView === 'dashboard' && user && (
          <Dashboard user={user} onLogout={handleLogout} />
        )}
      </main>
    </div>
  );
};

export default App;
