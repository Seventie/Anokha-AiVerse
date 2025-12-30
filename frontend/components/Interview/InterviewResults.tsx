// frontend/src/components/Interview/InterviewResults.tsx

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, Download, CheckCircle, XCircle, AlertCircle, 
  TrendingUp, Target, Award, MessageSquare, Loader,
  ChevronDown, ChevronUp
} from 'lucide-react';

interface Props {
  interviewId: string;
  onClose: () => void;
}

interface DetailedResults {
  interview: {
    id: string;
    company_name: string;
    duration_seconds: number;
    verdict: {
      label: string;
      color: string;
      icon: string;
      message: string;
    };
  };
  scores: {
    overall: number;
    technical: number;
    communication: number;
    problem_solving: number;
    confidence: number;
  };
  qa_breakdown: Array<{
    question_id: number;
    question: string;
    category: string;
    answer: string;
    score: number;
    confidence: string;
    feedback: string;
    strengths: string[];
    improvements: string[];
    audio_url?: string;
    answer_audio_url?: string;
  }>;
  skill_gaps: Array<{
    skill: string;
    severity: string;
    recommended_action: string;
  }>;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  recording: {
    video_url?: string;
    duration?: number;
  };
}

const InterviewResults: React.FC<Props> = ({ interviewId, onClose }) => {
  const [results, setResults] = useState<DetailedResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'questions' | 'gaps' | 'video'>('overview');
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set());
  
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    loadResults();
  }, []);

  const loadResults = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/interview/${interviewId}/detailed-results`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('auth_token')}`
          }
        }
      );
      
      if (!response.ok) throw new Error('Failed to load results');
      
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Failed to load results:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleQuestion = (questionId: number) => {
    const newExpanded = new Set(expandedQuestions);
    if (newExpanded.has(questionId)) {
      newExpanded.delete(questionId);
    } else {
      newExpanded.add(questionId);
    }
    setExpandedQuestions(newExpanded);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-500/20 border-green-500/40';
    if (score >= 60) return 'bg-yellow-500/20 border-yellow-500/40';
    return 'bg-red-500/20 border-red-500/40';
  };

  const getVerdictStyles = (color: string) => {
    const styles = {
      green: 'bg-green-500/10 border-green-500/50 text-green-400',
      blue: 'bg-blue-500/10 border-blue-500/50 text-blue-400',
      yellow: 'bg-yellow-500/10 border-yellow-500/50 text-yellow-400',
      red: 'bg-red-500/10 border-red-500/50 text-red-400'
    };
    return styles[color as keyof typeof styles] || styles.blue;
  };

  const downloadReport = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/interview/${interviewId}/report`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      if (!response.ok) throw new Error('Failed to download report');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `interview-report-${interviewId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download report:', error);
      alert('Report download coming soon!');
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b1714] flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader className="w-10 h-10 animate-spin text-primary mx-auto" />
          <p className="text-white/70">Loading your results...</p>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="min-h-screen bg-[#0b1714] flex items-center justify-center">
        <div className="text-center text-red-400">
          <XCircle className="w-16 h-16 mx-auto mb-4" />
          <p>Failed to load interview results</p>
          <button
            onClick={onClose}
            className="mt-4 px-6 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b1714] text-white py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">Interview Results</h1>
            <p className="text-white/60">
              {results.interview.company_name || 'Mock Interview'} • {formatDuration(results.interview.duration_seconds)}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={downloadReport}
              className="px-6 py-3 bg-white/10 text-white rounded-xl hover:bg-white/20 transition-colors flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              Download Report
            </button>
            <button
              onClick={onClose}
              className="px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary/90 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>

        {/* 🔥 VERDICT BANNER */}
        <div className={`mb-8 p-8 rounded-3xl border-2 ${getVerdictStyles(results.interview.verdict.color)}`}>
          <div className="flex items-center gap-4">
            <div className="text-6xl">{results.interview.verdict.icon}</div>
            <div className="flex-1">
              <h2 className="text-3xl font-bold mb-2">{results.interview.verdict.label}</h2>
              <p className="text-lg opacity-80">{results.interview.verdict.message}</p>
            </div>
            <div className="text-right">
              <div className="text-5xl font-bold">{Math.round(results.scores.overall)}</div>
              <div className="text-sm opacity-60">Overall Score</div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6 flex gap-2 border-b border-white/10 overflow-x-auto">
          {[
            { id: 'overview', label: 'Overview', icon: TrendingUp },
            { id: 'questions', label: 'Q&A Breakdown', icon: MessageSquare },
            { id: 'gaps', label: 'Skill Gaps', icon: Target },
            { id: 'video', label: 'Recording', icon: Play }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as any)}
              className={`px-6 py-3 font-medium rounded-t-xl transition-colors flex items-center gap-2 whitespace-nowrap ${
                activeTab === id
                  ? 'bg-white/10 text-white border-b-2 border-primary'
                  : 'text-white/60 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <>
              {/* Score Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: 'Technical', score: results.scores.technical },
                  { label: 'Communication', score: results.scores.communication },
                  { label: 'Problem Solving', score: results.scores.problem_solving },
                  { label: 'Confidence', score: results.scores.confidence }
                ].map(({ label, score }) => (
                  <div key={label} className="p-6 bg-white/5 rounded-2xl border border-white/10">
                    <div className="text-sm text-white/60 mb-2">{label}</div>
                    <div className="flex items-baseline gap-2">
                      <div className={`text-4xl font-bold ${getScoreColor(score)}`}>
                        {Math.round(score)}
                      </div>
                      <div className="text-white/40">/100</div>
                    </div>
                    <div className="mt-3 w-full bg-white/10 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(score, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Strengths & Weaknesses */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="p-6 bg-green-500/10 rounded-2xl border border-green-500/30">
                  <h3 className="text-xl font-bold mb-4 text-green-400 flex items-center gap-2">
                    <CheckCircle className="w-6 h-6" />
                    Key Strengths
                  </h3>
                  {results.strengths.length > 0 ? (
                    <ul className="space-y-2">
                      {results.strengths.map((strength, i) => (
                        <li key={i} className="flex items-start gap-3 text-green-100">
                          <span className="text-green-400 mt-1">✓</span>
                          <span>{strength}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-green-200/60">No strengths identified yet.</p>
                  )}
                </div>

                <div className="p-6 bg-yellow-500/10 rounded-2xl border border-yellow-500/30">
                  <h3 className="text-xl font-bold mb-4 text-yellow-400 flex items-center gap-2">
                    <AlertCircle className="w-6 h-6" />
                    Areas for Improvement
                  </h3>
                  {results.weaknesses.length > 0 ? (
                    <ul className="space-y-2">
                      {results.weaknesses.map((weakness, i) => (
                        <li key={i} className="flex items-start gap-3 text-yellow-100">
                          <span className="text-yellow-400 mt-1">→</span>
                          <span>{weakness}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-yellow-200/60">No areas for improvement identified.</p>
                  )}
                </div>
              </div>

              {/* Recommendations */}
              <div className="p-6 bg-blue-500/10 rounded-2xl border border-blue-500/30">
                <h3 className="text-xl font-bold mb-4 text-blue-400 flex items-center gap-2">
                  <Award className="w-6 h-6" />
                  Personalized Recommendations
                </h3>
                {results.recommendations.length > 0 ? (
                  <div className="space-y-3">
                    {results.recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-semibold flex-shrink-0">
                          {i + 1}
                        </div>
                        <p className="text-blue-100 pt-1">{rec}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-blue-200/60">Complete the interview to get personalized recommendations.</p>
                )}
              </div>
            </>
          )}

          {/* QUESTIONS TAB */}
          {activeTab === 'questions' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold">Question-by-Question Analysis</h3>
                <p className="text-white/60">{results.qa_breakdown.length} questions asked</p>
              </div>

              {results.qa_breakdown.length === 0 ? (
                <div className="text-center py-12 text-white/60">
                  <MessageSquare className="w-16 h-16 mx-auto mb-4" />
                  <p>No questions answered yet</p>
                </div>
              ) : (
                results.qa_breakdown.map((qa, index) => {
                  const isExpanded = expandedQuestions.has(qa.question_id);
                  
                  return (
                    <div
                      key={qa.question_id}
                      className={`p-6 rounded-2xl border transition-all ${
                        isExpanded ? 'bg-white/10 border-white/20' : 'bg-white/5 border-white/10'
                      }`}
                    >
                      {/* Question Header */}
                      <div
                        className="flex items-start justify-between cursor-pointer"
                        onClick={() => toggleQuestion(qa.question_id)}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2 flex-wrap">
                            <span className="px-3 py-1 rounded-full bg-primary/20 text-primary text-xs font-semibold">
                              Q{index + 1}
                            </span>
                            <span className="px-3 py-1 rounded-full bg-white/10 text-white/60 text-xs">
                              {qa.category}
                            </span>
                            <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${getScoreBg(qa.score)}`}>
                              <span className={getScoreColor(qa.score)}>{Math.round(qa.score)}/100</span>
                            </div>
                          </div>
                          <p className="text-white font-medium">{qa.question}</p>
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-white/60 flex-shrink-0 ml-4" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-white/60 flex-shrink-0 ml-4" />
                        )}
                      </div>

                      {/* Expanded Content */}
                      {isExpanded && (
                        <div className="mt-6 space-y-4 border-t border-white/10 pt-4">
                          {/* Your Answer */}
                          <div>
                            <div className="text-sm text-white/50 mb-2">Your Answer:</div>
                            <div className="p-4 bg-black/20 rounded-xl text-white/90">
                              {qa.answer || 'No answer provided'}
                            </div>
                            {qa.answer_audio_url && (
                              <audio controls className="mt-2 w-full">
                                <source src={`${import.meta.env.VITE_API_URL}${qa.answer_audio_url}`} type="audio/wav" />
                              </audio>
                            )}
                          </div>

                          {/* Feedback */}
                          {qa.feedback && (
                            <div>
                              <div className="text-sm text-white/50 mb-2">AI Feedback:</div>
                              <p className="text-white/80">{qa.feedback}</p>
                            </div>
                          )}

                          {/* Strengths & Improvements */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {qa.strengths && qa.strengths.length > 0 && (
                              <div>
                                <div className="text-sm text-green-400 font-semibold mb-2">✓ Strengths:</div>
                                <ul className="space-y-1">
                                  {qa.strengths.map((s, i) => (
                                    <li key={i} className="text-sm text-green-200">• {s}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {qa.improvements && qa.improvements.length > 0 && (
                              <div>
                                <div className="text-sm text-yellow-400 font-semibold mb-2">→ Improvements:</div>
                                <ul className="space-y-1">
                                  {qa.improvements.map((imp, i) => (
                                    <li key={i} className="text-sm text-yellow-200">• {imp}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* SKILL GAPS TAB */}
          {activeTab === 'gaps' && (
            <div className="space-y-4">
              <h3 className="text-xl font-bold mb-4">Identified Skill Gaps</h3>
              
              {results.skill_gaps.length === 0 ? (
                <div className="text-center py-12 text-white/60">
                  <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
                  <p>No critical skill gaps identified!</p>
                </div>
              ) : (
                results.skill_gaps.map((gap, i) => (
                  <div
                    key={i}
                    className={`p-6 rounded-2xl border ${
                      gap.severity === 'critical'
                        ? 'bg-red-500/10 border-red-500/30'
                        : gap.severity === 'important'
                        ? 'bg-yellow-500/10 border-yellow-500/30'
                        : 'bg-blue-500/10 border-blue-500/30'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2 flex-wrap">
                          <h4 className="text-lg font-bold text-white">{gap.skill}</h4>
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              gap.severity === 'critical'
                                ? 'bg-red-500/20 text-red-300'
                                : gap.severity === 'important'
                                ? 'bg-yellow-500/20 text-yellow-300'
                                : 'bg-blue-500/20 text-blue-300'
                            }`}
                          >
                            {gap.severity}
                          </span>
                        </div>
                        <p className="text-white/70 mb-3">{gap.recommended_action}</p>
                        <button className="px-4 py-2 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors">
                          Find Learning Resources →
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* VIDEO TAB */}
          {activeTab === 'video' && (
            <div className="space-y-4">
              {results.recording.video_url ? (
                <div className="rounded-2xl overflow-hidden bg-black">
                  <video
                    ref={videoRef}
                    src={results.recording.video_url}
                    controls
                    className="w-full"
                  />
                </div>
              ) : (
                <div className="text-center py-12 text-white/60">
                  <Play className="w-16 h-16 mx-auto mb-4" />
                  <p>No recording available</p>
                  <p className="text-sm mt-2">Recording will be available after completing the interview</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InterviewResults;
