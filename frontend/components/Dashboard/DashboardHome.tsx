// frontend/src/components/Dashboard/DashboardHome.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { dashboardService, DashboardData } from '../../services/dashboardService';
import { 
  Sparkles, TrendingUp, Target, Calendar, 
  Briefcase, Award, Zap, ChevronRight,
  Clock, MapPin, Book, Brain, MessageCircle,
  Flame, TrendingDown, Activity, Loader2,
  Newspaper, Lightbulb, CheckCircle2
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts';

interface DashboardHomeProps {
  user: User;
}

const DashboardHome: React.FC<DashboardHomeProps> = ({ user }) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const dashboardData = await dashboardService.getDashboardHome();
      setData(dashboardData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20">
        <p className="text-white/60">Failed to load dashboard. Please refresh.</p>
      </div>
    );
  }

  const { stats, progress, today_actions, recent_activity, industry_news, quick_stats } = data;

  // Prepare chart data
  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const activityData = progress.daily_entries.map((entries, idx) => ({
    day: weekDays[idx],
    entries
  }));

  return (
    <div className="space-y-8">
      
      {/* Welcome Header with Live Stats */}
      <div className="bg-gradient-to-r from-primary/20 via-primary/10 to-transparent border border-primary/30 rounded-[3rem] p-12">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-5xl font-light mb-4">
              Welcome back, <span className="text-primary font-medium">{data.user.name}</span>
            </h1>
            <p className="text-xl text-white/60 mb-6 flex items-center gap-3">
              <Target size={20} className="text-primary" />
              On track to become a {data.user.target_role}
            </p>
            <div className="flex items-center gap-8 text-sm text-white/40">
              <div className="flex items-center gap-2">
                <Clock size={16} />
                <span>{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</span>
              </div>
              {data.user.location && (
                <div className="flex items-center gap-2">
                  <MapPin size={16} />
                  <span>{data.user.location}</span>
                </div>
              )}
              {stats.streak_days > 0 && (
                <div className="flex items-center gap-2 text-orange-400">
                  <Flame size={16} />
                  <span>{stats.streak_days} day streak!</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-4">
            <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center text-primary text-3xl font-bold">
              {data.user.name.charAt(0).toUpperCase()}
            </div>
            <div className="text-right">
              <p className="text-sm text-white/40">Profile Completeness</p>
              <p className="text-2xl font-bold text-primary">{quick_stats.profile_completeness}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Industry News Banner */}
      <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-[3rem] p-8">
        <div className="flex items-start gap-6">
          <div className="w-16 h-16 rounded-2xl bg-blue-500/20 flex items-center justify-center flex-shrink-0">
            <Newspaper size={32} className="text-blue-400" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs font-medium">
                TRENDING NOW
              </span>
              <span className="text-xs text-white/40">Industry Insights</span>
            </div>
            <h3 className="text-2xl font-medium mb-3 text-white/90">
              {industry_news.headline}
            </h3>
            <p className="text-white/70 mb-4 leading-relaxed">
              {industry_news.summary}
            </p>
            <div className="flex items-start gap-3 p-4 bg-white/5 rounded-2xl border border-white/10">
              <Lightbulb size={20} className="text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-white/60 mb-1">Key Takeaway:</p>
                <p className="text-white/90">{industry_news.takeaway}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Quote */}
      <div className="bg-white/5 border border-white/10 rounded-[3rem] p-10 relative overflow-hidden">
        <div className="absolute top-6 right-6 text-primary/10">
          <Sparkles size={60} />
        </div>
        <div className="relative z-10">
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-4">Your Daily Motivation</p>
          <p className="text-2xl font-light italic text-white/90 leading-relaxed">
            "{data.daily_quote}"
          </p>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <StatCard
          icon={<Book className="text-blue-400" />}
          label="Journal Entries"
          value={stats.journal_entries_week}
          subtitle="This week"
          change={`${stats.journal_entries_month} this month`}
        />
        <StatCard
          icon={<MessageCircle className="text-green-400" />}
          label="Interview Practice"
          value={stats.interviews_completed}
          subtitle="Total sessions"
          change={`${stats.interviews_this_week} this week`}
        />
        <StatCard
          icon={<Award className="text-yellow-400" />}
          label="Skills"
          value={stats.skills_count}
          subtitle="In your arsenal"
          change={`${stats.projects_count} projects`}
        />
        <StatCard
          icon={
            stats.mood_trend === 'positive' ? <TrendingUp className="text-green-400" /> :
            stats.mood_trend === 'needs_attention' ? <TrendingDown className="text-red-400" /> :
            <Activity className="text-yellow-400" />
          }
          label="Mood Trend"
          value={stats.mood_trend === 'positive' ? 'Positive' : stats.mood_trend === 'needs_attention' ? 'Low' : 'Neutral'}
          subtitle="This week"
          change={`${stats.avg_sentiment > 0 ? '+' : ''}${stats.avg_sentiment} sentiment`}
        />
      </div>

      {/* Progress & Activity Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Weekly Progress */}
        <div className="bg-white/5 border border-white/10 rounded-[3rem] p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-medium flex items-center gap-3">
              <TrendingUp size={24} className="text-primary" />
              Weekly Progress
            </h3>
            <span className="text-2xl font-bold text-primary">{progress.percentage}%</span>
          </div>
          
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/60">Days Active: {progress.completed}/{progress.total}</span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-3">
              <div
                className="bg-primary h-3 rounded-full transition-all"
                style={{ width: `${progress.percentage}%` }}
              />
            </div>
          </div>

          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="day" stroke="rgba(255,255,255,0.5)" />
              <YAxis stroke="rgba(255,255,255,0.5)" />
              <Tooltip
                contentStyle={{ 
                  backgroundColor: 'rgba(20,20,20,0.9)', 
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px'
                }}
              />
              <Bar dataKey="entries" fill="#D4D4AA" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Today's Actions */}
        <div className="bg-white/5 border border-white/10 rounded-[3rem] p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-medium flex items-center gap-3">
              <CheckCircle2 size={24} className="text-primary" />
              Today's Actions
            </h3>
            <span className="text-sm text-white/60">{today_actions.length} tasks</span>
          </div>
          
          <div className="space-y-3">
            {today_actions.map((action, idx) => (
              <div
                key={idx}
                className="p-4 bg-white/5 rounded-2xl hover:bg-white/10 transition-all cursor-pointer group border border-white/5 hover:border-primary/30"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-1 rounded-lg text-xs font-medium ${
                        action.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                        action.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {action.priority}
                      </span>
                      <span className="text-xs text-white/40">{action.time}</span>
                    </div>
                    <h4 className="font-medium text-white/90 group-hover:text-primary transition-colors">
                      {action.title}
                    </h4>
                    <p className="text-sm text-white/60 mt-1">{action.description}</p>
                  </div>
                  <ChevronRight size={20} className="text-white/40 group-hover:text-primary transition-colors" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      {recent_activity.length > 0 && (
        <div className="bg-white/5 border border-white/10 rounded-[3rem] p-8">
          <h3 className="text-xl font-medium mb-6 flex items-center gap-3">
            <Activity size={24} className="text-primary" />
            Recent Activity
          </h3>
          <div className="space-y-3">
            {recent_activity.map((activity, idx) => (
              <div key={idx} className="flex items-center gap-4 p-4 bg-white/5 rounded-2xl">
                <div className="w-2 h-2 rounded-full bg-primary"></div>
                <div className="flex-1">
                  <p className="text-white/90">{activity.title}</p>
                  {activity.mood && (
                    <span className="text-xs text-white/60 capitalize">Mood: {activity.mood}</span>
                  )}
                </div>
                <span className="text-xs text-white/40">
                  {new Date(activity.time).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <QuickActionCard
          icon={<Book size={24} />}
          title="Daily Journal"
          description="Reflect on your progress"
          color="bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/30"
          onClick={() => window.location.hash = '#/dashboard/journal'}
        />
        <QuickActionCard
          icon={<Target size={24} />}
          title="View Roadmap"
          description="Track your goals"
          color="bg-purple-500/10 hover:bg-purple-500/20 border-purple-500/30"
          onClick={() => window.location.hash = '#/dashboard/roadmap'}
        />
        <QuickActionCard
          icon={<Zap size={24} />}
          title="Practice Interview"
          description="Mock interview session"
          color="bg-yellow-500/10 hover:bg-yellow-500/20 border-yellow-500/30"
          onClick={() => window.location.hash = '#/dashboard/interview'}
        />
        <QuickActionCard
          icon={<Award size={24} />}
          title="View Progress"
          description="Weekly summary"
          color="bg-green-500/10 hover:bg-green-500/20 border-green-500/30"
          onClick={() => window.location.hash = '#/dashboard/summary'}
        />
      </div>
    </div>
  );
};

const StatCard = ({ icon, label, value, subtitle, change }: any) => (
  <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
    <div className="flex items-center justify-between mb-4">
      <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
        {icon}
      </div>
    </div>
    <p className="text-3xl font-light mb-1">{value}</p>
    <p className="text-sm text-white/40">{label}</p>
    <p className="text-xs text-white/30 mt-2">{subtitle}</p>
    {change && (
      <p className="text-xs text-white/20 mt-1">{change}</p>
    )}
  </div>
);

const QuickActionCard = ({ icon, title, description, color, onClick }: any) => (
  <button 
    onClick={onClick}
    className={`${color} border rounded-[2rem] p-6 text-left transition-all hover:scale-105 active:scale-95`}
  >
    <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center text-primary mb-4">
      {icon}
    </div>
    <h4 className="font-medium mb-1">{title}</h4>
    <p className="text-xs text-white/60">{description}</p>
  </button>
);

export default DashboardHome;
