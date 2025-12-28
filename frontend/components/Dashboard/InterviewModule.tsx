// frontend/components/Dashboard/InterviewModule.tsx

import React, { useState } from 'react';
import { User } from '../../services/authService';
import { agentService } from '../../services/agentService';
import { 
  Video, Play, Send, CheckCircle, 
  AlertCircle, TrendingUp, Loader2, 
  Target, Clock, Award, Zap
} from 'lucide-react';

interface InterviewModuleProps {
  user: User;
}

const InterviewModule: React.FC<InterviewModuleProps> = ({ user }) => {
  const [session, setSession] = useState<any>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [questionIndex, setQuestionIndex] = useState(0);
  const [feedback, setFeedback] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [jobTitle, setJobTitle] = useState(user.targetRole || 'Software Engineer');
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [interviewStarted, setInterviewStarted] = useState(false);

  const startInterview = async () => {
    setLoading(true);
    try {
      const result = await agentService.startInterview(user.id, jobTitle, difficulty);
      setSession(result);
      if (result.first_question) {
        setCurrentQuestion(result.first_question);
        setInterviewStarted(true);
      }
    } catch (error) {
      console.error('Failed to start interview:', error);
      alert('Failed to start interview');
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!currentAnswer.trim() || !session) return;

    setLoading(true);
    try {
      const result = await agentService.submitAnswer(session.session_id, questionIndex, currentAnswer);
      setFeedback(result);
      setCurrentAnswer('');
      
      // Move to next question if available
      if (result.next_question) {
        setQuestionIndex(questionIndex + 1);
        setCurrentQuestion(result.next_question);
        setFeedback(null);
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFinalFeedback = async () => {
    if (!session) return;
    
    setLoading(true);
    try {
      const result = await agentService.getInterviewFeedback(session.session_id);
      setFeedback(result);
    } catch (error) {
      console.error('Failed to get feedback:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!interviewStarted) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-light mb-2">Mock Interview</h2>
            <p className="text-white/60">Practice with AI-powered interview questions</p>
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-8 max-w-2xl mx-auto">
          <div className="space-y-6">
            <div>
              <label className="block text-sm text-white/60 mb-2">Job Title</label>
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder-white/30 focus:outline-none focus:border-primary/50"
                placeholder="e.g., Software Engineer"
              />
            </div>

            <div>
              <label className="block text-sm text-white/60 mb-2">Difficulty Level</label>
              <div className="flex gap-3">
                {(['easy', 'medium', 'hard'] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => setDifficulty(d)}
                    className={`flex-1 p-4 rounded-2xl border transition-all capitalize ${
                      difficulty === d
                        ? 'bg-primary/20 border-primary/30 text-primary'
                        : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/10'
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={startInterview}
              disabled={loading || !jobTitle.trim()}
              className="w-full px-6 py-4 bg-primary text-bg-deep rounded-2xl font-bold flex items-center justify-center gap-3 hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  Starting Interview...
                </>
              ) : (
                <>
                  <Play size={20} />
                  Start Interview
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Mock Interview</h2>
          <p className="text-white/60">
            Question {questionIndex + 1} of {session?.total_questions || '?'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-4 py-2 bg-white/5 rounded-full text-sm capitalize">
            {difficulty}
          </span>
          <span className="px-4 py-2 bg-white/5 rounded-full text-sm">
            {jobTitle}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Question Section */}
        <div className="space-y-6">
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <div className="flex items-center gap-3 mb-4">
              <Video size={20} className="text-primary" />
              <h3 className="text-lg font-medium">Question</h3>
            </div>
            
            {currentQuestion && (
              <div className="space-y-4">
                <div className="p-4 bg-white/5 rounded-2xl">
                  <p className="text-white/90 leading-relaxed">{currentQuestion.question}</p>
                </div>
                
                {currentQuestion.category && (
                  <div className="flex items-center gap-2 text-sm text-white/60">
                    <span className="px-3 py-1 bg-primary/10 text-primary rounded-full capitalize">
                      {currentQuestion.category}
                    </span>
                    {currentQuestion.time_limit_seconds && (
                      <span className="flex items-center gap-1">
                        <Clock size={14} />
                        {currentQuestion.time_limit_seconds}s
                      </span>
                    )}
                  </div>
                )}

                {currentQuestion.what_to_look_for && (
                  <div className="p-4 bg-primary/10 rounded-xl">
                    <p className="text-xs text-primary/80 mb-2">What we're looking for:</p>
                    <p className="text-sm text-white/70">{currentQuestion.what_to_look_for}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Answer Input */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
              <Target size={20} className="text-primary" />
              Your Answer
            </h3>
            <textarea
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              placeholder="Type your answer here... Take your time to structure your response."
              className="w-full h-48 bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder-white/30 resize-none focus:outline-none focus:border-primary/50"
            />
            <button
              onClick={submitAnswer}
              disabled={loading || !currentAnswer.trim()}
              className="w-full mt-4 px-6 py-4 bg-primary text-bg-deep rounded-2xl font-bold flex items-center justify-center gap-3 hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  Evaluating...
                </>
              ) : (
                <>
                  <Send size={20} />
                  Submit Answer
                </>
              )}
            </button>
          </div>
        </div>

        {/* Feedback Section */}
        <div className="space-y-6">
          {feedback && (
            <>
              {feedback.final_score !== undefined ? (
                // Final Feedback
                <div className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 rounded-[2rem] p-6">
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                    <Award size={20} className="text-primary" />
                    Final Results
                  </h3>
                  <div className="text-center mb-6">
                    <div className="text-5xl font-bold text-primary mb-2">
                      {feedback.final_score || 0}
                    </div>
                    <p className="text-white/60">Overall Score</p>
                  </div>
                  {feedback.feedback && (
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm text-white/60 mb-2">Overall Feedback:</p>
                        <p className="text-white/90">{feedback.feedback}</p>
                      </div>
                      {feedback.improvements && feedback.improvements.length > 0 && (
                        <div>
                          <p className="text-sm text-white/60 mb-2">Areas to Improve:</p>
                          <ul className="space-y-2">
                            {feedback.improvements.map((imp: string, idx: number) => (
                              <li key={idx} className="flex items-start gap-2 text-sm text-white/80">
                                <AlertCircle size={16} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                                <span>{imp}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                // Question Feedback
                <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                    <TrendingUp size={20} className="text-primary" />
                    Feedback
                  </h3>
                  {feedback.score !== undefined && (
                    <div className="mb-4">
                      <div className="text-3xl font-bold text-primary mb-1">
                        {feedback.score}/100
                      </div>
                      <p className="text-sm text-white/60">Score for this answer</p>
                    </div>
                  )}
                  {feedback.feedback && (
                    <p className="text-white/80 mb-4">{feedback.feedback}</p>
                  )}
                  {feedback.strengths && feedback.strengths.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm text-white/60 mb-2">Strengths:</p>
                      <ul className="space-y-1">
                        {feedback.strengths.map((s: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-white/80">
                            <CheckCircle size={14} className="text-green-400 mt-0.5 flex-shrink-0" />
                            <span>{s}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {feedback.improvements && feedback.improvements.length > 0 && (
                    <div>
                      <p className="text-sm text-white/60 mb-2">Improvements:</p>
                      <ul className="space-y-1">
                        {feedback.improvements.map((imp: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-white/80">
                            <AlertCircle size={14} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                            <span>{imp}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {!feedback && (
            <div className="bg-white/5 border border-white/10 rounded-[2rem] p-12 text-center">
              <Video size={48} className="mx-auto mb-4 text-white/20" />
              <p className="text-white/60">
                Submit your answer to receive AI-powered feedback
              </p>
            </div>
          )}

          {questionIndex >= (session?.total_questions || 0) - 1 && !feedback?.final_score && (
            <button
              onClick={getFinalFeedback}
              disabled={loading}
              className="w-full px-6 py-4 bg-primary/20 hover:bg-primary/30 text-primary rounded-2xl font-bold flex items-center justify-center gap-3 transition-all border border-primary/30"
            >
              <Award size={20} />
              Get Final Feedback
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default InterviewModule;

