// frontend/components/Dashboard/ResumeModule.tsx

import React, { useState } from 'react';
import { User } from '../../services/authService';
import { agentService } from '../../services/agentService';
import { 
  FileText, Upload, Sparkles, TrendingUp, 
  AlertCircle, CheckCircle, Loader2, Download,
  Target, Zap, Edit3, Copy
} from 'lucide-react';

interface ResumeModuleProps {
  user: User;
}

const ResumeModule: React.FC<ResumeModuleProps> = ({ user }) => {
  const [resumeText, setResumeText] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [analysis, setAnalysis] = useState<any>(null);
  const [optimizedResume, setOptimizedResume] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'analyze' | 'optimize'>('analyze');

  const handleAnalyze = async () => {
    if (!resumeText.trim()) {
      alert('Please paste your resume text');
      return;
    }

    setLoading(true);
    try {
      const result = await agentService.analyzeResume(user.id, resumeText);
      setAnalysis(result);
    } catch (error) {
      console.error('Failed to analyze:', error);
      alert('Failed to analyze resume');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!resumeText.trim()) {
      alert('Please paste your resume text');
      return;
    }
    if (!jobDescription.trim()) {
      alert('Please paste the job description');
      return;
    }

    setLoading(true);
    try {
      const result = await agentService.optimizeResume(user.id, jobDescription);
      setOptimizedResume(result.optimized_resume || '');
      setAnalysis(result);
    } catch (error) {
      console.error('Failed to optimize:', error);
      alert('Failed to optimize resume');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Resume Intelligence</h2>
          <p className="text-white/60">Analyze and optimize your resume</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setMode('analyze')}
            className={`px-6 py-3 rounded-2xl font-medium transition-all ${
              mode === 'analyze'
                ? 'bg-primary/20 text-primary border border-primary/30'
                : 'bg-white/5 text-white/60 hover:bg-white/10'
            }`}
          >
            Analyze
          </button>
          <button
            onClick={() => setMode('optimize')}
            className={`px-6 py-3 rounded-2xl font-medium transition-all ${
              mode === 'optimize'
                ? 'bg-primary/20 text-primary border border-primary/30'
                : 'bg-white/5 text-white/60 hover:bg-white/10'
            }`}
          >
            Optimize
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Input Section */}
        <div className="space-y-6">
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
              <FileText size={20} className="text-primary" />
              Resume Text
            </h3>
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your resume text here..."
              className="w-full h-64 bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder-white/30 resize-none focus:outline-none focus:border-primary/50"
            />
          </div>

          {mode === 'optimize' && (
            <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                <Target size={20} className="text-primary" />
                Job Description
              </h3>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the job description here..."
                className="w-full h-48 bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder-white/30 resize-none focus:outline-none focus:border-primary/50"
              />
            </div>
          )}

          <button
            onClick={mode === 'analyze' ? handleAnalyze : handleOptimize}
            disabled={loading}
            className="w-full px-6 py-4 bg-primary text-bg-deep rounded-2xl font-bold flex items-center justify-center gap-3 hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                {mode === 'analyze' ? 'Analyzing...' : 'Optimizing...'}
              </>
            ) : (
              <>
                <Zap size={20} />
                {mode === 'analyze' ? 'Analyze Resume' : 'Optimize Resume'}
              </>
            )}
          </button>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {analysis && (
            <>
              {/* Score Card */}
              <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
                <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                  <TrendingUp size={20} className="text-primary" />
                  Resume Score
                </h3>
                <div className="flex items-center justify-center mb-4">
                  <div className="relative w-32 h-32">
                    <svg className="transform -rotate-90 w-32 h-32">
                      <circle
                        cx="64"
                        cy="64"
                        r="56"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        className="text-white/10"
                      />
                      <circle
                        cx="64"
                        cy="64"
                        r="56"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        strokeDasharray={`${(analysis.resume_score || 0) * 3.52} 352`}
                        className="text-primary"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-3xl font-bold text-primary">
                        {analysis.resume_score || 0}
                      </span>
                    </div>
                  </div>
                </div>
                <p className="text-center text-white/60 text-sm">Overall Quality Score</p>
              </div>

              {/* Strengths */}
              {analysis.strengths && analysis.strengths.length > 0 && (
                <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                    <CheckCircle size={20} className="text-green-400" />
                    Strengths
                  </h3>
                  <ul className="space-y-2">
                    {analysis.strengths.map((strength: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-3 text-white/80">
                        <CheckCircle size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Weaknesses */}
              {analysis.weaknesses && analysis.weaknesses.length > 0 && (
                <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                    <AlertCircle size={20} className="text-yellow-400" />
                    Areas for Improvement
                  </h3>
                  <ul className="space-y-2">
                    {analysis.weaknesses.map((weakness: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-3 text-white/80">
                        <AlertCircle size={16} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span>{weakness}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Suggestions */}
              {analysis.suggestions && analysis.suggestions.length > 0 && (
                <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                    <Sparkles size={20} className="text-primary" />
                    Optimization Suggestions
                  </h3>
                  <div className="space-y-3">
                    {analysis.suggestions.slice(0, 5).map((suggestion: any, idx: number) => (
                      <div key={idx} className="p-3 bg-white/5 rounded-xl">
                        <p className="text-sm text-white/80">{suggestion.suggestion || suggestion}</p>
                        {suggestion.section && (
                          <p className="text-xs text-white/40 mt-1">Section: {suggestion.section}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Optimized Resume */}
              {optimizedResume && (
                <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium flex items-center gap-3">
                      <FileText size={20} className="text-primary" />
                      Optimized Resume
                    </h3>
                    <button
                      onClick={() => copyToClipboard(optimizedResume)}
                      className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded-xl flex items-center gap-2 text-sm transition-all"
                    >
                      <Copy size={14} />
                      Copy
                    </button>
                  </div>
                  <div className="bg-white/5 rounded-xl p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm text-white/80 whitespace-pre-wrap font-sans">
                      {optimizedResume}
                    </pre>
                  </div>
                </div>
              )}
            </>
          )}

          {!analysis && (
            <div className="bg-white/5 border border-white/10 rounded-[2rem] p-12 text-center">
              <FileText size={48} className="mx-auto mb-4 text-white/20" />
              <p className="text-white/60">
                {mode === 'analyze' 
                  ? 'Paste your resume and click "Analyze Resume" to get started'
                  : 'Paste your resume and job description, then click "Optimize Resume"'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResumeModule;

