// frontend/src/components/Dashboard.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../services/authService';
import { 
  Home, Map, Briefcase, FileText, BookOpen, 
  Video, BarChart3, UserCircle, LogOut, 
  Menu, X, Sparkles, Target, Zap
} from 'lucide-react';

// Import dashboard modules (REMOVED InterviewModule)
import DashboardHome from './Dashboard/DashboardHome';
import RoadmapModule from './Dashboard/RoadmapModule';
import OpportunitiesModule from './Dashboard/OpportunitiesModule';
import ResumeModule from './Dashboard/ResumeModule';
import JournalModule from './Dashboard/JournalModule';
import SummaryModule from './Dashboard/SummaryModule';
import ProfileModule from './Dashboard/ProfileModule';

interface DashboardProps {
  user: User;
  onLogout: () => void;
  onNavigateToInterview: () => void;
}

// REMOVED 'interview' from ModuleName type
type ModuleName = 'home' | 'roadmap' | 'opportunities' | 'resume' | 'journal' | 'summary' | 'profile';

const Dashboard: React.FC<DashboardProps> = ({ user, onLogout, onNavigateToInterview }) => {
  const [activeModule, setActiveModule] = useState<ModuleName>('home');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [agentStatus, setAgentStatus] = useState({
    supervisor: 'active',
    roadmap: 'idle',
    opportunities: 'scanning',
    resume: 'idle',
    journal: 'idle',
    interview: 'idle',
    summary: 'idle'
  });

  const modules = [
    { id: 'home', name: 'Home', icon: Home, description: 'Your personalized dashboard' },
    { id: 'roadmap', name: 'Roadmap', icon: Map, description: 'Career planning & goals', agent: 'Roadmap Generator' },
    { id: 'opportunities', name: 'Opportunities', icon: Briefcase, description: 'Jobs & internships', agent: 'Opportunities Scanner' },
    { id: 'resume', name: 'Resume', icon: FileText, description: 'Resume intelligence', agent: 'Resume Optimizer' },
    { id: 'journal', name: 'Journal', icon: BookOpen, description: 'Daily reflections', agent: 'Career Coach' },
    // UPDATED: Interview now navigates externally
    { id: 'interview', name: 'Interview', icon: Video, description: 'AI Mock Interviews', agent: 'Interview Trainer', isExternal: true },
    { id: 'summary', name: 'Progress', icon: BarChart3, description: 'Weekly insights', agent: 'Progress Tracker' },
    { id: 'profile', name: 'Profile', icon: UserCircle, description: 'Manage account', agent: 'Profile Manager' },
  ];

  useEffect(() => {
    // Get token from localStorage
    const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
    
    if (!token) {
      console.warn('No authentication token found. WebSocket will not connect.');
      return;
    }

    // Correct WebSocket URL with authentication
    const wsUrl = `ws://localhost:8000/api/agents/ws?token=${encodeURIComponent(token)}`;
    console.log('🔌 Connecting WebSocket to:', wsUrl);

    let ws: WebSocket;
    
    try {
      ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        ws.send(JSON.stringify({ type: 'ping' }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Received:', data);
          
          if (data.type === 'agent_status') {
            setAgentStatus(prev => ({ ...prev, [data.agent]: data.status }));
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };

      ws.onclose = (event) => {
        console.log(`🔌 WebSocket closed: Code ${event.code}, Reason: ${event.reason || 'Unknown'}`);
      };

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  // UPDATED: Handle module navigation
  const handleModuleClick = (moduleId: string, isExternal?: boolean) => {
    if (moduleId === 'interview' && isExternal) {
      // Navigate to external Interview page
      onNavigateToInterview();
    } else {
      // Normal module switching
      setActiveModule(moduleId as ModuleName);
    }
  };

  // UPDATED: Removed interview case
  const renderModule = () => {
    switch (activeModule) {
      case 'home':
        return <DashboardHome user={user} onNavigateToInterview={onNavigateToInterview} />;
      case 'roadmap':
        return <RoadmapModule user={user} />;
      case 'opportunities':
        return <OpportunitiesModule user={user} />;
      case 'resume':
        return <ResumeModule user={user} />;
      case 'journal':
        return <JournalModule user={user} />;
      // REMOVED: case 'interview'
      case 'summary':
        return <SummaryModule user={user} />;
      case 'profile':
        return <ProfileModule user={user} />;
      default:
        return <DashboardHome user={user} onNavigateToInterview={onNavigateToInterview} />;
    }
  };

  const getAgentStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'scanning': return 'bg-blue-500 animate-pulse';
      case 'thinking': return 'bg-yellow-500 animate-pulse';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-[#0f231e] via-[#1a2f2a] to-[#0f231e] text-white overflow-hidden">
      
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-20'} bg-white/5 backdrop-blur-xl border-r border-white/10 transition-all duration-300 flex flex-col`}>
        
        {/* Header */}
        <div className="p-6 border-b border-white/10 flex items-center justify-between">
          {sidebarOpen && (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
                <Sparkles size={20} className="text-primary" />
              </div>
              <div>
                <h2 className="font-bold text-lg tracking-tight">CareerAI</h2>
                <p className="text-xs text-white/40">Agentic Platform</p>
              </div>
            </div>
          )}
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)} 
            className="p-2 hover:bg-white/10 rounded-xl transition-all"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* User Info */}
        {sidebarOpen && (
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-lg">
                {(user.fullName || user.email || 'U').charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 overflow-hidden">
                <h3 className="font-medium truncate">{user.fullName || user.email || 'User'}</h3>
                <p className="text-xs text-white/40 truncate">{user.email || ''}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <Target size={14} className="text-primary" />
              <span className="text-white/60">{user.targetRole || 'Not set'}</span>
            </div>
          </div>
        )}

        {/* Navigation - UPDATED */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {modules.map((module) => (
            <button
              key={module.id}
              onClick={() => handleModuleClick(module.id, module.isExternal)}
              className={`w-full ${sidebarOpen ? 'p-4' : 'p-3'} rounded-2xl transition-all flex items-center gap-4 group ${
                activeModule === module.id && !module.isExternal
                  ? 'bg-primary/20 text-primary border border-primary/30' 
                  : 'hover:bg-white/5 text-white/60 hover:text-white'
              }`}
            >
              <module.icon size={22} />
              {sidebarOpen && (
                <div className="flex-1 text-left">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm">{module.name}</span>
                    {module.agent && (
                      <div className={`w-2 h-2 rounded-full ${getAgentStatusColor(agentStatus[module.id as keyof typeof agentStatus] || 'idle')}`} />
                    )}
                  </div>
                  <p className="text-xs text-white/40 mt-0.5">{module.description}</p>
                </div>
              )}
            </button>
          ))}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-white/10">
          <button
            onClick={onLogout}
            className={`w-full ${sidebarOpen ? 'p-4' : 'p-3'} rounded-2xl bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-all flex items-center gap-4`}
          >
            <LogOut size={22} />
            {sidebarOpen && <span className="font-medium">Logout</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        
        {/* Top Bar */}
        <div className="h-20 bg-white/5 backdrop-blur-xl border-b border-white/10 flex items-center justify-between px-8">
          <div>
            <h1 className="text-2xl font-light tracking-tight">
              {modules.find(m => m.id === activeModule)?.name}
            </h1>
            <p className="text-sm text-white/40">
              {modules.find(m => m.id === activeModule)?.description}
            </p>
          </div>
          
          {/* Agent Status Indicator */}
          <div className="flex items-center gap-3 px-4 py-2 bg-white/5 rounded-full border border-white/10">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-primary" />
              <span className="text-xs font-medium">Supervisor Active</span>
            </div>
            <div className={`w-2 h-2 rounded-full ${getAgentStatusColor(agentStatus.supervisor)}`} />
          </div>
        </div>

        {/* Module Content */}
        <div className="flex-1 overflow-auto p-8">
          {renderModule()}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
