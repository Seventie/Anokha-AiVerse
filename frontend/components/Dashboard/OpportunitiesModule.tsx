// frontend/components/Dashboard/OpportunitiesModule.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { agentService } from '../../services/agentService';
import { 
  Briefcase, MapPin, TrendingUp, Clock, 
  Save, ExternalLink, Search, Loader2,
  Star, Filter, Zap, CheckCircle
} from 'lucide-react';

interface OpportunitiesModuleProps {
  user: User;
}

const OpportunitiesModule: React.FC<OpportunitiesModuleProps> = ({ user }) => {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  useEffect(() => {
    loadOpportunities();
  }, []);

  const loadOpportunities = async () => {
    try {
      const data = await agentService.getOpportunities(user.id);
      setOpportunities(data.opportunities || []);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load opportunities:', error);
      setLoading(false);
    }
  };

  const scanForOpportunities = async () => {
    setScanning(true);
    try {
      const result = await agentService.scanOpportunities(user.id);
      if (result.opportunities) {
        setOpportunities(result.opportunities);
      }
    } catch (error) {
      console.error('Failed to scan:', error);
    } finally {
      setScanning(false);
    }
  };

  const saveJob = async (jobId: string) => {
    try {
      await agentService.saveJob(user.id, jobId);
      alert('Job saved to your list!');
    } catch (error) {
      console.error('Failed to save job:', error);
    }
  };

  const filteredOpportunities = opportunities.filter(job => {
    if (filter === 'all') return true;
    const score = job.compatibility_score || job.compatibility || 0;
    if (filter === 'high') return score >= 80;
    if (filter === 'medium') return score >= 60 && score < 80;
    return score < 60;
  });

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
          <h2 className="text-3xl font-light mb-2">Job Opportunities</h2>
          <p className="text-white/60">Discover roles matching your profile</p>
        </div>
        <button
          onClick={scanForOpportunities}
          disabled={scanning}
          className="px-6 py-3 bg-primary text-bg-deep rounded-2xl font-bold flex items-center gap-3 hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
        >
          {scanning ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              Scanning...
            </>
          ) : (
            <>
              <Search size={20} />
              Scan Opportunities
            </>
          )}
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Filter size={20} className="text-white/40" />
        <div className="flex gap-2">
          {(['all', 'high', 'medium', 'low'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                filter === f
                  ? 'bg-primary/20 text-primary border border-primary/30'
                  : 'bg-white/5 text-white/60 hover:bg-white/10'
              }`}
            >
              {f === 'all' ? 'All' : f === 'high' ? 'High Match' : f === 'medium' ? 'Medium' : 'Low Match'}
            </button>
          ))}
        </div>
      </div>

      {/* Opportunities List */}
      <div className="space-y-4">
        {filteredOpportunities.length > 0 ? (
          filteredOpportunities.map((job, idx) => (
            <div
              key={job.job_id || idx}
              className="bg-white/5 border border-white/10 rounded-[2rem] p-6 hover:bg-white/10 transition-all group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-medium group-hover:text-primary transition-colors">
                      {job.title}
                    </h3>
                    {job.rank && (
                      <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-bold">
                        #{job.rank}
                      </span>
                    )}
                  </div>
                  <p className="text-white/60 mb-3">{job.company}</p>
                  <div className="flex items-center gap-4 text-sm text-white/40">
                    <div className="flex items-center gap-2">
                      <MapPin size={16} />
                      <span>{job.location}</span>
                    </div>
                    {job.posted_date && (
                      <div className="flex items-center gap-2">
                        <Clock size={16} />
                        <span>{job.posted_date}</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-3">
                  <div className={`px-4 py-2 rounded-full text-sm font-bold ${
                    (job.compatibility_score || job.compatibility || 0) >= 80
                      ? 'bg-green-500/20 text-green-400'
                      : (job.compatibility_score || job.compatibility || 0) >= 60
                      ? 'bg-yellow-500/20 text-yellow-400'
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {job.compatibility_score || job.compatibility || 0}% Match
                  </div>
                  {job.urgency && (
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      job.urgency === 'high' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {job.urgency} priority
                    </span>
                  )}
                </div>
              </div>

              {job.description && (
                <p className="text-white/70 mb-4 line-clamp-2">{job.description}</p>
              )}

              {/* Skills Match */}
              {job.matching_skills && job.matching_skills.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-white/40 mb-2">Matching Skills:</p>
                  <div className="flex flex-wrap gap-2">
                    {job.matching_skills.slice(0, 5).map((skill: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Missing Skills */}
              {job.missing_skills && job.missing_skills.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-white/40 mb-2">Skills to Learn:</p>
                  <div className="flex flex-wrap gap-2">
                    {job.missing_skills.slice(0, 3).map((skill: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-yellow-500/10 text-yellow-400 rounded-full text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-3 pt-4 border-t border-white/10">
                <button
                  onClick={() => saveJob(job.job_id || job.id)}
                  className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl flex items-center gap-2 transition-all"
                >
                  <Save size={16} />
                  Save Job
                </button>
                {job.application_url && (
                  <a
                    href={job.application_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl flex items-center gap-2 transition-all"
                  >
                    <ExternalLink size={16} />
                    Apply Now
                  </a>
                )}
                {job.application_actions && (
                  <button className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-sm transition-all">
                    View Tips
                  </button>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-20">
            <Briefcase size={80} className="mx-auto mb-8 text-white/20" />
            <h3 className="text-2xl font-light mb-4">No Opportunities Found</h3>
            <p className="text-white/60 mb-8 max-w-md mx-auto">
              Click "Scan Opportunities" to discover jobs matching your profile and skills.
            </p>
            <button
              onClick={scanForOpportunities}
              disabled={scanning}
              className="px-8 py-4 bg-primary text-bg-deep rounded-2xl font-bold flex items-center gap-3 mx-auto hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all"
            >
              <Zap size={20} />
              Start Scanning
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OpportunitiesModule;

