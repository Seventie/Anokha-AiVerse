// frontend/src/components/Interview/InterviewRoom.tsx

import React, { useState, useEffect, useRef } from 'react';
import { interviewService, Question, AnswerFeedback, Round } from '../../services/interviewService';

interface Props {
  interviewId: string;
  onEnd: () => void;
  onBack: () => void;
}

const InterviewRoom: React.FC<Props> = ({ interviewId, onEnd, onBack }) => {
  const [rounds, setRounds] = useState<Round[]>([]);
  const [currentRound, setCurrentRound] = useState<Round | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioMode, setAudioMode] = useState(false);
  const [error, setError] = useState<string>('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    loadRounds();
  }, []);

  const loadRounds = async () => {
    try {
      setError('');
      console.log('📥 Loading rounds for interview:', interviewId);
      const roundsData = await interviewService.getRounds(interviewId);
      console.log('✅ Rounds loaded:', roundsData);
      setRounds(roundsData);
      
      // Find first unlocked round
      const firstUnlocked = roundsData.find(r => r.status === 'unlocked');
      if (firstUnlocked) {
        setCurrentRound(firstUnlocked);
        console.log('🎯 Current round set to:', firstUnlocked);
      }
    } catch (error: any) {
      console.error('❌ Failed to load rounds:', error);
      setError(error.message || 'Failed to load rounds');
    }
  };

  const startRound = async () => {
    if (!currentRound) return;
    
    setLoading(true);
    setError('');
    try {
      console.log('▶️ Starting round:', currentRound.id);
      const question = await interviewService.startRound(interviewId, currentRound.id);
      console.log('✅ Question received:', question);
      setCurrentQuestion(question);
      
      // Play question audio if available
      if (question.audio_url && audioMode) {
        const audio = interviewService.playAudio(question.audio_url);
        audioRef.current = audio;
      }
    } catch (error: any) {
      console.error('❌ Failed to start round:', error);
      setError(error.message || 'Failed to start round');
    } finally {
      setLoading(false);
    }
  };

  const submitTextAnswer = async () => {
    if (!currentQuestion || !answer.trim()) return;
    
    setLoading(true);
    setError('');
    try {
      const result = await interviewService.submitTextAnswer(
        interviewId,
        currentRound!.id,
        currentQuestion.question_id,
        answer
      );
      
      setFeedback(result);
      
      if (result.next_question) {
        setTimeout(() => {
          setCurrentQuestion(result.next_question!);
          setAnswer('');
          setFeedback(null);
          
          if (result.next_question!.audio_url && audioMode) {
            interviewService.playAudio(result.next_question!.audio_url);
          }
        }, 5000);
      } else {
        setTimeout(() => {
          loadRounds();
          setCurrentQuestion(null);
          setFeedback(null);
        }, 5000);
      }
    } catch (error: any) {
      console.error('❌ Failed to submit answer:', error);
      setError(error.message || 'Failed to submit answer');
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await submitAudioAnswer(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const submitAudioAnswer = async (audioBlob: Blob) => {
    if (!currentQuestion) return;
    
    setLoading(true);
    setError('');
    try {
      const result = await interviewService.submitAudioAnswer(
        interviewId,
        currentRound!.id,
        currentQuestion.question_id,
        audioBlob
      );
      
      setFeedback(result);
      
      if (result.next_question) {
        setTimeout(() => {
          setCurrentQuestion(result.next_question!);
          setFeedback(null);
          
          if (result.next_question!.audio_url && audioMode) {
            interviewService.playAudio(result.next_question!.audio_url);
          }
        }, 5000);
      } else {
        setTimeout(() => {
          loadRounds();
          setCurrentQuestion(null);
          setFeedback(null);
        }, 5000);
      }
    } catch (error: any) {
      console.error('❌ Failed to submit audio:', error);
      setError(error.message || 'Failed to submit audio answer');
    } finally {
      setLoading(false);
    }
  };

  const completeInterview = async () => {
    try {
      await interviewService.completeInterview(interviewId);
      onEnd();
    } catch (error) {
      console.error('Failed to complete interview:', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
        <h2 className="text-2xl font-light">Mock Interview</h2>
        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={audioMode}
              onChange={(e) => setAudioMode(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Audio Mode</span>
          </label>
          <button
            onClick={onBack}
            className="px-4 py-2 border border-white/20 rounded-xl hover:bg-white/10 transition-all"
          >
            Exit
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400">
          <p className="font-semibold">Error:</p>
          <p>{error}</p>
        </div>
      )}

      {/* Rounds Progress - FIXED */}
      <div className="mb-6 flex gap-2">
        {rounds.map((round) => (
          <div
            key={round.id}
            className={`flex-1 p-3 rounded-xl text-center border ${
              round.status === 'passed'
                ? 'bg-green-500/20 border-green-500/30 text-green-400'
                : round.status === 'failed'
                ? 'bg-red-500/20 border-red-500/30 text-red-400'
                : round.status === 'in_progress'
                ? 'bg-blue-500/20 border-blue-500/30 text-blue-400'
                : 'bg-white/5 border-white/10 text-white/60'
            }`}
          >
            <div className="font-semibold">Round {round.round_number}</div>
            <div className="text-sm">{round.round_type}</div>
            {/* ← FIXED: Safe score display */}
            {round.score != null && (
              <div className="text-xs mt-1">{Math.round(round.score)}/100</div>
            )}
          </div>
        ))}
      </div>

      {/* Question & Answer Area */}
      {!currentQuestion && currentRound && (
        <div className="text-center py-12 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl">
          <h3 className="text-xl font-semibold mb-4">
            Ready to start Round {currentRound.round_number}?
          </h3>
          <p className="text-white/60 mb-6">
            Type: {currentRound.round_type} | Difficulty: {currentRound.difficulty}
          </p>
          <button
            onClick={startRound}
            disabled={loading}
            className="px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary/80 disabled:opacity-50 transition-all"
          >
            {loading ? 'Loading...' : 'Start Round'}
          </button>
        </div>
      )}

      {currentQuestion && !feedback && (
        <div className="space-y-6">
          {/* Question */}
          <div className="p-6 bg-primary/20 border border-primary/30 rounded-2xl">
            <div className="text-sm text-primary mb-2">Question</div>
            <h3 className="text-xl font-semibold mb-4">{currentQuestion.question_text}</h3>
            
            {currentQuestion.what_to_look_for.length > 0 && (
              <div>
                <div className="text-sm font-medium mb-2">What we're looking for:</div>
                <ul className="list-disc list-inside text-sm text-white/70">
                  {currentQuestion.what_to_look_for.map((point, i) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Answer Input */}
          {!audioMode ? (
            <div>
              <label className="block text-sm font-medium mb-2 text-white/80">Your Answer</label>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Type your answer here..."
                rows={8}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:ring-2 focus:ring-primary text-white placeholder-white/40"
              />
              <button
                onClick={submitTextAnswer}
                disabled={loading || !answer.trim()}
                className="mt-4 px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary/80 disabled:opacity-50 transition-all"
              >
                {loading ? 'Submitting...' : 'Submit Answer'}
              </button>
            </div>
          ) : (
            <div className="text-center py-12 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={loading}
                className={`px-8 py-4 rounded-full text-white font-semibold transition-all ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                    : 'bg-primary hover:bg-primary/80'
                }`}
              >
                {isRecording ? '⏹ Stop Recording' : '🎤 Start Recording'}
              </button>
              <p className="mt-4 text-sm text-white/60">
                {isRecording
                  ? 'Recording... Click to stop and submit'
                  : 'Click to record your answer'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Feedback */}
      {feedback && (
        <div className="space-y-4">
          <div className="p-6 bg-green-500/20 border border-green-500/30 rounded-2xl">
            <div className="text-2xl font-bold text-green-400 mb-2">
              Score: {feedback.score}/100
            </div>
            <p className="text-white/80">{feedback.feedback}</p>
          </div>

          {feedback.strengths.length > 0 && (
            <div className="p-4 bg-green-500/20 border border-green-500/30 rounded-2xl">
              <h4 className="font-semibold mb-2 text-green-400">✅ Strengths:</h4>
              <ul className="list-disc list-inside text-sm text-white/70">
                {feedback.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {feedback.improvements.length > 0 && (
            <div className="p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-2xl">
              <h4 className="font-semibold mb-2 text-yellow-400">💡 Improvements:</h4>
              <ul className="list-disc list-inside text-sm text-white/70">
                {feedback.improvements.map((imp, i) => (
                  <li key={i}>{imp}</li>
                ))}
              </ul>
            </div>
          )}

          {!feedback.next_question && (
            <div className="text-center py-4">
              <p className="text-lg font-semibold mb-4">Round Complete!</p>
              <button
                onClick={() => {
                  setFeedback(null);
                  loadRounds();
                }}
                className="px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary/80 transition-all"
              >
                Continue
              </button>
            </div>
          )}
        </div>
      )}

      {/* All Rounds Complete */}
      {rounds.length > 0 && rounds.every(r => r.status === 'passed' || r.status === 'failed') && !currentQuestion && (
        <div className="text-center py-12 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl">
          <h3 className="text-2xl font-bold mb-4">Interview Complete! 🎉</h3>
          <p className="text-white/60 mb-6">
            You've completed all rounds. View your detailed evaluation.
          </p>
          <button
            onClick={completeInterview}
            className="px-6 py-3 bg-green-500 text-white rounded-xl hover:bg-green-600 transition-all"
          >
            View Results
          </button>
        </div>
      )}
    </div>
  );
};

export default InterviewRoom;
