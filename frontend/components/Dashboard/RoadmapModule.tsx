// frontend/src/components/Dashboard/RoadmapModule.tsx

import React, { useState, useEffect } from 'react';
import { 
  roadmapService, 
  GenerateRoadmapRequest, 
  CurrentRoadmapResponse,
  formatTimelineText,
  calculateDaysRemaining
} from '../../services/roadmapService';
import { apiService } from '../../services/apiService';
import RoadmapVisualization from '../roadmap/RoadmapVisualization';
import SkillGapAnalysis from '../roadmap/SkillGapAnalysis';
import LearningResources from '../roadmap/LearningResources';
import { 
  Loader2, Target, Calendar, TrendingUp, CheckCircle2, 
  Circle, Clock, Trash2, RefreshCw, AlertCircle, 
  Sparkles, Zap, Brain, BookOpen, Award, Bell, Send,
  Link, CheckCircle, XCircle
} from 'lucide-react';

const RoadmapModule: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [scheduling, setScheduling] = useState(false);
  const [roadmapData, setRoadmapData] = useState<CurrentRoadmapResponse | null>(null);
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Google OAuth state
  const [googleConnected, setGoogleConnected] = useState(false);
  const [checkingGoogle, setCheckingGoogle] = useState(true);
  
  // Form state
  const [targetRole, setTargetRole] = useState('Full Stack Developer');
  const [timelineWeeks, setTimelineWeeks] = useState(12);

  useEffect(() => {
    fetchCurrentRoadmap();
    checkGoogleStatus();
    
    // Check URL params for Google OAuth callback
    const params = new URLSearchParams(window.location.search);
    if (params.get('google_connected') === 'true') {
      setSuccessMessage('✅ Google Calendar & Gmail connected! You can now schedule tasks and receive weekly summaries.');
      setGoogleConnected(true);
      checkGoogleStatus(); // Refresh status
      window.history.replaceState({}, '', '/dashboard');
    } else if (params.get('google_error')) {
      setError('❌ Google connection failed: ' + params.get('google_error'));
      window.history.replaceState({}, '', '/dashboard');
    }
  }, []);

  const checkGoogleStatus = async () => {
    setCheckingGoogle(true);
    try {
      const token = apiService.getToken();
      if (!token) {
        setCheckingGoogle(false);
        return;
      }

      const response = await fetch('http://localhost:8000/api/auth/google/status', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setGoogleConnected(data.connected || false);
        
        // Store in localStorage for persistence
        if (data.connected) {
          localStorage.setItem('google_connected', 'true');
        } else {
          localStorage.removeItem('google_connected');
        }
      }
    } catch (error) {
      console.error('Failed to check Google status:', error);
    } finally {
      setCheckingGoogle(false);
    }
  };

  const handleConnectGoogle = async () => {
    try {
      const token = apiService.getToken();
      if (!token) {
        setError('⚠️ Please login first');
        return;
      }

      setCheckingGoogle(true);

      const response = await fetch('http://localhost:8000/api/auth/google/connect', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.auth_url) {
          // Save current location
          localStorage.setItem('pre_oauth_url', window.location.pathname);
          
          // Redirect to Google OAuth
          window.location.href = data.auth_url;
        } else {
          setError('❌ Failed to get authorization URL');
        }
      } else {
        const errorData = await response.json();
        setError(`❌ Connection failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error: any) {
      console.error('Failed to connect Google:', error);
      setError('❌ Failed to connect Google Calendar. Please try again.');
    } finally {
      setCheckingGoogle(false);
    }
  };

  const handleDisconnectGoogle = async () => {
    if (!confirm('⚠️ Disconnect Google?\n\nYou will lose:\n• Calendar sync\n• Weekly email summaries\n• Auto-scheduling')) return;
    
    try {
      const token = apiService.getToken();
      const response = await fetch('http://localhost:8000/api/auth/google/disconnect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setGoogleConnected(false);
        localStorage.removeItem('google_connected');
        setSuccessMessage('✅ Google Calendar disconnected');
      } else {
        setError('❌ Failed to disconnect');
      }
    } catch (error) {
      console.error('Disconnect error:', error);
      setError('❌ Failed to disconnect Google');
    }
  };

  const fetchCurrentRoadmap = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await roadmapService.getCurrentRoadmap();
      
      if (response.error) {
        setError(response.error);
        setShowGenerateForm(true);
        return;
      }
      
      if (response.data) {
        setRoadmapData(response.data);
        
        if (!response.data.has_roadmap) {
          setShowGenerateForm(true);
        }
      }
    } catch (error: any) {
      console.error('Failed to fetch roadmap:', error);
      setError('Failed to load roadmap');
      setShowGenerateForm(true);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateRoadmap = async () => {
    if (!targetRole.trim()) {
      setError('⚠️ Please enter a target role');
      return;
    }

    if (timelineWeeks < 4 || timelineWeeks > 52) {
      setError('⚠️ Timeline must be between 4 and 52 weeks');
      return;
    }

    setGenerating(true);
    setError(null);
    try {
      const request: GenerateRoadmapRequest = {
        target_role: targetRole,
        timeline_weeks: timelineWeeks
      };

      const response = await roadmapService.generateRoadmap(request);
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      setSuccessMessage('✅ ' + (response.data?.message || 'Roadmap generated successfully!'));
      await fetchCurrentRoadmap();
      setShowGenerateForm(false);
      
    } catch (error: any) {
      console.error('Failed to generate roadmap:', error);
      setError('❌ Failed to generate roadmap. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const handleScheduleNext7Days = async () => {
    if (!googleConnected) {
      setError('⚠️ Please connect Google Calendar first to schedule tasks');
      return;
    }

    setScheduling(true);
    setError(null);
    
    try {
      console.log('📅 Starting schedule process...');
      const response = await roadmapService.scheduleNext7Days();
      
      console.log('✅ Response:', response);
      
      if (response.error) {
        setError('❌ ' + response.error);
        return;
      }
      
      if (response.data) {
        const { scheduled_days, tasks_scheduled, calendar_events_created } = response.data;
        
        setSuccessMessage(
          `✅ Successfully scheduled ${tasks_scheduled} tasks across ${scheduled_days} days! ` +
          `Created ${calendar_events_created} calendar events. Check your Google Calendar! 🗓️`
        );
        
        await fetchCurrentRoadmap();
        
        // Optional: Show detailed notification
        setTimeout(() => {
          if (response.data.notifications && response.data.notifications.length > 0) {
            console.log('📢 Notifications:', response.data.notifications);
          }
        }, 1000);
      }
      
    } catch (error: any) {
      console.error('❌ Failed to schedule:', error);
      setError(`❌ ${error.message || 'Failed to schedule calendar events. Please try again.'}`);
    } finally {
      setScheduling(false);
    }
  };

  const handleCheckProgress = async () => {
    try {
      const response = await roadmapService.checkDailyProgress();
      if (response.data) {
        setSuccessMessage('✅ ' + response.data.message);
        await fetchCurrentRoadmap();
      }
    } catch (error) {
      console.error('Failed to check progress:', error);
    }
  };

  const handleDeleteRoadmap = async () => {
    if (!roadmapData?.roadmap?.id) return;
    
    if (!confirm('⚠️ Delete this roadmap?\n\nThis will:\n• Delete all tasks\n• Remove calendar events\n• Clear progress\n\nThis cannot be undone!')) return;

    try {
      const response = await roadmapService.deleteRoadmap(roadmapData.roadmap.id);
      
      if (response.error) {
        setError('❌ ' + response.error);
        return;
      }
      
      setRoadmapData(null);
      setShowGenerateForm(true);
      setSuccessMessage('✅ Roadmap deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete roadmap:', error);
      setError('❌ Failed to delete roadmap');
    }
  };

  const handleTaskUpdate = async (taskId: string, status: string) => {
    try {
      const response = await roadmapService.updateTask(taskId, { 
        status: status as 'not_started' | 'in_progress' | 'completed' | 'skipped'
      });
      
      if (response.error) {
        setError('❌ ' + response.error);
        return;
      }
      
      await fetchCurrentRoadmap();
      
      // Auto-check progress if task completed
      if (status === 'completed') {
        setSuccessMessage('✅ Task completed! Great progress!');
        await handleCheckProgress();
      }
    } catch (error) {
      console.error('Failed to update task:', error);
      setError('❌ Failed to update task');
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <Loader2 size={48} className="animate-spin text-primary" />
        <p className="text-white/60">Loading your roadmap...</p>
      </div>
    );
  }

  // No roadmap - show generate form
  if (showGenerateForm || !roadmapData?.has_roadmap) {
    return (
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-light mb-2">Create Learning Roadmap</h2>
            <p className="text-white/60">
              AI-powered personalized path based on your skills
            </p>
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-[2rem] p-4 flex items-start gap-3 animate-in fade-in">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-red-400 font-medium">Error</p>
              <p className="text-red-300/80 text-sm">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300 transition-colors">
              ✕
            </button>
          </div>
        )}

        {successMessage && (
          <div className="bg-green-500/10 border border-green-500/30 rounded-[2rem] p-4 flex items-start gap-3 animate-in fade-in">
            <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-green-400 font-medium">Success</p>
              <p className="text-green-300/80 text-sm">{successMessage}</p>
            </div>
            <button onClick={() => setSuccessMessage(null)} className="text-green-400 hover:text-green-300 transition-colors">
              ✕
            </button>
          </div>
        )}

        {/* Split Layout: Form Left, Preview Right */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* LEFT: Generation Form */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-8">
            <div className="mb-6">
              <Target size={40} className="text-primary mb-4" />
              <h3 className="text-2xl font-light mb-2">Set Your Goal</h3>
              <p className="text-white/60 text-sm">
                Tell us what role you're aiming for and we'll create your path
              </p>
            </div>

            <div className="space-y-6">
              {/* Target Role */}
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Target Role *
                </label>
                <input
                  type="text"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  placeholder="e.g., Full Stack Developer, Data Scientist"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl 
                           text-white placeholder-white/40 focus:outline-none focus:border-primary/50 
                           transition-all"
                />
                <p className="text-xs text-white/40 mt-2">
                  💡 Be specific: "Senior Backend Engineer" instead of just "Developer"
                </p>
              </div>

              {/* Timeline */}
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Timeline: {timelineWeeks} weeks
                </label>
                <input
                  type="range"
                  value={timelineWeeks}
                  onChange={(e) => setTimelineWeeks(parseInt(e.target.value))}
                  min={4}
                  max={52}
                  step={2}
                  className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer
                           [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 
                           [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full 
                           [&::-webkit-slider-thumb]:bg-primary"
                />
                <div className="flex justify-between text-xs text-white/40 mt-2">
                  <span>4 weeks</span>
                  <span className="text-primary font-medium">{formatTimelineText(timelineWeeks)}</span>
                  <span>52 weeks</span>
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerateRoadmap}
                disabled={generating}
                className="w-full px-6 py-4 bg-primary/20 hover:bg-primary/30 text-primary 
                         rounded-2xl font-bold flex items-center justify-center gap-3 
                         transition-all border border-primary/30 disabled:opacity-50 
                         disabled:cursor-not-allowed hover:scale-105 active:scale-95"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating Roadmap...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Generate AI Roadmap
                  </>
                )}
              </button>

              <p className="text-center text-xs text-white/40">
                🤖 AI-powered • ⚡ ~10 seconds • 📊 Based on your current skills
              </p>
            </div>
          </div>

          {/* RIGHT: Preview/Info */}
          <div className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 rounded-[2rem] p-8">
            <h3 className="text-xl font-light mb-6 flex items-center gap-3">
              <Zap size={24} className="text-primary" />
              What You'll Get
            </h3>

            <div className="space-y-4">
              <FeatureItem 
                icon={<Brain className="text-primary" />}
                title="Skill Gap Analysis"
                description="Identify what you need to learn vs what you already know"
              />
              <FeatureItem 
                icon={<Target className="text-primary" />}
                title="Phased Learning Path"
                description="Structured plan from foundation to advanced topics"
              />
              <FeatureItem 
                icon={<BookOpen className="text-primary" />}
                title="Curated Resources"
                description="Best courses, tutorials, and materials for each skill"
              />
              <FeatureItem 
                icon={<Calendar className="text-primary" />}
                title="Auto Google Calendar Sync"
                description="Schedule next 7 days automatically with smart AI"
              />
              <FeatureItem 
                icon={<Bell className="text-primary" />}
                title="Smart Notifications"
                description="3-day missed reminder and auto-rescheduling"
              />
              <FeatureItem 
                icon={<Send className="text-primary" />}
                title="Weekly Email Summary"
                description="Sunday morning roadmap progress updates"
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Has roadmap - show dashboard
  const { roadmap, statistics, tasks_by_phase } = roadmapData;

  const daysRemaining = roadmap ? calculateDaysRemaining(
    roadmap.timeline_weeks, 
    roadmap.created_at
  ) : 0;

  return (
    <div className="space-y-8">
      
      {/* Header with Google OAuth */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-light mb-2">
            🎯 {roadmap?.target_role}
          </h2>
          <p className="text-white/60">
            {formatTimelineText(roadmap?.timeline_weeks || 0)} • {roadmap?.current_phase} phase • {daysRemaining} days left
          </p>
        </div>
        
        <div className="flex gap-3 flex-wrap">
          {/* Google Connect/Status */}
          {checkingGoogle ? (
            <div className="px-6 py-3 bg-white/5 rounded-2xl flex items-center gap-2">
              <Loader2 size={20} className="animate-spin text-white/40" />
              <span className="text-white/40 text-sm">Checking Google...</span>
            </div>
          ) : googleConnected ? (
            <>
              <div className="px-4 py-3 bg-green-500/10 border border-green-500/30 rounded-2xl flex items-center gap-2">
                <CheckCircle size={18} className="text-green-400" />
                <span className="text-green-400 font-medium text-sm">Google Connected</span>
                <button
                  onClick={handleDisconnectGoogle}
                  className="ml-1 text-green-400/60 hover:text-green-400 transition-colors"
                  title="Disconnect Google"
                >
                  <XCircle size={16} />
                </button>
              </div>
              
              <button
                onClick={handleScheduleNext7Days}
                disabled={scheduling}
                className="px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary rounded-2xl 
                         font-bold flex items-center gap-3 transition-all border border-primary/30
                         disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
              >
                {scheduling ? (
                  <>
                    <Loader2 size={20} className="animate-spin" />
                    Scheduling...
                  </>
                ) : (
                  <>
                    <Calendar size={20} />
                    Schedule Next 7 Days
                  </>
                )}
              </button>
            </>
          ) : (
            <button
              onClick={handleConnectGoogle}
              className="px-6 py-3 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 
                       rounded-2xl font-bold flex items-center gap-3 transition-all 
                       border border-blue-500/30 hover:scale-105 active:scale-95"
            >
              <Link size={20} />
              Connect Google Calendar
            </button>
          )}
          
          <button
            onClick={fetchCurrentRoadmap}
            className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white/80 rounded-2xl 
                     font-bold flex items-center gap-3 transition-all border border-white/10
                     hover:scale-105 active:scale-95"
            title="Refresh roadmap"
          >
            <RefreshCw size={20} />
          </button>
          
          <button
            onClick={handleDeleteRoadmap}
            className="px-6 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-2xl 
                     font-bold flex items-center gap-3 transition-all border border-red-500/30
                     hover:scale-105 active:scale-95"
            title="Delete roadmap"
          >
            <Trash2 size={20} />
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-[2rem] p-4 flex items-center gap-3 animate-in fade-in">
          <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
          <p className="text-red-400 flex-1">{error}</p>
          <button 
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-300 font-medium transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      {successMessage && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-[2rem] p-4 flex items-center gap-3 animate-in fade-in">
          <CheckCircle2 className="w-6 h-6 text-green-400 flex-shrink-0" />
          <p className="text-green-400 flex-1">{successMessage}</p>
          <button 
            onClick={() => setSuccessMessage(null)}
            className="text-green-400 hover:text-green-300 font-medium transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Progress Bar */}
      <div className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 rounded-[2rem] p-6">
        <div className="flex justify-between text-sm mb-2 font-medium">
          <span className="text-white/80">Overall Progress</span>
          <span className="text-primary text-lg">{roadmap?.overall_progress}%</span>
        </div>
        <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
          <div
            className="bg-primary h-3 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${roadmap?.overall_progress}%` }}
          />
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          icon={<CheckCircle2 className="text-green-400" />}
          label="Completed"
          value={statistics?.completed || 0}
        />
        <MetricCard
          icon={<Clock className="text-blue-400" />}
          label="In Progress"
          value={statistics?.in_progress || 0}
        />
        <MetricCard
          icon={<Circle className="text-white/40" />}
          label="Not Started"
          value={statistics?.not_started || 0}
        />
        <MetricCard
          icon={<Award className="text-primary" />}
          label="Total Tasks"
          value={statistics?.total_tasks || 0}
        />
      </div>

      {/* Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <SkillGapAnalysis roadmapData={roadmapData.roadmap_data} />
        </div>
        <div>
          {roadmap?.diagram && (
            <RoadmapVisualization
              svgUrl={roadmap.diagram.svg_url}
              pngUrl={roadmap.diagram.png_url}
            />
          )}
        </div>
      </div>

      {/* Tasks by Phase */}
      <div className="space-y-4">
        <h3 className="text-2xl font-light flex items-center gap-3">
          <Calendar size={24} className="text-primary" />
          Learning Tasks
        </h3>
        {Object.entries(tasks_by_phase || {}).map(([phase, tasks]: [string, any]) => (
          <LearningResources
            key={phase}
            phase={phase}
            tasks={tasks}
            onTaskUpdate={handleTaskUpdate}
          />
        ))}
      </div>
    </div>
  );
};

// Helper Components
const MetricCard: React.FC<{ 
  icon: React.ReactNode; 
  label: string; 
  value: number;
}> = ({ icon, label, value }) => (
  <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6 hover:bg-white/10 transition-all">
    <div className="flex items-center justify-between mb-4">
      <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
        {icon}
      </div>
    </div>
    <p className="text-3xl font-light mb-1">{value}</p>
    <p className="text-sm text-white/40">{label}</p>
  </div>
);

const FeatureItem: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
}> = ({ icon, title, description }) => (
  <div className="flex items-start gap-4 p-4 bg-white/5 rounded-xl border border-white/10 hover:border-white/20 transition-all">
    <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
      {icon}
    </div>
    <div>
      <h4 className="font-medium text-white/90 mb-1">{title}</h4>
      <p className="text-sm text-white/60">{description}</p>
    </div>
  </div>
);

export default RoadmapModule;
