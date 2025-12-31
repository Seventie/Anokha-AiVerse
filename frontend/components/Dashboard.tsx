// frontend/src/components/Dashboard.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../services/authService';
import { 
  Home, Map, Briefcase, FileText, BookOpen, 
  Video, BarChart3, UserCircle, LogOut, 
  Menu, X, Sparkles
} from 'lucide-react';

// Import dashboard modules
import DashboardHome from './Dashboard/DashboardHome';
import RoadmapModule from './Dashboard/RoadmapModule';
import OpportunitiesModule from './Dashboard/OpportunitiesModule';
import ResumeModule from './Dashboard/ResumeModule';
import JournalModule from './Dashboard/JournalModule';
import SummaryModule from './Dashboard/SummaryModule';
import ProfileModule from './Dashboard/ProfileModule';
import ColdEmailModule from './Dashboard/ColdEmailModule';
import InterviewModule from './Dashboard/InterviewModule'; // ✅ Changed from Interview/InterviewPage

interface DashboardProps {
  user: User;
  onLogout: () => void;
  onNavigateToInterview?: () => void; // ✅ Make optional since we don't need it anymore
}

// ✅ Add 'interview' to the type
type ModuleName = 'home' | 'roadmap' | 'opportunities' | 'resume' | 'journal' | 'coldEmail' | 'interview' | 'summary' | 'profile';

const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  const [activeModule, setActiveModule] = useState<ModuleName>('home');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  console.log('🏠 Dashboard rendering with user:', user?.email);

  const modules = [
    { id: 'home', name: 'Home', icon: Home, description: 'Your personalized dashboard' },
    { id: 'roadmap', name: 'Roadmap', icon: Map, description: 'Career planning & goals' },
    { id: 'opportunities', name: 'Opportunities', icon: Briefcase, description: 'Jobs & internships' },
    { id: 'resume', name: 'Resume', icon: FileText, description: 'Resume intelligence' },
    { id: 'journal', name: 'Journal', icon: BookOpen, description: 'Daily reflections' },
    { id: 'interview', name: 'Interview', icon: Video, description: 'AI Mock Interviews' }, // ✅ Removed isExternal
    { id: 'coldEmail', name: 'Cold Email', icon: Briefcase, description: 'AI outreach campaigns' },
    { id: 'summary', name: 'Progress', icon: BarChart3, description: 'Weekly insights' },
    { id: 'profile', name: 'Profile', icon: UserCircle, description: 'Manage account' },
  ];

  const handleModuleClick = (moduleId: string) => {
    setActiveModule(moduleId as ModuleName); // ✅ Simplified - no external check
  };

  const renderModule = () => {
    console.log('📄 Rendering module:', activeModule);
    
    try {
      switch (activeModule) {
        case 'home':
          return <DashboardHome user={user} />;
        case 'roadmap':
          return <RoadmapModule user={user} />;
        case 'opportunities':
          return <OpportunitiesModule user={user} />;
        case 'resume':
          return <ResumeModule user={user} />;
        case 'journal':
          return <JournalModule user={user} />;
        case 'interview': // ✅ Renders inside dashboard now
          return <InterviewModule user={user} />;
        case 'coldEmail':
          return <ColdEmailModule user={user} />;
        case 'summary':
          return <SummaryModule user={user} />;
        case 'profile':
          return <ProfileModule user={user} />;
        default:
          return <DashboardHome user={user} />;
      }
    } catch (error) {
      console.error('❌ Module rendering error:', error);
      return (
        <div className="p-8">
          <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6">
            <h3 className="text-xl font-bold text-red-400 mb-2">Module Error</h3>
            <p className="text-white/80">Failed to load {activeModule} module</p>
          </div>
        </div>
      );
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-[#0f231e] via-[#1a2f2a] to-[#0f231e] text-white overflow-hidden">
      
      {/* Sidebar */}
      <aside 
        className={`${
          sidebarOpen ? 'w-72' : 'w-20'
        } bg-black/20 backdrop-blur-xl border-r border-white/10 transition-all duration-300 flex flex-col`}
      >
        {/* Header */}
        <div className="p-6 border-b border-white/10 flex items-center justify-between">
          {sidebarOpen && (
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Sparkles className="text-primary" size={24} />
                CareerAI
              </h2>
              <p className="text-xs text-white/40 mt-1">AI-Powered Career Growth</p>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-white/10 rounded-xl transition-colors"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* User Info */}
        {sidebarOpen && (
          <div className="p-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="text-primary font-bold">
                  {user.fullName?.charAt(0) || user.username?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{user.fullName || user.username}</p>
                <p className="text-xs text-white/40 truncate">{user.email}</p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto">
          <div className="space-y-2">
            {modules.map((module) => {
              const Icon = module.icon;
              const isActive = activeModule === module.id;
              
              return (
                <button
                  key={module.id}
                  onClick={() => handleModuleClick(module.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl transition-all ${
                    isActive 
                      ? 'bg-primary/20 text-primary border border-primary/30' 
                      : 'hover:bg-white/5 text-white/70 hover:text-white'
                  }`}
                >
                  <Icon size={20} />
                  {sidebarOpen && (
                    <div className="flex-1 text-left">
                      <p className="font-medium">{module.name}</p>
                      <p className="text-xs opacity-60">{module.description}</p>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-white/10">
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl hover:bg-red-500/10 
                     text-red-400 transition-all"
          >
            <LogOut size={20} />
            {sidebarOpen && <span className="font-medium">Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          {renderModule()}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
