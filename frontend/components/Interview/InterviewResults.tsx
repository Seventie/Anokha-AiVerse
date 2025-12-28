// frontend/src/components/Interview/InterviewResults.tsx

import React, { useState, useEffect } from 'react';
import { interviewService } from '../../services/interviewService';
import { Download, Share2, ArrowLeft, Loader } from 'lucide-react';
import InterviewAnalytics from './InterviewAnalytics';

interface Props {
  interviewId: string;
  onBackHome: () => void;
}

const InterviewResults: React.FC<Props> = ({ interviewId, onBackHome }) => {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadResults();
  }, [interviewId]);

  const loadResults = async () => {
    try {
      setLoading(true);
      const data = await interviewService.getResults(interviewId);
      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      await interviewService.downloadReport(interviewId);
    } catch (err) {
      console.error('Failed to download report:', err);
    }
  };

  const handleShareResults = async () => {
    try {
      const url = `${window.location.origin}/interview-results/${interviewId}`;
      await navigator.clipboard.writeText(url);
      alert('Results link copied to clipboard!');
    } catch (err) {
      console.error('Failed to share results:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b1714] flex items-center justify-center">
        <Loader className="w-10 h-10 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b1714] text-white">
      <div className="max-w-[1400px] mx-auto px-8 md:px-24 py-12 space-y-10">
        {/* Header */}
        <div className="flex items-center justify-between gap-4">
          <button
            onClick={onBackHome}
            className="inline-flex items-center gap-2 text-sm font-light text-white/70 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Mock Interview Menu</span>
          </button>
          <span className="text-[11px] tracking-[0.3em] text-white/40 uppercase">
            Interview Results
          </span>
        </div>

        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-500/15 border border-red-500/40 text-xs text-red-100">
            {error}
          </div>
        )}

        {results && (
          <>
            {/* Score card */}
            <div className="grid grid-cols-1 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-8 items-center">
              <div className="p-10 rounded-[3rem] bg-white/[0.06] border border-white/15 backdrop-blur-sm text-center shadow-2xl shadow-black/40">
                <p className="text-[11px] font-medium tracking-[0.3em] uppercase text-white/60 mb-4">
                  Final Score
                </p>
                <p className="text-6xl md:text-7xl font-semibold text-primary mb-3">
                  {results.overall_score || 0}%
                </p>
                <p className="text-xs text-white/70">
                  Duration: {results.duration || 'N/A'}
                </p>
                <p className="text-xs text-white/60 mt-2">
                  {results.interview_type === 'company_specific'
                    ? results.company_name || 'Company-specific mock interview'
                    : 'Custom topics mock interview'}
                </p>
              </div>

              {/* Actions and short message */}
              <div className="space-y-5">
                <p className="text-lg font-light leading-relaxed text-white/90">
                  Review your performance, understand your strengths, and focus your next sprint on
                  the most impactful improvements.
                </p>
                <div className="flex flex-col md:flex-row gap-3">
                  <button
                    onClick={handleDownloadReport}
                    className="flex-1 py-3 rounded-2xl bg-primary text-white text-sm font-semibold inline-flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Download Report
                  </button>
                  <button
                    onClick={handleShareResults}
                    className="flex-1 py-3 rounded-2xl border border-primary text-primary text-sm font-semibold inline-flex items-center justify-center gap-2 hover:bg-primary/10 transition-colors"
                  >
                    <Share2 className="w-4 h-4" />
                    Share Results
                  </button>
                </div>
              </div>
            </div>

            {/* Analytics */}
            <div className="p-8 rounded-[3rem] bg-white/[0.04] border border-white/15 backdrop-blur-sm">
              <InterviewAnalytics interviewId={interviewId} />
            </div>

            {/* Q&A Review */}
            {results.qa_pairs && results.qa_pairs.length > 0 && (
              <div className="p-8 rounded-[3rem] bg-white/[0.04] border border-white/15 backdrop-blur-sm space-y-6">
                <h2 className="text-xl md:text-2xl font-medium text-white">
                  Question & Answer <span className="font-serif italic text-primary">Review</span>
                </h2>
                <div className="space-y-5">
                  {results.qa_pairs.map((pair: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-6 rounded-2xl bg-white/5 border border-white/15 space-y-4"
                    >
                      {/* Question */}
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-xs text-white/60">
                          <span className="px-3 py-1 rounded-full bg-primary/20 text-primary font-semibold text-[10px] tracking-[0.2em] uppercase">
                            Q{idx + 1}
                          </span>
                          <span>
                            {pair.round_type} • {pair.difficulty}
                          </span>
                        </div>
                        <p className="text-sm text-white/90">{pair.question}</p>
                      </div>

                      {/* Answer */}
                      <div className="space-y-1">
                        <p className="text-[11px] font-medium tracking-[0.25em] uppercase text-white/50">
                          Your Answer
                        </p>
                        <p className="text-sm text-white/85 leading-relaxed">
                          {pair.answer}
                        </p>
                      </div>

                      {/* Feedback + Score */}
                      <div className="pt-4 border-t border-white/10 flex flex-col md:flex-row justify-between gap-3">
                        <div>
                          <p className="text-[11px] font-medium tracking-[0.25em] uppercase text-white/50 mb-1">
                            Feedback
                          </p>
                          <p className="text-xs text-white/80">
                            {pair.feedback || 'No specific recommendations for this question.'}
                          </p>
                        </div>
                        <div className="self-start md:self-center px-4 py-1.5 rounded-xl bg-primary text-white text-xs font-semibold">
                          {pair.score}/10
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default InterviewResults;
