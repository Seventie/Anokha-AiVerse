// frontend/components/Dashboard/SummaryModule.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { journalService } from '../../services/journalService';
import { 
  BarChart3, Calendar, TrendingUp, CheckCircle, 
  Clock, Target, Award, Loader2, 
  Sparkles, Zap, ArrowLeft, ArrowRight,
  Brain, Heart, BookOpen, MessageSquare
} from 'lucide-react';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from 'recharts';

interface SummaryModuleProps {
  user: User;
}

const COLORS = ['#D4D4AA', '#8B8B66', '#A8A888', '#C0C099', '#BCBC88'];

const SummaryModule: React.FC<SummaryModuleProps> = ({ user }) => {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    setLoading(true);
    try {
      const data = await journalService.getComprehensiveSummary();
      setSummary(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load summary:', error);
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

  if (!summary) {
    return (
      <div className="text-center py-20">
        <BarChart3 size={80} className="mx-auto mb-8 text-white/20" />
        <h3 className="text-2xl font-light mb-4">No Data Available</h3>
        <p className="text-white/60">Start journaling to see your progress!</p>
      </div>
    );
  }

  const { metrics, mood_distribution, top_topics, daily_activity, ai_summary, skills_breakdown } = summary;

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Weekly Progress</h2>
          <p className="text-white/60">
            {summary.period?.start} - {summary.period?.end}
          </p>
        </div>
        <button
          onClick={loadSummary}
          className="px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary rounded-2xl font-bold flex items-center gap-3 transition-all border border-primary/30"
        >
          <Zap size={20} />
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard
          icon={<BookOpen className="text-primary" />}
          label="Journal Entries"
          value={metrics.journal_entries}
          change={`${metrics.completion_rate}% weekly goal`}
        />
        <MetricCard
          icon={<Brain className="text-blue-400" />}
          label="Skills Tracked"
          value={metrics.skills_count}
          change="Active skills"
        />
        <MetricCard
          icon={<MessageSquare className="text-green-400" />}
          label="Interviews"
          value={metrics.interviews_practiced}
          change="This week"
        />
        <MetricCard
          icon={<Heart className={
            metrics.avg_sentiment > 0.3 ? "text-green-400" :
            metrics.avg_sentiment < -0.3 ? "text-red-400" : "text-yellow-400"
          } />}
          label="Avg Sentiment"
          value={metrics.avg_sentiment > 0 ? `+${metrics.avg_sentiment}` : metrics.avg_sentiment}
          change={
            metrics.avg_sentiment > 0.3 ? "Positive" :
            metrics.avg_sentiment < -0.3 ? "Needs attention" : "Neutral"
          }
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Daily Activity Chart */}
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
            <TrendingUp size={20} className="text-primary" />
            Daily Activity
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={daily_activity}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" />
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

        {/* Mood Distribution */}
        {mood_distribution && mood_distribution.length > 0 && (
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
              <Heart size={20} className="text-primary" />
              Mood Distribution
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={mood_distribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {mood_distribution.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ 
                    backgroundColor: 'rgba(20,20,20,0.9)', 
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* AI Summary */}
      {ai_summary && (
        <div className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 rounded-[2rem] p-6">
          <h3 className="text-xl font-medium mb-4 flex items-center gap-3">
            <Sparkles size={24} className="text-primary" />
            AI-Generated Weekly Insights
          </h3>
          
          {ai_summary.summary && (
            <p className="text-white/90 mb-6 leading-relaxed">{ai_summary.summary}</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Themes */}
            {ai_summary.themes && ai_summary.themes.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-primary mb-3">Key Themes</h4>
                <div className="flex flex-wrap gap-2">
                  {ai_summary.themes.map((theme: string, idx: number) => (
                    <span key={idx} className="px-3 py-1 bg-white/10 rounded-full text-sm">
                      {theme}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Progress Highlights */}
            {ai_summary.progress_highlights && ai_summary.progress_highlights.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-green-400 mb-3">Progress Highlights</h4>
                <ul className="space-y-2">
                  {ai_summary.progress_highlights.map((highlight: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-white/80">
                      <CheckCircle size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                      <span>{highlight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Recommendations */}
          {ai_summary.recommendations && ai_summary.recommendations.length > 0 && (
            <div className="mt-6 pt-6 border-t border-white/10">
              <h4 className="text-sm font-medium text-primary mb-3">Recommendations for Next Week</h4>
              <ul className="space-y-2">
                {ai_summary.recommendations.map((rec: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-white/80">
                    <Target size={16} className="text-primary mt-0.5 flex-shrink-0" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Top Topics */}
      {top_topics && top_topics.length > 0 && (
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
            <Brain size={20} className="text-primary" />
            Topics You Focused On
          </h3>
          <div className="space-y-3">
            {top_topics.map((topic: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between">
                <span className="text-white/80 capitalize">{topic.name}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 bg-white/10 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{ width: `${(topic.count / top_topics[0].count) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-white/60 w-8 text-right">{topic.count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skills Breakdown */}
      {skills_breakdown && skills_breakdown.length > 0 && (
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
            <Award size={20} className="text-primary" />
            Your Skills
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {skills_breakdown.map((skill: any, idx: number) => (
              <div key={idx} className="p-3 bg-white/5 rounded-xl">
                <div className="text-sm font-medium text-white/90 mb-1">{skill.name}</div>
                <div className="text-xs text-white/60 capitalize">{skill.level}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const MetricCard = ({ icon, label, value, change }: any) => (
  <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
    <div className="flex items-center justify-between mb-4">
      <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
        {icon}
      </div>
    </div>
    <p className="text-3xl font-light mb-1">{value}</p>
    <p className="text-sm text-white/40">{label}</p>
    {change && (
      <p className="text-xs text-white/30 mt-2">{change}</p>
    )}
  </div>
);

export default SummaryModule;
