// frontend/src/components/Interview/InterviewRoom.tsx

import React, { useState, useEffect, useRef } from 'react';
import { interviewService } from '../../services/interviewService';
import { Mic, MicOff, Volume2, VolumeX, Send, Phone, Loader } from 'lucide-react';

interface Props {
  interviewId: string;
  onInterviewEnd: () => void;
  onCancel: () => void;
}

const InterviewRoom: React.FC<Props> = ({ interviewId, onInterviewEnd, onCancel }) => {
  const [currentRound, setCurrentRound] = useState<any>(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeaker, setIsSpeaker] = useState(true);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    initializeInterview();
    initializeCamera();
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const initializeCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: true,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
      }
    } catch (err) {
      setError('Please allow camera and microphone access.');
    }
  };

  const initializeInterview = async () => {
    try {
      setLoading(true);
      const data = await interviewService.getInterview(interviewId);
      if (data.current_round) {
        setCurrentRound(data.current_round);
        setQuestion(data.current_round.question || '');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load interview');
    } finally {
      setLoading(false);
    }
  };

  const toggleMicrophone = () => {
    if (streamRef.current) {
      streamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = !track.enabled;
      });
      setIsMuted((prev) => !prev);
    }
  };

  const submitAnswer = async () => {
    if (!answer.trim()) {
      setError('Please provide an answer.');
      return;
    }

    try {
      setError('');
      setSubmitting(true);
      const response = await interviewService.submitAnswer(interviewId, {
        answer,
        is_voice: false,
      });

      if (response.feedback) {
        setFeedback(response.feedback);
      }

      if (response.is_complete) {
        setTimeout(onInterviewEnd, 1500);
      } else if (response.next_round) {
        setCurrentRound(response.next_round);
        setQuestion(response.next_round.question || '');
        setAnswer('');
        setFeedback(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit answer');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !currentRound) {
    return (
      <div className="min-h-screen bg-[#0b1714] flex items-center justify-center text-white">
        <div className="text-center space-y-4">
          <Loader className="w-10 h-10 animate-spin text-primary mx-auto" />
          <p className="text-sm text-white/70">Preparing your mock interview…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b1714] text-white">
      <div className="max-w-[1400px] mx-auto px-8 md:px-24 py-10">
        {/* Top Bar */}
        <div className="flex items-center justify-between mb-8">
          <div className="space-y-1">
            <p className="text-xs tracking-[0.3em] uppercase text-white/40">Live Mock Interview</p>
            <p className="text-sm text-white/70">
              Round {currentRound?.round_number ?? 1} • {currentRound?.round_type}{' '}
              • {currentRound?.difficulty}
            </p>
          </div>
          <button
            onClick={onCancel}
            className="inline-flex items-center gap-2 text-xs font-medium text-red-300 hover:text-red-200"
          >
            <Phone className="w-4 h-4" />
            End Session
          </button>
        </div>

        {error && (
          <div className="mb-4 px-4 py-3 rounded-xl bg-red-500/15 border border-red-500/40 text-xs text-red-100">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          {/* Video */}
          <div className="lg:col-span-2 space-y-4">
            <div className="relative rounded-[2.5rem] overflow-hidden bg-black/60 border border-white/15 shadow-2xl shadow-black/50 aspect-video">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted={!isSpeaker}
                className="w-full h-full object-cover"
              />
              <div className="absolute top-4 left-4 px-3 py-1 rounded-full text-[11px] font-medium bg-emerald-500/90 text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                Camera Active
              </div>
              <div className="absolute top-4 right-4 px-3 py-1 rounded-full text-[11px] font-medium bg-black/50 text-white/80">
                Mock Interview
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-center gap-4 mt-4">
              <button
                onClick={toggleMicrophone}
                className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  isMuted ? 'bg-red-500' : 'bg-primary'
                } text-white shadow-lg shadow-black/40 hover:scale-105 transition-transform`}
              >
                {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              <button
                onClick={() => setIsSpeaker((prev) => !prev)}
                className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  isSpeaker ? 'bg-primary' : 'bg-white/15'
                } text-white shadow-lg shadow-black/40 hover:scale-105 transition-transform`}
              >
                {isSpeaker ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Question + Answer */}
          <div className="space-y-6">
            {/* Question */}
            <div className="p-6 rounded-3xl bg-white/[0.06] border border-white/15 backdrop-blur-sm">
              <p className="text-[11px] font-medium tracking-[0.25em] uppercase text-white/50 mb-3">
                Question
              </p>
              <p className="text-sm md:text-base text-white/90 leading-relaxed">{question}</p>
            </div>

            {/* Feedback or Answer box */}
            {feedback ? (
              <div className="p-6 rounded-3xl bg-emerald-500/10 border border-emerald-500/60">
                <p className="text-[11px] font-medium tracking-[0.25em] uppercase text-emerald-300 mb-3">
                  Feedback
                </p>
                <p className="text-sm text-emerald-100 mb-3">{feedback.feedback}</p>
                {typeof feedback.score !== 'undefined' && (
                  <p className="text-xs text-emerald-200">
                    Score:{' '}
                    <span className="font-semibold">
                      {feedback.score}/10
                    </span>
                  </p>
                )}
              </div>
            ) : (
              <div className="p-6 rounded-3xl bg-white/[0.06] border border-white/15 backdrop-blur-sm">
                <label className="block text-[11px] font-medium tracking-[0.25em] uppercase text-white/50 mb-3">
                  Your Answer
                </label>
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  rows={6}
                  placeholder="Walk through your thought process. Explain tradeoffs, assumptions, and edge cases."
                  className="w-full bg-white/5 border border-white/20 rounded-2xl px-4 py-3 text-sm text-white placeholder-white/40 outline-none focus:ring-2 focus:ring-primary resize-none"
                />
                <button
                  onClick={submitAnswer}
                  disabled={submitting}
                  className="mt-3 w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-primary text-white text-sm font-semibold py-2.5 hover:bg-primary/90 transition-colors disabled:opacity-60"
                >
                  <Send className="w-4 h-4" />
                  {submitting ? 'Submitting…' : 'Submit Answer'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewRoom;
