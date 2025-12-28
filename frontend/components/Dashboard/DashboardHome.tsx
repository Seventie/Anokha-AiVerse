// frontend/src/components/Dashboard/DashboardHome.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { agentService } from '../../services/agentService';
import { 
  Sparkles, TrendingUp, Target, Calendar, 
  Briefcase, Award, Zap, ChevronRight,
  Clock, MapPin, Book
} from 'lucide-react';

interface DashboardHomeProps {
  user: User;
}

const DashboardHome: React.FC<DashboardHomeProps> = ({ user }) => {
  const [dailyQuote, setDailyQuote] = useState('');
  const [todaySchedule, setTodaySchedule] = useState<any[]>([]);
  const [topJobs, setTopJobs] = useState<any[]>([]);
  const [progress, setProgress] = useState({ completed: 0, total: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const data = await agentService.getDashboardData(user.id);
      setDailyQuote(data?.quote || 'Success is not final, failure is not fatal: it is the courage to continue that counts.');
      setTodaySchedule(data?.schedule || []);
      setTopJobs(data?.topJobs || []);
      setProgress(data?.progress || { completed: 0, total: 0 });
      setLoading(false);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      setDailyQuote('Success is not final, failure is not fatal: it is the courage to continue that counts.');
      setTodaySchedule([]);
      setTopJobs([]);
      setProgress({ completed: 0, total: 0 });
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-primary/20 via-primary/10 to-transparent border border-primary/30 rounded-[3rem] p-12">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-5xl font-light mb-4">
              Welcome back, <span className="text-primary font-medium">{(user.fullName || user.email || 'User').split(' ')[0]}</span>
            </h1>
            <p className="text-xl text-white/60 mb-6 flex items-center gap-3">
              <Target size={20} className="text-primary" />
              On track to become a {user.targetRole || 'your dream role'}
            </p>
            <div className="flex items-center gap-8 text-sm text-white/40">
              <div className="flex items-center gap-2">
                <Clock size={16} />
                <span>{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</span>
              </div>
              {user.location && (
                <div className="flex items-center gap-2">
                  <MapPin size={16} />
                  <span>{user.location}</span>
                </div>
              )}
            </div>
          </div>
          <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center text-primary text-3xl font-bold">
            {(user.fullName || user.email || 'U').charAt(0).toUpperCase()}
          </div>
        </div>
      </div>

      {/* Daily Quote */}
      <div className="bg-white/5 border border-white/10 rounded-[3rem] p-10 relative overflow-hidden">
        <div className="absolute top-6 right-6 text-primary/10">
          <Sparkles size={60} />
        </div>
        <div className="relative z-10">
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-4">Daily Motivation</p>
          <p className="text-2xl font-light italic text-white/90 leading-relaxed">
            "{dailyQuote || 'Success is not final, failure is not fatal: it is the courage to continue that counts.'}"
          </p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          icon={<TrendingUp className="text-green-400" />}
          label="Progress This Week"
          value={`${progress.completed}/${progress.total}`}
          change="+12%"
          positive={true}
        />
        <StatCard
          icon={<Briefcase className="text-blue-400" />}
          label="New Opportunities"
          value={topJobs.length.toString()}
          change="Updated 2h ago"
        />
        <StatCard
          icon={<Award className="text-yellow-400" />}
          label="Skills Acquired"
          value="7"
          change="This month"
        />
      </div>

      {/* Today's Schedule & Top Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Today's Schedule */}
        <div className="bg-white/5 border border-white/10 rounded-[3rem] p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-medium flex items-center gap-3">
              <Calendar size={24} className="text-primary" />
              Today's Schedule
            </h3>
            <button className="text-sm text-primary hover:underline">View All</button>
          </div>
          
          <div className="space-y-4">
            {todaySchedule.length > 0 ? (
              todaySchedule.map((item, idx) => (
                <div key={idx} className="flex items-start gap-4 p-4 bg-white/5 rounded-2xl hover:bg-white/10 transition-all">
                  <div className="w-2 h-2 rounded-full bg-primary mt-2"></div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-medium">{item.title}</p>
                      <span className="text-xs text-white/40">{item.time}</span>
                    </div>
                    <p className="text-sm text-white/60">{item.description}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-white/40">
                <Calendar size={48} className="mx-auto mb-4 opacity-20" />
                <p>No tasks scheduled for today</p>
                <button className="mt-4 text-primary text-sm hover:underline">
                  Plan your day
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Top Opportunities */}
        <div className="bg-white/5 border border-white/10 rounded-[3rem] p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-medium flex items-center gap-3">
              <Briefcase size={24} className="text-primary" />
              Top Opportunities
            </h3>
            <button className="text-sm text-primary hover:underline">See More</button>
          </div>
          
          <div className="space-y-4">
            {topJobs.slice(0, 3).map((job, idx) => (
              <div key={idx} className="p-4 bg-white/5 rounded-2xl hover:bg-white/10 transition-all cursor-pointer group">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-medium mb-1 group-hover:text-primary transition-colors">
                      {job.title}
                    </h4>
                    <p className="text-sm text-white/60">{job.company}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                      {job.compatibility}% Match
                    </div>
                    <ChevronRight size={16} className="text-white/40 group-hover:text-primary transition-colors" />
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-white/40">
                  <MapPin size={12} />
                  <span>{job.location}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <QuickActionCard
          icon={<Book size={24} />}
          title="Daily Journal"
          description="Reflect on your progress"
          color="bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/30"
        />
        <QuickActionCard
          icon={<Target size={24} />}
          title="Update Roadmap"
          description="Adjust your goals"
          color="bg-purple-500/10 hover:bg-purple-500/20 border-purple-500/30"
        />
        <QuickActionCard
          icon={<Zap size={24} />}
          title="Practice Interview"
          description="Mock interview session"
          color="bg-yellow-500/10 hover:bg-yellow-500/20 border-yellow-500/30"
        />
        <QuickActionCard
          icon={<Award size={24} />}
          title="View Progress"
          description="Weekly summary"
          color="bg-green-500/10 hover:bg-green-500/20 border-green-500/30"
        />
      </div>
    </div>
  );
};

const StatCard = ({ icon, label, value, change, positive }: any) => (
  <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
    <div className="flex items-center justify-between mb-4">
      <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
        {icon}
      </div>
      {positive !== undefined && (
        <span className={`text-xs ${positive ? 'text-green-400' : 'text-red-400'}`}>
          {change}
        </span>
      )}
    </div>
    <p className="text-3xl font-light mb-1">{value}</p>
    <p className="text-sm text-white/40">{label}</p>
    {positive === undefined && (
      <p className="text-xs text-white/30 mt-2">{change}</p>
    )}
  </div>
);

const QuickActionCard = ({ icon, title, description, color }: any) => (
  <button className={`${color} border rounded-[2rem] p-6 text-left transition-all hover:scale-105 active:scale-95`}>
    <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center text-primary mb-4">
      {icon}
    </div>
    <h4 className="font-medium mb-1">{title}</h4>
    <p className="text-xs text-white/60">{description}</p>
  </button>
);

export default DashboardHome;