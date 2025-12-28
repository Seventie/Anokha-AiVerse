// frontend/components/Dashboard/ResumeModule.tsx - WITH MULTIPLE RESUME SUPPORT

import React, { useState, useEffect } from 'react';
import { 
  resumeService, 
  type ResumeData, 
  type ResumeAnalysis,
  type ATSScore,
  type JDAnalysis 
} from '../../services/resumeService';
import { 
  FileText, Upload, Loader2, CheckCircle, 
  AlertCircle, TrendingUp, Target, Lightbulb,
  Code, X, RefreshCw, Sparkles, Trash2, 
  Plus, ChevronDown, GitCompare
} from 'lucide-react';

const ResumeModule: React.FC = () => {
  const [allResumes, setAllResumes] = useState<ResumeData[]>([]);
  const [currentResume, setCurrentResume] = useState<ResumeData | null>(null);
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadingFile, setUploadingFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState('');
  const [showJDInput, setShowJDInput] = useState(false);
  const [showUploadSection, setShowUploadSection] = useState(false);
  const [showResumeDropdown, setShowResumeDropdown] = useState(false);
  const [message, setMessage] = useState('');
  const [compareMode, setCompareMode] = useState(false);
  const [compareResume, setCompareResume] = useState<ResumeData | null>(null);

  useEffect(() => {
    loadAllResumes();
  }, []);

  const loadAllResumes = async () => {
  setLoading(true);
  try {
    const resumes = await resumeService.getAllResumes();
    setAllResumes(resumes);
    
    if (resumes.length > 0) {
      const active = resumes.find(r => r.is_active) || resumes[0];
      setCurrentResume(active);
      await analyzeResume(active.id); // This will now work
    } else {
      setShowUploadSection(true); // Show upload if no resumes
    }
  } catch (error: any) {
    console.error('Failed to load resumes:', error);
    setShowUploadSection(true);
  } finally {
    setLoading(false);
  }
};

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadingFile(file);
    }
  };

  const handleUpload = async () => {
    if (!uploadingFile) return;

    setLoading(true);
    setMessage('📤 Uploading and analyzing resume...');

    try {
      await resumeService.uploadResume(uploadingFile, jdText || undefined);
      setMessage('✅ Resume uploaded successfully!');
      setUploadingFile(null);
      setJdText('');
      setShowJDInput(false);
      setShowUploadSection(false);
      
      await loadAllResumes();
    } catch (error: any) {
      setMessage(`❌ Upload failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const analyzeResume = async (resumeId?: string) => {
    const targetResumeId = resumeId || currentResume?.id;
    if (!targetResumeId) return;

    setAnalyzing(true);
    setMessage('🤖 Analyzing resume with AI...');

    try {
      const result = await resumeService.analyzeResume(targetResumeId, jdText || undefined);
      setAnalysis(result.data);
      setMessage('✅ Analysis complete!');
    } catch (error: any) {
      setMessage(`❌ Analysis failed: ${error.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDeleteResume = async (resumeId: string) => {
    if (confirm('Are you sure you want to delete this resume?')) {
      try {
        await resumeService.deleteResume(resumeId);
        setMessage('✅ Resume deleted successfully');
        
        // If deleted current resume, switch to another
        if (currentResume?.id === resumeId) {
          setCurrentResume(null);
          setAnalysis(null);
        }
        
        await loadAllResumes();
      } catch (error: any) {
        setMessage(`❌ Failed to delete: ${error.message}`);
      }
    }
  };

  const handleSwitchResume = async (resume: ResumeData) => {
    setCurrentResume(resume);
    setShowResumeDropdown(false);
    await analyzeResume(resume.id);
  };

  const handleSetActive = async (resumeId: string) => {
    try {
      await resumeService.setActiveResume(resumeId);
      setMessage('✅ Active resume updated');
      await loadAllResumes();
    } catch (error: any) {
      setMessage(`❌ Failed to set active: ${error.message}`);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'bg-green-500/20 text-green-400';
    if (score >= 70) return 'bg-yellow-500/20 text-yellow-400';
    return 'bg-red-500/20 text-red-400';
  };

  const renderATSScore = (atsScore: ATSScore, label?: string) => (
    <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
      <h3 className="text-xl font-medium mb-6 flex items-center gap-2">
        <TrendingUp size={24} className="text-primary" />
        {label || 'ATS Score'}
      </h3>
      
      <div className="flex items-center justify-between mb-6 p-6 bg-white/5 rounded-2xl">
        <div>
          <div className={`text-5xl font-light mb-2 ${getScoreColor(atsScore.overall_score)}`}>
            {atsScore.overall_score}
            <span className="text-2xl text-white/40">/100</span>
          </div>
          <div className="text-lg font-medium">
            Grade: <span className="text-primary">{atsScore.grade}</span>
          </div>
        </div>
        <div className="text-right max-w-xs">
          <p className="text-white/70">{atsScore.message}</p>
        </div>
      </div>

      <div className="space-y-4">
        {Object.entries(atsScore.breakdown).map(([key, value]) => (
          <div key={key}>
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium capitalize text-white/80">
                {key.replace('_', ' ')}
              </span>
              <span className="font-semibold text-primary">{value}%</span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  value >= 20 ? 'bg-green-500' : 
                  value >= 10 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${(value / 25) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderSuggestions = () => {
    if (!analysis?.suggestions) return null;

    const { strengths, weaknesses, improvements } = analysis.suggestions;

    return (
      <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
        <h3 className="text-xl font-medium mb-6 flex items-center gap-2">
          <Lightbulb size={24} className="text-primary" />
          AI Recommendations
        </h3>

        <div className="mb-6">
          <h4 className="font-medium text-green-400 mb-3 flex items-center gap-2">
            <CheckCircle size={18} />
            Strengths
          </h4>
          <ul className="space-y-2">
            {strengths.map((strength, idx) => (
              <li key={idx} className="flex items-start gap-3 text-white/70">
                <span className="text-green-400 mt-1">•</span>
                <span>{strength}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="mb-6">
          <h4 className="font-medium text-orange-400 mb-3 flex items-center gap-2">
            <AlertCircle size={18} />
            Areas to Improve
          </h4>
          <ul className="space-y-2">
            {weaknesses.map((weakness, idx) => (
              <li key={idx} className="flex items-start gap-3 text-white/70">
                <span className="text-orange-400 mt-1">•</span>
                <span>{weakness}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="font-medium text-blue-400 mb-3 flex items-center gap-2">
            <Sparkles size={18} />
            Action Items
          </h4>
          <ul className="space-y-2">
            {improvements.map((improvement, idx) => (
              <li key={idx} className="flex items-start gap-3 text-white/70">
                <span className="text-blue-400 mt-1">{idx + 1}.</span>
                <span>{improvement}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const renderProjectSuggestions = () => {
    if (!analysis?.project_suggestions?.length) return null;

    return (
      <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
        <h3 className="text-xl font-medium mb-6 flex items-center gap-2">
          <Code size={24} className="text-primary" />
          Recommended Projects to Build
        </h3>
        
        <div className="space-y-4">
          {analysis.project_suggestions.map((project, idx) => (
            <div key={idx} className="bg-white/5 border border-white/10 rounded-2xl p-4 hover:bg-white/10 transition-all">
              <h4 className="font-bold text-lg text-purple-400 mb-2">
                {project.name}
              </h4>
              <p className="text-white/70 mb-3">{project.description}</p>
              
              <div className="mb-3">
                <span className="text-sm font-medium text-white/60">Technologies:</span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {project.technologies.map((tech, i) => (
                    <span key={i} className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-3">
                <span className="text-sm font-medium text-green-400">Why it matters:</span>
                <p className="text-sm text-white/70 mt-1">{project.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderJDAnalysis = (jdAnalysis: JDAnalysis) => (
    <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
      <h3 className="text-xl font-medium mb-6 flex items-center gap-2">
        <Target size={24} className="text-primary" />
        Job Description Match
      </h3>

      <div className="flex items-center gap-4 mb-6 p-6 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-2xl border border-white/10">
        <div className={`text-5xl font-light ${getScoreColor(jdAnalysis.match_score)}`}>
          {jdAnalysis.match_score}%
        </div>
        <div>
          <p className="font-medium text-white/90 text-lg">Job Match Score</p>
          <p className="text-sm text-white/60">
            {jdAnalysis.match_score >= 80 ? 'Excellent fit!' :
             jdAnalysis.match_score >= 60 ? 'Good match with improvements' :
             'Needs significant updates'}
          </p>
        </div>
      </div>

      <div className="mb-6">
        <h4 className="font-medium text-green-400 mb-3 flex items-center gap-2">
          <CheckCircle size={18} />
          Your Matching Skills
        </h4>
        <div className="flex flex-wrap gap-2">
          {jdAnalysis.matching_keywords.slice(0, 15).map((kw, idx) => (
            <span key={idx} className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">
              {kw}
            </span>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <h4 className="font-medium text-red-400 mb-3 flex items-center gap-2">
          <X size={18} />
          Missing Keywords
        </h4>
        <div className="flex flex-wrap gap-2">
          {jdAnalysis.missing_keywords.slice(0, 10).map((kw, idx) => (
            <span key={idx} className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm">
              {kw}
            </span>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <h4 className="font-medium text-blue-400 mb-3">🔧 Recommended Edits</h4>
        <ul className="space-y-2">
          {jdAnalysis.recommended_changes.map((change, idx) => (
            <li key={idx} className="flex items-start gap-3 text-white/70">
              <span className="text-blue-400 mt-1">{idx + 1}.</span>
              <span>{change}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="bg-purple-500/10 border border-purple-500/30 rounded-2xl p-4">
        <h4 className="font-medium text-purple-400 mb-3">🔑 Critical ATS Keywords to Add</h4>
        <div className="flex flex-wrap gap-2 mb-3">
          {jdAnalysis.ats_keywords.map((kw, idx) => (
            <span key={idx} className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-sm font-medium">
              {kw}
            </span>
          ))}
        </div>
        <p className="text-xs text-white/60">
          💡 Add these keywords naturally in your experience and skills sections to boost ATS ranking
        </p>
      </div>
    </div>
  );

  if (loading && allResumes.length === 0) {
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
          <h2 className="text-3xl font-light mb-2">Resume Optimizer</h2>
          <p className="text-white/60">AI-powered resume analysis and ATS optimization</p>
        </div>
        <button
          onClick={() => setShowUploadSection(!showUploadSection)}
          className="px-6 py-3 bg-primary text-bg-deep rounded-2xl font-bold flex items-center gap-2
                   hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all"
        >
          <Plus size={20} />
          Upload New Resume
        </button>
      </div>

      {/* Message Banner */}
      {message && (
        <div className={`p-4 rounded-2xl border ${
          message.includes('❌') ? 'bg-red-500/10 border-red-500/30 text-red-400' :
          message.includes('✅') ? 'bg-green-500/10 border-green-500/30 text-green-400' :
          'bg-blue-500/10 border-blue-500/30 text-blue-400'
        }`}>
          <div className="flex items-center justify-between">
            <span>{message}</span>
            <button onClick={() => setMessage('')} className="text-white/40 hover:text-white/80">
              <X size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Upload Section (Collapsible) */}
      {showUploadSection && (
        <div className="bg-white/5 border border-white/10 rounded-[3rem] p-8">
          <h3 className="text-2xl font-light mb-6 flex items-center gap-3">
            <Upload size={28} className="text-primary" />
            Upload New Resume
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Select Resume (PDF, DOCX, TXT)
              </label>
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileSelect}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white/90
                         file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0
                         file:bg-primary file:text-bg-deep file:font-medium
                         hover:bg-white/20 transition-all"
              />
            </div>

            {uploadingFile && (
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                <div className="flex items-center gap-3 mb-4">
                  <FileText size={24} className="text-primary" />
                  <div className="flex-1">
                    <p className="font-medium text-white/90">{uploadingFile.name}</p>
                    <p className="text-sm text-white/60">
                      {(uploadingFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={() => setUploadingFile(null)}
                    className="p-2 hover:bg-white/10 rounded-lg transition-all"
                  >
                    <X size={20} className="text-white/60" />
                  </button>
                </div>
                
                <button
                  onClick={() => setShowJDInput(!showJDInput)}
                  className="text-sm text-primary hover:text-primary/80 font-medium mb-3"
                >
                  {showJDInput ? '− Hide' : '+ Compare with Job Description'}
                </button>

                {showJDInput && (
                  <textarea
                    value={jdText}
                    onChange={(e) => setJdText(e.target.value)}
                    placeholder="Paste the job description here to get JD-specific analysis..."
                    rows={6}
                    className="w-full mb-3 px-4 py-3 bg-white/10 border border-white/20 rounded-xl 
                             text-white/90 placeholder-white/40 focus:outline-none focus:border-primary/50"
                  />
                )}

                <button
                  onClick={handleUpload}
                  disabled={loading}
                  className="w-full px-6 py-3 bg-primary text-bg-deep rounded-xl font-bold
                           hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all 
                           disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 size={20} className="animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload size={20} />
                      Upload & Analyze
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Resume Selector & Current Resume Info */}
      {currentResume && (
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4 flex-1">
              <FileText size={40} className="text-primary" />
              
              {/* Resume Dropdown */}
              <div className="flex-1 relative">
                <button
                  onClick={() => setShowResumeDropdown(!showResumeDropdown)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-white/10 
                           hover:bg-white/20 rounded-xl transition-all border border-white/20"
                >
                  <div className="text-left">
                    <p className="font-medium text-white/90">{currentResume.filename}</p>
                    <p className="text-sm text-white/60">
                      Uploaded {new Date(currentResume.uploaded_at).toLocaleDateString()}
                      {currentResume.is_active && (
                        <span className="ml-2 px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs">
                          Active
                        </span>
                      )}
                    </p>
                  </div>
                  <ChevronDown size={20} className={`text-white/60 transition-transform ${
                    showResumeDropdown ? 'rotate-180' : ''
                  }`} />
                </button>

                {/* Dropdown Menu */}
                {showResumeDropdown && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-bg-deep border border-white/20 
                                rounded-xl shadow-2xl z-50 max-h-80 overflow-y-auto">
                    <div className="p-2">
                      <p className="px-3 py-2 text-xs text-white/40 font-medium">
                        Your Resumes ({allResumes.length})
                      </p>
                      {allResumes.map((resume) => (
                        <div
                          key={resume.id}
                          className={`flex items-center justify-between px-3 py-2 rounded-lg 
                                   hover:bg-white/10 transition-all cursor-pointer group ${
                            currentResume.id === resume.id ? 'bg-white/10' : ''
                          }`}
                          onClick={() => handleSwitchResume(resume)}
                        >
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white/90">{resume.filename}</p>
                            <p className="text-xs text-white/50">
                              {new Date(resume.uploaded_at).toLocaleDateString()}
                            </p>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {resume.is_active && (
                              <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">
                                Active
                              </span>
                            )}
                            {!resume.is_active && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleSetActive(resume.id);
                                }}
                                className="px-2 py-1 bg-primary/20 hover:bg-primary/30 text-primary 
                                         rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                Set Active
                              </button>
                            )}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteResume(resume.id);
                              }}
                              className="p-1 hover:bg-red-500/20 rounded transition-all opacity-0 
                                       group-hover:opacity-100"
                            >
                              <Trash2 size={14} className="text-red-400" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowJDInput(!showJDInput)}
                className="px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 
                         rounded-xl transition-all"
              >
                {showJDInput ? 'Hide JD' : '+ Compare with JD'}
              </button>
              
              <button
                onClick={() => analyzeResume()}
                disabled={analyzing}
                className="px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary 
                         rounded-xl transition-all disabled:opacity-50 flex items-center gap-2"
              >
                <RefreshCw size={18} className={analyzing ? 'animate-spin' : ''} />
                {analyzing ? 'Analyzing...' : 'Re-analyze'}
              </button>

              {allResumes.length > 1 && (
                <button
                  onClick={() => setCompareMode(!compareMode)}
                  className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 
                           rounded-xl transition-all flex items-center gap-2"
                >
                  <GitCompare size={18} />
                  {compareMode ? 'Exit Compare' : 'Compare'}
                </button>
              )}
            </div>
          </div>

          {showJDInput && (
            <div className="pt-6 border-t border-white/10">
              <label className="block text-sm font-medium text-white/80 mb-2">
                Job Description (Optional)
              </label>
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the job description here for JD-specific analysis..."
                rows={6}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl 
                         text-white/90 placeholder-white/40 focus:outline-none focus:border-primary/50"
              />
              <button
                onClick={() => analyzeResume()}
                disabled={analyzing}
                className="mt-3 px-6 py-3 bg-primary text-bg-deep rounded-xl font-bold
                         hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all 
                         disabled:opacity-50"
              >
                Analyze with JD
              </button>
            </div>
          )}
        </div>
      )}

      {/* Compare Mode - Select Second Resume */}
      {compareMode && allResumes.length > 1 && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-2xl p-4">
          <h4 className="font-medium text-blue-400 mb-3 flex items-center gap-2">
            <GitCompare size={20} />
            Select a resume to compare with
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {allResumes
              .filter(r => r.id !== currentResume?.id)
              .map((resume) => (
                <button
                  key={resume.id}
                  onClick={() => setCompareResume(resume)}
                  className={`p-3 rounded-xl border transition-all text-left ${
                    compareResume?.id === resume.id
                      ? 'bg-blue-500/20 border-blue-500 text-blue-400'
                      : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                >
                  <p className="text-sm font-medium truncate">{resume.filename}</p>
                  <p className="text-xs text-white/50 mt-1">
                    {new Date(resume.uploaded_at).toLocaleDateString()}
                  </p>
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analyzing ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 size={48} className="animate-spin text-primary" />
        </div>
      ) : analysis ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {renderATSScore(analysis.ats_score, compareMode ? `${currentResume?.filename} - ATS Score` : undefined)}
          {renderSuggestions()}
          
          <div className="lg:col-span-2">
            {renderProjectSuggestions()}
          </div>

          {analysis.jd_analysis && (
            <div className="lg:col-span-2">
              {renderJDAnalysis(analysis.jd_analysis)}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};

export default ResumeModule;
