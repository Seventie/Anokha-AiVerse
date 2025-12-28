// frontend/components/Dashboard/OpportunitiesModule.tsx - REDESIGNED

import React, { useState, useEffect } from 'react';
import { opportunitiesService } from '../../services/opportunitiesService';
import { resumeService } from '../../services/resumeService';
import { 
  Briefcase, Search, Loader2, ExternalLink, 
  Save, CheckCircle, MapPin, TrendingUp, 
  Trophy, Upload, File, X, Sparkles
} from 'lucide-react';

interface JobOpportunity {
  id: string;
  match_id: number;
  title: string;
  company: string;
  location: string;
  url: string;
  job_type: string;
  is_remote: boolean;
  description?: string;
  requirements?: string[];
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  experience_level?: string;
  match_score: number;
  matching_skills: string[];
  missing_skills: string[];
  status: string;
  source?: string;
}

interface Hackathon {
  id: string;
  title: string;
  organizer: string;
  platform: string;
  prize_pool: string;
  url: string;
  match_score: number;
  themes?: string[];
  mode?: string;
  description?: string;
}

const OpportunitiesModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'jobs' | 'hackathons'>('jobs');
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [jobs, setJobs] = useState<JobOpportunity[]>([]);
  const [hackathons, setHackathons] = useState<Hackathon[]>([]);
  const [stats, setStats] = useState({
    total_matches: 0,
    applied: 0,
    saved: 0,
    interviewing: 0
  });
  const [message, setMessage] = useState('');
  const [showResumeUpload, setShowResumeUpload] = useState(false);

  useEffect(() => {
    loadMatches();
    loadStats();
  }, []);

  const loadMatches = async () => {
    setLoading(true);
    try {
      const response = await opportunitiesService.getMatches(30);
      if (response.success && response.data) {
        setJobs(response.data.jobs || []);
        setHackathons(response.data.hackathons || []);
      }
    } catch (error: any) {
      setMessage(error.message || 'Failed to load opportunities');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await opportunitiesService.getStats();
      if (response.success) {
        setStats(response.stats);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    setMessage('🔍 Scanning for opportunities...');
    
    try {
      const result = await opportunitiesService.scanOpportunities();
      
      if (result.success) {
        setMessage(
          `✅ ${result.message} - Found ${result.data.job_matches} jobs and ${result.data.hackathon_matches} hackathons!`
        );
        await loadMatches();
        await loadStats();
      } else {
        setMessage(`❌ ${result.message}`);
      }
    } catch (error: any) {
      setMessage(`❌ Scan failed: ${error.message}`);
    } finally {
      setScanning(false);
    }
  };

  const handleStatusUpdate = async (matchId: number, status: string) => {
    try {
      await opportunitiesService.updateJobStatus(matchId, status as any);
      setMessage(`✅ Status updated to ${status}`);
      await loadMatches();
      await loadStats();
    } catch (error: any) {
      setMessage(`❌ ${error.message}`);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-500/20 text-green-400';
    if (score >= 60) return 'bg-yellow-500/20 text-yellow-400';
    return 'bg-orange-500/20 text-orange-400';
  };

  const formatSalary = (min?: number, max?: number, currency?: string) => {
    if (!min && !max) return null;
    const curr = currency || 'INR';
    if (min && max) return `${curr} ${min.toLocaleString()} - ${max.toLocaleString()}`;
    if (min) return `${curr} ${min.toLocaleString()}+`;
    if (max) return `Up to ${curr} ${max.toLocaleString()}`;
    return null;
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
          <h2 className="text-3xl font-light mb-2">Job Opportunities</h2>
          <p className="text-white/60">AI-powered matching based on your profile</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowResumeUpload(true)}
            className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-2xl flex items-center gap-3 transition-all border border-white/10"
          >
            <Upload size={20} />
            Update Resume
          </button>
          <button
            onClick={handleScan}
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
      </div>

      {/* Message Banner */}
      {message && (
        <div className={`p-4 rounded-2xl border ${
          message.includes('❌') 
            ? 'bg-red-500/10 border-red-500/30 text-red-400' 
            : message.includes('✅')
            ? 'bg-green-500/10 border-green-500/30 text-green-400'
            : 'bg-blue-500/10 border-blue-500/30 text-blue-400'
        }`}>
          <div className="flex items-center justify-between">
            <span>{message}</span>
            <button 
              onClick={() => setMessage('')}
              className="text-white/40 hover:text-white/80"
            >
              <X size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <div className="text-3xl font-light mb-1 text-primary">{stats.total_matches}</div>
          <div className="text-sm text-white/40">Total Matches</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <div className="text-3xl font-light mb-1 text-green-400">{stats.applied}</div>
          <div className="text-sm text-white/40">Applied</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <div className="text-3xl font-light mb-1 text-yellow-400">{stats.saved}</div>
          <div className="text-sm text-white/40">Saved</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <div className="text-3xl font-light mb-1 text-blue-400">{hackathons.length}</div>
          <div className="text-sm text-white/40">Hackathons</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-white/10">
        <button
          onClick={() => setActiveTab('jobs')}
          className={`px-6 py-3 font-medium transition-all ${
            activeTab === 'jobs'
              ? 'text-primary border-b-2 border-primary'
              : 'text-white/60 hover:text-white/80'
          }`}
        >
          <div className="flex items-center gap-2">
            <Briefcase size={20} />
            Jobs ({jobs.length})
          </div>
        </button>
        <button
          onClick={() => setActiveTab('hackathons')}
          className={`px-6 py-3 font-medium transition-all ${
            activeTab === 'hackathons'
              ? 'text-primary border-b-2 border-primary'
              : 'text-white/60 hover:text-white/80'
          }`}
        >
          <div className="flex items-center gap-2">
            <Trophy size={20} />
            Hackathons ({hackathons.length})
          </div>
        </button>
      </div>

      {/* Content */}
      <div className="space-y-4">
        {activeTab === 'jobs' ? (
          jobs.length === 0 ? (
            <div className="text-center py-20 bg-white/5 border border-white/10 rounded-[3rem]">
              <Briefcase size={80} className="mx-auto mb-8 text-white/20" />
              <h3 className="text-2xl font-light mb-4">No Opportunities Found</h3>
              <p className="text-white/60 mb-8 max-w-md mx-auto">
                Click "Scan Opportunities" to discover jobs matching your profile
              </p>
              <button
                onClick={handleScan}
                disabled={scanning}
                className="px-8 py-4 bg-primary text-bg-deep rounded-2xl font-bold flex items-center gap-3 mx-auto hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all"
              >
                <Sparkles size={20} />
                Start Scanning
              </button>
            </div>
          ) : (
            jobs.map((job) => (
              <div
                key={job.id}
                className="bg-white/5 border border-white/10 rounded-[2rem] p-6 hover:bg-white/10 transition-all group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-medium group-hover:text-primary transition-colors">
                        {job.title}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${getScoreColor(job.match_score)}`}>
                        {Math.round(job.match_score)}% Match
                      </span>
                      {job.is_remote && (
                        <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs font-bold">
                          Remote
                        </span>
                      )}
                    </div>
                    
                    <p className="text-white/60 mb-3">{job.company}</p>
                    
                    <div className="flex items-center gap-4 text-sm text-white/40 mb-4">
                      <div className="flex items-center gap-2">
                        <MapPin size={16} />
                        <span>{job.location}</span>
                      </div>
                      {job.experience_level && <span>📊 {job.experience_level}</span>}
                      {job.source && (
                        <span className="text-xs bg-white/5 px-2 py-1 rounded">
                          via {job.source}
                        </span>
                      )}
                    </div>

                    {/* Salary */}
                    {formatSalary(job.salary_min, job.salary_max, job.salary_currency) && (
                      <div className="mb-3 text-green-400 font-medium">
                        💰 {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
                      </div>
                    )}

                    {job.description && (
                      <p className="text-white/70 mb-4 line-clamp-2">{job.description}</p>
                    )}

                    {/* Skills */}
                    {job.matching_skills && job.matching_skills.length > 0 && (
                      <div className="mb-4">
                        <p className="text-xs text-white/40 mb-2">Matching Skills</p>
                        <div className="flex flex-wrap gap-2">
                          {job.matching_skills.slice(0, 5).map((skill, i) => (
                            <span key={i} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-xs">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {job.missing_skills && job.missing_skills.length > 0 && (
                      <div className="mb-4">
                        <p className="text-xs text-white/40 mb-2">Skills to Learn</p>
                        <div className="flex flex-wrap gap-2">
                          {job.missing_skills.slice(0, 3).map((skill, i) => (
                            <span key={i} className="px-3 py-1 bg-yellow-500/10 text-yellow-400 rounded-full text-xs">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 pt-4 border-t border-white/10">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl flex items-center gap-2 transition-all"
                  >
                    <ExternalLink size={16} />
                    Apply Now
                  </a>
                  
                  <button
                    onClick={() => handleStatusUpdate(job.match_id, 'saved')}
                    className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl flex items-center gap-2 transition-all"
                  >
                    <Save size={16} />
                    Save
                  </button>
                  
                  <button
                    onClick={() => handleStatusUpdate(job.match_id, 'applied')}
                    className="px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-xl flex items-center gap-2 transition-all"
                  >
                    <CheckCircle size={16} />
                    Applied
                  </button>

                  <span className={`ml-auto px-3 py-1 rounded-full text-xs font-medium ${
                    job.status === 'applied' ? 'bg-green-500/20 text-green-400' :
                    job.status === 'saved' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-white/10 text-white/60'
                  }`}>
                    {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                  </span>
                </div>
              </div>
            ))
          )
        ) : (
          // Hackathons tab - similar styling
          hackathons.length === 0 ? (
            <div className="text-center py-20 bg-white/5 border border-white/10 rounded-[3rem]">
              <Trophy size={80} className="mx-auto mb-8 text-white/20" />
              <h3 className="text-2xl font-light mb-4">No Hackathons Found</h3>
              <p className="text-white/60 mb-8 max-w-md mx-auto">
                Scan to discover exciting hackathon opportunities
              </p>
            </div>
          ) : (
            hackathons.map((hack) => (
              <div
                key={hack.id}
                className="bg-white/5 border border-white/10 rounded-[2rem] p-6 hover:bg-white/10 transition-all"
              >
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-medium">{hack.title}</h3>
                  <span className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-sm font-medium">
                    {hack.platform}
                  </span>
                </div>
                
                <div className="flex items-center gap-4 text-white/60 mb-3">
                  <span>🎯 {hack.organizer}</span>
                  <span>💰 {hack.prize_pool}</span>
                  {hack.mode && (
                    <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                      {hack.mode}
                    </span>
                  )}
                </div>

                {hack.description && (
                  <p className="text-white/70 mb-3">{hack.description}</p>
                )}

                {hack.themes && hack.themes.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {hack.themes.map((theme, i) => (
                      <span key={i} className="px-3 py-1 bg-indigo-500/20 text-indigo-400 rounded-full text-sm">
                        {theme}
                      </span>
                    ))}
                  </div>
                )}

                <a
                  href={hack.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block px-4 py-2 bg-primary text-bg-deep rounded-xl hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all"
                >
                  Register Now →
                </a>
              </div>
            ))
          )
        )}
      </div>

      {/* Resume Upload Modal */}
      {showResumeUpload && <ResumeUploadModal onClose={() => setShowResumeUpload(false)} />}
    </div>
  );
};

// Resume Upload Modal Component
const ResumeUploadModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await resumeService.uploadResume(file);
      alert('Resume uploaded successfully!');
      onClose();
    } catch (error) {
      alert('Failed to upload resume');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-bg-deep border border-white/10 rounded-[2rem] p-6 max-w-lg w-full">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-light">Upload Resume</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-all">
            <X size={24} />
          </button>
        </div>

        <div className="border-2 border-dashed border-white/20 rounded-2xl p-8 text-center hover:border-white/40 transition-all">
          {file ? (
            <div className="space-y-2">
              <File size={48} className="mx-auto text-primary" />
              <p className="text-white/90 font-medium">{file.name}</p>
              <p className="text-sm text-white/60">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <button
                onClick={() => setFile(null)}
                className="text-sm text-red-400 hover:text-red-300"
              >
                Remove
              </button>
            </div>
          ) : (
            <>
              <Upload size={48} className="mx-auto mb-4 text-white/40" />
              <p className="text-white/80 mb-4">Drag & drop or browse</p>
              <label className="px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl inline-flex items-center gap-2 cursor-pointer">
                <File size={20} />
                Browse Files
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => e.target.files && setFile(e.target.files[0])}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-white/40 mt-4">PDF, DOC, DOCX (Max 10MB)</p>
            </>
          )}
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="flex-1 px-6 py-3 bg-primary text-bg-deep rounded-xl font-bold hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
          >
            {uploading ? 'Uploading...' : 'Upload Resume'}
          </button>
          <button
            onClick={onClose}
            className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default OpportunitiesModule;
