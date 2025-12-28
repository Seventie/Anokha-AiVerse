// frontend/components/Dashboard/SummaryModule.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { agentService } from '../../services/agentService';
import { 
  BarChart3, Calendar, TrendingUp, CheckCircle, 
  Clock, Target, Award, Loader2, 
  Sparkles, Zap, ArrowLeft, ArrowRight
} from 'lucide-react';

interface SummaryModuleProps {
  user: User;
}

const SummaryModule: React.FC<SummaryModuleProps> = ({ user }) => {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [weekOffset, setWeekOffset] = useState(0);

  useEffect(() => {
    loadSummary();
  }, [weekOffset]);

  const loadSummary = async () => {
    setLoading(true);
    try {
      const data = await agentService.getWeeklySummary(user.id, weekOffset);
      setSummary(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load summary:', error);
      setLoading(false);
    }
  };

  const generateNewSummary = async () => {
    setGenerating(true);
    try {
      const result = await agentService.generateSummary(user.id);
      setSummary(result);
    } catch (error) {
      console.error('Failed to generate summary:', error);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Weekly Progress</h2>
          <p className="text-white/60">Your career journey summary</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setWeekOffset(weekOffset + 1)}
            className="p-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all"
          >
            <ArrowLeft size={20} />
          </button>
          <span className="px-4 py-2 bg-white/5 rounded-xl text-sm">
            Week {weekOffset === 0 ? 'This Week' : `${weekOffset} week${weekOffset > 1 ? 's' : ''} ago`}
          </span>
          <button
            onClick={() => setWeekOffset(Math.max(0, weekOffset - 1))}
            disabled={weekOffset === 0}
            className="p-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all disabled:opacity-50"
          >
            <ArrowRight size={20} />
          </button>
          <button
            onClick={generateNewSummary}
            disabled={generating}
            className="px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary rounded-2xl font-bold flex items-center gap-3 transition-all border border-primary/30"
          >
            {generating ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Zap size={20} />
                Generate
              </>
            )}
          </button>
        </div>
      </div>

      {summary ? (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <MetricCard
              icon={<CheckCircle className="text-green-400" />}
              label="Tasks Completed"
              value={`${summary.completed_tasks?.length || 0}`}
              change={`${summary.metrics?.completion_rate || 0}% completion rate`}
            />
            <MetricCard
              icon={<Target className="text-blue-400" />}
              label="Skills Progressed"
              value={Object.keys(summary.skills_progress || {}).length}
              change="This week"
            />
            <MetricCard
              icon={<Award className="text-yellow-400" />}
              label="Interviews Practiced"
              value={summary.metrics?.interviews_practiced || 0}
              change="Mock sessions"
            />
            <MetricCard
              icon={<TrendingUp className="text-purple-400" />}
              label="Job Applications"
              value={summary.metrics?.jobs_discovered || 0}
              change="Opportunities found"
            />
          </div>

          {/* Completed Tasks */}
          {summary.completed_tasks && summary.completed_tasks.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
              <h3 className="text-xl font-medium mb-4 flex items-center gap-3">
                <CheckCircle size={24} className="text-green-400" />
                Completed Tasks
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {summary.completed_tasks.map((task: any, idx: number) => (
                  <div key={idx} className="p-4 bg-white/5 rounded-2xl">
                    <div className="flex items-start gap-3">
                      <CheckCircle size={20} className="text-green-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="font-medium text-white/90">{task.task || task}</p>
                        {task.category && (
                          <p className="text-xs text-white/40 mt-1">{task.category}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missed Tasks */}
          {summary.missed_tasks && summary.missed_tasks.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
              <h3 className="text-xl font-medium mb-4 flex items-center gap-3">
                <Clock size={24} className="text-yellow-400" />
                Missed Tasks
              </h3>
              <div className="space-y-3">
                {summary.missed_tasks.map((task: any, idx: number) => (
                  <div key={idx} className="p-4 bg-white/5 rounded-2xl flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-white/90">{task.task || task}</p>
                      {task.reason && (
                        <p className="text-sm text-white/60 mt-1">Reason: {task.reason}</p>
                      )}
                    </div>
                    {task.can_reschedule && (
                      <button className="px-3 py-1 bg-primary/20 text-primary rounded-xl text-sm hover:bg-primary/30 transition-all">
                        Reschedule
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skills Progress */}
          {summary.skills_progress && Object.keys(summary.skills_progress).length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
              <h3 className="text-xl font-medium mb-4 flex items-center gap-3">
                <TrendingUp size={24} className="text-primary" />
                Skills Progress
              </h3>
              <div className="space-y-4">
                {Object.entries(summary.skills_progress).map(([skill, data]: [string, any]) => (
                  <div key={skill} className="p-4 bg-white/5 rounded-2xl">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{skill}</h4>
                      <span className="text-sm text-primary">
                        {data.progress_percentage || 0}%
                      </span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2 mb-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{ width: `${data.progress_percentage || 0}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-xs text-white/60">
                      <span>{data.time_invested_hours || 0}h invested</span>
                      <span className="capitalize">{data.confidence_level || 'beginner'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Insights */}
          {summary.insights && summary.insights.length > 0 && (
            <div className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 rounded-[2rem] p-6">
              <h3 className="text-xl font-medium mb-4 flex items-center gap-3">
                <Sparkles size={24} className="text-primary" />
                Key Insights
              </h3>
              <ul className="space-y-3">
                {summary.insights.map((insight: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-3 text-white/90">
                    <Zap size={18} className="text-primary mt-0.5 flex-shrink-0" />
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {summary.recommendations && summary.recommendations.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
              <h3 className="text-xl font-medium mb-4 flex items-center gap-3">
                <Target size={24} className="text-primary" />
                Recommendations for Next Week
              </h3>
              <div className="space-y-3">
                {summary.recommendations.map((rec: any, idx: number) => (
                  <div key={idx} className="p-4 bg-white/5 rounded-2xl">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-white/90">{rec.action || rec}</h4>
                      <span className={`px-3 py-1 rounded-full text-xs ${
                        rec.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                        rec.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {rec.priority || 'medium'}
                      </span>
                    </div>
                    {rec.reasoning && (
                      <p className="text-sm text-white/60 mt-2">{rec.reasoning}</p>
                    )}
                    {rec.estimated_time && (
                      <p className="text-xs text-white/40 mt-2">
                        Estimated: {rec.estimated_time}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Celebrations */}
          {summary.celebrations && summary.celebrations.length > 0 && (
            <div className="bg-gradient-to-br from-yellow-500/20 to-yellow-500/5 border border-yellow-500/30 rounded-[2rem] p-6">
              <h3 className="text-xl font-medium mb-4 flex items-center gap-3">
                <Award size={24} className="text-yellow-400" />
                Celebrations
              </h3>
              <ul className="space-y-2">
                {summary.celebrations.map((celebration: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-3 text-white/90">
                    <Sparkles size={18} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                    <span>{celebration}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* News Summary */}
          {summary.news && (
            <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
              <h3 className="text-xl font-medium mb-4 flex items-center gap-3">
                <Calendar size={24} className="text-primary" />
                Industry News
              </h3>
              <p className="text-white/80 leading-relaxed whitespace-pre-line">
                {summary.news}
              </p>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-20">
          <BarChart3 size={80} className="mx-auto mb-8 text-white/20" />
          <h3 className="text-2xl font-light mb-4">No Summary Available</h3>
          <p className="text-white/60 mb-8 max-w-md mx-auto">
            Generate a weekly summary to see your progress, insights, and recommendations.
          </p>
          <button
            onClick={generateNewSummary}
            disabled={generating}
            className="px-8 py-4 bg-primary text-bg-deep rounded-2xl font-bold flex items-center gap-3 mx-auto hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all"
          >
            <Zap size={20} />
            Generate Summary
          </button>
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

