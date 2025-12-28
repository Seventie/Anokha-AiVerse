// frontend/src/components/Interview/InterviewAnalytics.tsx

import React, { useState, useEffect } from 'react';
import { interviewService } from '../../services/interviewService';
import { BarChart3, TrendingUp, Award, AlertCircle, Loader } from 'lucide-react';

interface Props {
  interviewId: string;
}

const InterviewAnalytics: React.FC<Props> = ({ interviewId }) => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!interviewId) {
      setLoading(false);
      return;
    }
    loadAnalytics();
  }, [interviewId]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await interviewService.getAnalytics(interviewId);
      setAnalytics(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-2xl bg-red-500/15 border border-red-500/40 text-xs text-red-100 flex items-start gap-3">
        <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <p>{error}</p>
      </div>
    );
  }

  if (!analytics) return null;

  const stats = [
    {
      label: 'Overall Score',
      value: `${analytics.overall_score || 0}/100`,
      icon: Award,
    },
    {
      label: 'Average Round Score',
      value: `${analytics.average_round_score || 0}/10`,
      icon: TrendingUp,
    },
    {
      label: 'Best Round Score',
      value: analytics.best_round_score || 'N/A',
      icon: BarChart3,
    },
    {
      label: 'Total Rounds',
      value: analytics.total_rounds || 0,
      icon: BarChart3,
    },
  ];

  return (
    <div className="space-y-8 text-white">
      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-white/[0.05] border border-white/15 backdrop-blur-sm flex flex-col justify-between shadow-black/30 shadow-lg"
            >
              <Icon className="w-5 h-5 text-primary mb-3" />
              <p className="text-[11px] font-medium tracking-[0.25em] uppercase text-white/50 mb-1">
                {stat.label}
              </p>
              <p className="text-2xl font-semibold tracking-tight">{stat.value}</p>
            </div>
          );
        })}
      </div>

      {/* Round-wise performance */}
      {analytics.rounds && analytics.rounds.length > 0 && (
        <div className="p-6 rounded-3xl bg-white/[0.04] border border-white/15 backdrop-blur-sm">
          <h3 className="text-sm font-medium tracking-[0.25em] uppercase text-white/60 mb-4">
            Round-wise Performance
          </h3>
          <div className="space-y-3">
            {analytics.rounds.map((round: any, idx: number) => (
              <div
                key={idx}
                className="flex flex-col md:flex-row gap-3 items-start md:items-center bg-white/5 border border-white/15 rounded-2xl px-4 py-3"
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">
                    Round {idx + 1} • {round.type} • {round.difficulty}
                  </p>
                  {round.feedback && (
                    <p className="text-xs text-white/70 mt-1">{round.feedback}</p>
                  )}
                </div>
                <div className="px-4 py-1.5 rounded-xl bg-primary text-white text-xs font-semibold">
                  {round.score}/10
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Strengths & improvements */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {analytics.strengths && (
          <div className="p-6 rounded-3xl bg-emerald-500/10 border border-emerald-500/50">
            <h4 className="text-sm font-medium tracking-[0.25em] uppercase text-emerald-200 mb-3">
              Strengths
            </h4>
            <ul className="space-y-2">
              {analytics.strengths.map((s: string, i: number) => (
                <li key={i} className="text-xs text-emerald-50 flex gap-2">
                  <span className="mt-[3px] w-1 h-1 rounded-full bg-emerald-300" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {analytics.improvements && (
          <div className="p-6 rounded-3xl bg-red-500/10 border border-red-500/50">
            <h4 className="text-sm font-medium tracking-[0.25em] uppercase text-red-200 mb-3">
              Areas to Improve
            </h4>
            <ul className="space-y-2">
              {analytics.improvements.map((s: string, i: number) => (
                <li key={i} className="text-xs text-red-50 flex gap-2">
                  <span className="mt-[3px] w-1 h-1 rounded-full bg-red-300" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default InterviewAnalytics;
