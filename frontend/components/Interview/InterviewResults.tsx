// frontend/src/components/Interview/InterviewResults.tsx

import React, { useState, useEffect } from 'react';
import { interviewService, Evaluation } from '../../services/interviewService';

interface Props {
  interviewId: string;
  onClose: () => void;
}

const InterviewResults: React.FC<Props> = ({ interviewId, onClose }) => {
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [conversation, setConversation] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'transcript' | 'recommendations'>('overview');

  useEffect(() => {
    loadResults();
  }, []);

  const loadResults = async () => {
    try {
      const [evalData, convData] = await Promise.all([
        interviewService.getEvaluation(interviewId),
        interviewService.getConversation(interviewId)
      ]);
      
      setEvaluation(evalData);
      setConversation(convData);
    } catch (error) {
      console.error('Failed to load results:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading results...</div>
      </div>
    );
  }

  if (!evaluation) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-red-500">Failed to load evaluation</div>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold mb-2">Interview Results</h1>
          <p className="text-gray-600">Comprehensive performance evaluation</p>
        </div>
        <button
          onClick={onClose}
          className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Back to Dashboard
        </button>
      </div>

      {/* Overall Score Card */}
      <div className="mb-8 p-8 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-2xl shadow-xl">
        <div className="text-center">
          <div className="text-6xl font-bold mb-2">{evaluation.overall_score.toFixed(0)}</div>
          <div className="text-2xl mb-4">Overall Score</div>
          <div className="flex justify-center gap-8 mt-6">
            <div>
              <div className="text-3xl font-bold">{evaluation.technical_score.toFixed(0)}</div>
              <div className="text-sm opacity-80">Technical</div>
            </div>
            <div>
              <div className="text-3xl font-bold">{evaluation.communication_score.toFixed(0)}</div>
              <div className="text-sm opacity-80">Communication</div>
            </div>
            <div>
              <div className="text-3xl font-bold">{evaluation.problem_solving_score.toFixed(0)}</div>
              <div className="text-sm opacity-80">Problem Solving</div>
            </div>
            <div>
              <div className="text-3xl font-bold">{evaluation.confidence_score.toFixed(0)}</div>
              <div className="text-sm opacity-80">Confidence</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b">
        <div className="flex gap-6">
          {(['overview', 'transcript', 'recommendations'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 px-2 font-medium capitalize ${
                activeTab === tab
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Detailed Scores */}
          <div className="grid grid-cols-2 gap-6">
            {[
              { label: 'Technical Skills', score: evaluation.technical_score },
              { label: 'Communication', score: evaluation.communication_score },
              { label: 'Problem Solving', score: evaluation.problem_solving_score },
              { label: 'Confidence', score: evaluation.confidence_score }
            ].map((item) => (
              <div key={item.label} className={`p-6 rounded-lg ${getScoreBgColor(item.score)}`}>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold">{item.label}</span>
                  <span className={`text-2xl font-bold ${getScoreColor(item.score)}`}>
                    {item.score.toFixed(0)}
                  </span>
                </div>
                <div className="w-full bg-white rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      item.score >= 80
                        ? 'bg-green-500'
                        : item.score >= 60
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${item.score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Strengths */}
          {evaluation.strengths.length > 0 && (
            <div className="p-6 bg-green-50 rounded-lg">
              <h3 className="text-xl font-bold mb-4 text-green-700">✅ Key Strengths</h3>
              <ul className="space-y-2">
                {evaluation.strengths.map((strength, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-gray-700">{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Weaknesses */}
          {evaluation.weaknesses.length > 0 && (
            <div className="p-6 bg-yellow-50 rounded-lg">
              <h3 className="text-xl font-bold mb-4 text-yellow-700">⚠️ Areas for Improvement</h3>
              <ul className="space-y-2">
                {evaluation.weaknesses.map((weakness, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <span className="text-yellow-600 text-xl">!</span>
                    <span className="text-gray-700">{weakness}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {activeTab === 'transcript' && (
        <div className="space-y-4">
          <h3 className="text-xl font-bold mb-4">Interview Transcript</h3>
          {conversation.map((msg, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg ${
                msg.speaker === 'ai'
                  ? 'bg-blue-50 border-l-4 border-blue-500'
                  : 'bg-gray-50 border-l-4 border-gray-500'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="font-semibold">
                  {msg.speaker === 'ai' ? '🤖 Interviewer' : '👤 You'}
                </span>
                {msg.score && (
                  <span className={`font-bold ${getScoreColor(msg.score)}`}>
                    {msg.score.toFixed(0)}/100
                  </span>
                )}
              </div>
              <p className="text-gray-700 whitespace-pre-wrap">{msg.message}</p>
              {msg.audio_url && (
                <audio controls className="mt-2 w-full">
                  <source src={`http://localhost:8000${msg.audio_url}`} type="audio/wav" />
                </audio>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'recommendations' && (
        <div className="space-y-6">
          <div className="p-6 bg-blue-50 rounded-lg">
            <h3 className="text-xl font-bold mb-4 text-blue-700">📚 Personalized Recommendations</h3>
            {evaluation.recommendations.length > 0 ? (
              <ul className="space-y-3">
                {evaluation.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <span className="text-blue-600 text-xl">→</span>
                    <span className="text-gray-700">{rec}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-600">No specific recommendations at this time.</p>
            )}
          </div>

          {/* Next Steps */}
          <div className="p-6 bg-purple-50 rounded-lg">
            <h3 className="text-xl font-bold mb-4 text-purple-700">🎯 Next Steps</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-purple-200 rounded-full flex items-center justify-center font-bold text-purple-700">
                  1
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Review Feedback</h4>
                  <p className="text-sm text-gray-600">
                    Study the strengths and weaknesses identified in this interview.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-purple-200 rounded-full flex items-center justify-center font-bold text-purple-700">
                  2
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Practice Weak Areas</h4>
                  <p className="text-sm text-gray-600">
                    Focus on the areas for improvement before your next interview.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-purple-200 rounded-full flex items-center justify-center font-bold text-purple-700">
                  3
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Retake in 1 Week</h4>
                  <p className="text-sm text-gray-600">
                    Schedule another mock interview to track your improvement.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button className="flex-1 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
              Schedule Next Interview
            </button>
            <button className="flex-1 py-3 border border-blue-500 text-blue-500 rounded-lg hover:bg-blue-50">
              Download Report (PDF)
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewResults;
