// frontend/src/App.tsx

import React, { useState, useEffect } from 'react';
import LandingPage from './components/LandingPage';
import Navbar from './components/Navbar';
import GetStarted from './components/GetStarted';
import Login from './components/Login';
import ForgotPassword from './components/ForgotPassword';
import Dashboard from './components/Dashboard';
import { authService, User } from './services/authService';

type ViewType = 'landing' | 'get-started' | 'login' | 'forgot-password' | 'dashboard'; // ✅ Removed 'interview'

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('landing');
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadSession = async () => {
      try {
        console.log('🔄 Loading session...');
        const session = await authService.getSession();
        
        if (session && session.user) {
          console.log('✅ User found:', session.user);
          setUser(session.user);
          setCurrentView('dashboard');
        } else {
          console.log('❌ No valid session, showing landing page');
          setCurrentView('landing');
        }
      } catch (error: any) {
        console.error('❌ Session load error:', error);
        authService.logout();
        setCurrentView('landing');
      } finally {
        setLoading(false);
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
    
    if (currentView !== 'dashboard') { // ✅ Removed interview check
      window.scrollTo(0, 0);
    }
  }, [currentView]);

  const handleAuthSuccess = async (userData: User) => {
    try {
      console.log('✅ Auth success, user data:', userData);
      setUser(userData);
      setCurrentView('dashboard');
    } catch (error: any) {
      console.error('❌ Auth success handler error:', error);
    }
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setCurrentView('landing');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a1612] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white/60">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {currentView !== 'dashboard' && ( // ✅ Simplified check
        <Navbar
          onGetStarted={() => setCurrentView('get-started')}
          onLogin={() => setCurrentView('login')}
          onHome={() => setCurrentView('landing')}
        />
      )}

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
        <Dashboard
          user={user}
          onLogout={handleLogout}
        />
      )}
    </div>
  );
};

export default App;
