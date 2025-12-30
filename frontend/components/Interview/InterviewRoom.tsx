// frontend/src/components/Interview/InterviewRoom.tsx

import React, { useState, useEffect, useRef } from 'react';
import { interviewService, Question, AnswerFeedback, Round } from '../../services/interviewService';
import { Mic, MicOff, Volume2, VolumeX, Send, Phone, Loader } from 'lucide-react';

interface Props {
  interviewId: string;
  onInterviewEnd: () => void;
  onCancel: () => void;
}

const InterviewRoom: React.FC<Props> = ({ interviewId, onInterviewEnd, onCancel }) => {
  // State
  const [rounds, setRounds] = useState<Round[]>([]);
  const [currentRound, setCurrentRound] = useState<Round | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeaker, setIsSpeaker] = useState(true);

  // 🔥 Audio recording for Whisper
  const [isRecordingAudio, setIsRecordingAudio] = useState(false);
  const [audioMode, setAudioMode] = useState<'text' | 'voice'>('text');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  
  // 🔥 Session recording for playback
  const [isRecordingSession, setIsRecordingSession] = useState(false);
  const sessionRecorderRef = useRef<MediaRecorder | null>(null);
  const sessionChunksRef = useRef<Blob[]>([]);

  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Initialize
  useEffect(() => {
    void bootstrap();
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      stopSessionRecording();
    };
  }, []);

  const bootstrap = async () => {
    try {
      await initializeCamera();
      await startSessionRecording();
      await loadRounds();
    } catch (err: any) {
      setError(err?.message || 'Failed to start interview');
    }
  };

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
      console.warn('Camera access denied:', err);
      setError('Please allow camera and microphone access.');
    }
  };

  const startSessionRecording = async () => {
    if (!streamRef.current) return;
    
    try {
      // Check if the mimeType is supported
      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')
        ? 'video/webm;codecs=vp8,opus'
        : MediaRecorder.isTypeSupported('video/webm')
        ? 'video/webm'
        : '';

      if (!mimeType) {
        console.warn('No supported video mime type found');
        return;
      }

      const recorder = new MediaRecorder(streamRef.current, { mimeType });
      
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          sessionChunksRef.current.push(e.data);
        }
      };
      
      recorder.start(1000); // Record in 1s chunks
      sessionRecorderRef.current = recorder;
      setIsRecordingSession(true);
      console.log('📹 Session recording started');
    } catch (err) {
      console.error('Failed to start session recording:', err);
    }
  };

  const stopSessionRecording = () => {
    if (sessionRecorderRef.current && sessionRecorderRef.current.state !== 'inactive') {
      sessionRecorderRef.current.stop();
      setIsRecordingSession(false);
      console.log('⏹️ Session recording stopped');
    }
  };

  const loadRounds = async () => {
    try {
      setLoading(true);
      setError('');
      
      console.log('📥 Loading rounds for interview:', interviewId);
      const roundsData = await interviewService.getRounds(interviewId);
      console.log('✅ Rounds loaded:', roundsData);
      
      setRounds(roundsData);

      // Find first unlocked round
      const firstUnlocked = roundsData.find((r) => r.status === 'unlocked');
      
      if (firstUnlocked) {
        setCurrentRound(firstUnlocked);
        console.log('🎯 Current round set to:', firstUnlocked);
        
        // Auto-start the round to get first question
        await startRound(firstUnlocked);
      } else {
        const allDone = roundsData.length > 0 && roundsData.every((r) => r.status === 'passed' || r.status === 'failed');
        if (allDone) {
          console.log('✅ All rounds complete');
          await finishInterview();
        }
      }
    } catch (error: any) {
      console.error('❌ Failed to load rounds:', error);
      setError(error.message || 'Failed to load rounds');
    } finally {
      setLoading(false);
    }
  };

  const startRound = async (round: Round) => {
    try {
      setLoading(true);
      setError('');
      setFeedback(null);
      
      console.log('🚀 Starting round:', round.id);
      const questionData = await interviewService.startRound(interviewId, round.id);
      console.log('✅ Question received:', questionData);
      
      setCurrentQuestion(questionData);
      setAnswer('');
    } catch (error: any) {
      console.error('❌ Failed to start round:', error);
      setError(error.message || 'Failed to start round');
    } finally {
      setLoading(false);
    }
  };

  // 🔥 Record audio answer
  const recordAudioAnswer = async (): Promise<void> => {
    return new Promise((resolve) => {
      if (!streamRef.current) {
        resolve();
        return;
      }

      const audioStream = new MediaStream(streamRef.current.getAudioTracks());
      audioChunksRef.current = [];

      // Check supported mime types
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : '';

      if (!mimeType) {
        console.error('No supported audio mime type');
        resolve();
        return;
      }

      const recorder = new MediaRecorder(audioStream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        resolve();
      };

      recorder.start();
      setIsRecordingAudio(true);

      // Auto-stop after 2 minutes
      setTimeout(() => {
        if (recorder.state !== 'inactive') {
          recorder.stop();
          setIsRecordingAudio(false);
        }
      }, 120000);
    });
  };

  const stopAudioRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecordingAudio(false);
    }
  };

  // 🔥 Submit answer with audio or text
  const submitAnswer = async () => {
    if (!currentRound || !currentQuestion) {
      setError('No active question');
      return;
    }

    try {
      setError('');
      setSubmitting(true);

      let response: AnswerFeedback;

      if (audioMode === 'voice' && isRecordingAudio) {
        // Stop recording and get audio blob
        stopAudioRecording();
        await new Promise(r => setTimeout(r, 500)); // Wait for onstop
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        console.log('📤 Submitting audio answer (Whisper will transcribe)');
        
        // Check if submitAudioAnswer method exists
        if (typeof interviewService.submitAudioAnswer === 'function') {
          response = await interviewService.submitAudioAnswer(
            interviewId,
            currentRound.id,
            currentQuestion.question_id,
            audioBlob
          );
        } else {
          // Fallback: Convert to base64 and submit as text
          const reader = new FileReader();
          reader.readAsDataURL(audioBlob);
          await new Promise((resolve) => {
            reader.onloadend = resolve;
          });
          const audioBase64 = reader.result as string;
          
          response = await interviewService.submitAnswer(
            interviewId,
            currentRound.id,
            currentQuestion.question_id,
            '[Voice Answer - Transcription pending]',
            audioBase64
          );
        }
      } else {
        // Text answer
        if (!answer.trim()) {
          setError('Please provide an answer.');
          setSubmitting(false);
          return;
        }

        console.log('📤 Submitting text answer');
        response = await interviewService.submitAnswer(
          interviewId,
          currentRound.id,
          currentQuestion.question_id,
          answer
        );
      }

      console.log('✅ Answer feedback:', response);
      setFeedback(response);
      setAnswer('');

      // Next question or end
      if (response.next_question) {
        console.log('➡️ Moving to next question');
        setTimeout(() => {
          setCurrentQuestion(response.next_question!);
          setFeedback(null);
        }, 3000); // Show feedback for 3 seconds
      } else {
        console.log('🏁 Round complete, reloading...');
        setTimeout(() => {
          void loadRounds();
        }, 3000);
      }
    } catch (err: any) {
      console.error('❌ Submit answer error:', err);
      setError(err.message || 'Failed to submit answer');
    } finally {
      setSubmitting(false);
    }
  };

  const finishInterview = async () => {
    try {
      stopSessionRecording();
      
      // Upload session recording
      if (sessionChunksRef.current.length > 0) {
        const videoBlob = new Blob(sessionChunksRef.current, { type: 'video/webm' });
        console.log('📤 Uploading interview recording...');
        
        // Check if uploadRecording method exists
        if (typeof interviewService.uploadRecording === 'function') {
          await interviewService.uploadRecording(interviewId, videoBlob);
        } else {
          console.warn('Upload recording method not available');
        }
      }

      await interviewService.completeInterview(interviewId);
      onInterviewEnd();
    } catch (error) {
      console.error('Failed to complete interview:', error);
      onInterviewEnd();
    }
  };

  const startVoiceAnswer = async () => {
    setAudioMode('voice');
    await recordAudioAnswer();
  };

  const toggleMicrophone = () => {
    if (streamRef.current) {
      streamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = !track.enabled;
      });
      setIsMuted((prev) => !prev);
    }
  };

  // Loading state
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
      <div className="max-w-[1400px] mx-auto px-4 sm:px-8 md:px-24 py-10">
        {/* Top Bar */}
        <div className="flex items-center justify-between mb-8">
          <div className="space-y-1">
            <p className="text-xs tracking-[0.3em] uppercase text-white/40">Live Mock Interview</p>
            <p className="text-sm text-white/70">
              Round {currentRound?.round_number ?? 1} • {currentRound?.round_type} • {currentRound?.difficulty}
            </p>
          </div>
          <button
            onClick={onCancel}
            className="inline-flex items-center gap-2 text-xs font-medium text-red-300 hover:text-red-200 transition-colors"
          >
            <Phone className="w-4 h-4" />
            End Session
          </button>
        </div>

        {/* Recording indicator */}
        {isRecordingSession && (
          <div className="fixed top-4 right-4 px-4 py-2 rounded-full bg-red-500/90 text-white text-sm flex items-center gap-2 z-50 shadow-lg">
            <span className="w-3 h-3 rounded-full bg-white animate-pulse" />
            Recording Session
          </div>
        )}

        {/* Error Display */}
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
              <div className="absolute top-4 right-4 px-3 py-1 rounded-full text-[11px] font-medium bg-black/50 text-white/80 backdrop-blur-sm">
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
                title={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              <button
                onClick={() => setIsSpeaker((prev) => !prev)}
                className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  isSpeaker ? 'bg-primary' : 'bg-white/15'
                } text-white shadow-lg shadow-black/40 hover:scale-105 transition-transform`}
                title={isSpeaker ? 'Disable speaker' : 'Enable speaker'}
              >
                {isSpeaker ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Question + Answer */}
          <div className="space-y-6">
            {/* Question */}
            {currentQuestion && (
              <div className="p-6 rounded-3xl bg-white/[0.06] border border-white/15 backdrop-blur-sm">
                <p className="text-[11px] font-medium tracking-[0.25em] uppercase text-white/50 mb-3">
                  Question
                </p>
                <p className="text-sm md:text-base text-white/90 leading-relaxed">
                  {currentQuestion.question_text}
                </p>
                
                {currentQuestion.what_to_look_for && currentQuestion.what_to_look_for.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <p className="text-[10px] font-medium tracking-[0.2em] uppercase text-white/40 mb-2">
                      What to cover
                    </p>
                    <ul className="space-y-1">
                      {currentQuestion.what_to_look_for.map((point, i) => (
                        <li key={i} className="text-xs text-white/60">• {point}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Answer Input */}
            {!feedback && currentQuestion && (
              <div className="p-6 rounded-3xl bg-white/[0.06] border border-white/15 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-[11px] font-medium tracking-[0.25em] uppercase text-white/50">
                    Your Answer
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAudioMode('text')}
                      disabled={isRecordingAudio}
                      className={`px-3 py-1 rounded-lg text-xs transition-colors ${
                        audioMode === 'text' ? 'bg-primary text-white' : 'bg-white/10 text-white/60 hover:bg-white/20'
                      } disabled:opacity-50`}
                    >
                      Text
                    </button>
                    <button
                      onClick={() => setAudioMode('voice')}
                      disabled={isRecordingAudio}
                      className={`px-3 py-1 rounded-lg text-xs transition-colors ${
                        audioMode === 'voice' ? 'bg-primary text-white' : 'bg-white/10 text-white/60 hover:bg-white/20'
                      } disabled:opacity-50`}
                    >
                      🎤 Voice
                    </button>
                  </div>
                </div>

                {audioMode === 'text' ? (
                  <>
                    <textarea
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      rows={6}
                      placeholder="Walk through your thought process..."
                      className="w-full bg-white/5 border border-white/20 rounded-2xl px-4 py-3 text-sm text-white placeholder-white/40 outline-none focus:ring-2 focus:ring-primary resize-none"
                    />
                    <button
                      onClick={submitAnswer}
                      disabled={submitting || !answer.trim()}
                      className="mt-3 w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-primary text-white text-sm font-semibold py-2.5 hover:bg-primary/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      {submitting ? (
                        <>
                          <Loader className="w-4 h-4 animate-spin" />
                          Submitting…
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          Submit Answer
                        </>
                      )}
                    </button>
                  </>
                ) : (
                  <div className="text-center py-8">
                    {!isRecordingAudio ? (
                      <button
                        onClick={startVoiceAnswer}
                        disabled={submitting}
                        className="px-8 py-4 rounded-2xl bg-red-500 text-white text-sm font-semibold hover:bg-red-600 transition-colors inline-flex items-center gap-3 disabled:opacity-60"
                      >
                        <Mic className="w-5 h-5" />
                        Start Recording
                      </button>
                    ) : (
                      <>
                        <div className="mb-4 flex items-center justify-center gap-2">
                          <span className="w-4 h-4 rounded-full bg-red-500 animate-pulse" />
                          <span className="text-sm text-white/70">Recording your answer...</span>
                        </div>
                        <button
                          onClick={submitAnswer}
                          disabled={submitting}
                          className="px-8 py-4 rounded-2xl bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors disabled:opacity-60"
                        >
                          {submitting ? (
                            <>
                              <Loader className="w-4 h-4 animate-spin inline mr-2" />
                              Processing...
                            </>
                          ) : (
                            'Stop & Submit'
                          )}
                        </button>
                      </>
                    )}
                    <p className="text-xs text-white/50 mt-4">
                      Your voice will be transcribed using Whisper AI
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Feedback Display */}
            {feedback && (
              <div className="p-6 rounded-3xl bg-emerald-500/10 border border-emerald-500/60 animate-fadeIn">
                <p className="text-[11px] font-medium tracking-[0.25em] uppercase text-emerald-300 mb-3">
                  Feedback
                </p>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-emerald-400">{Math.round(feedback.score)}</span>
                  <span className="text-sm text-emerald-300">/100</span>
                </div>
                <p className="text-sm text-emerald-100 mb-3">{feedback.feedback}</p>
                
                {feedback.strengths && feedback.strengths.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-emerald-200 mb-1">Strengths:</p>
                    <ul className="space-y-1">
                      {feedback.strengths.map((s, i) => (
                        <li key={i} className="text-xs text-emerald-100">✓ {s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {feedback.improvements && feedback.improvements.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-yellow-200 mb-1">Improvements:</p>
                    <ul className="space-y-1">
                      {feedback.improvements.map((imp, i) => (
                        <li key={i} className="text-xs text-yellow-100">→ {imp}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        
        {/* Rounds Progress */}
        {rounds.length > 0 && (
          <div className="mt-8 flex gap-2 overflow-x-auto pb-2">
            {rounds.map((round) => (
              <div
                key={round.id}
                className={`flex-1 min-w-[120px] p-3 rounded-xl text-center border transition-all ${
                  round.status === 'passed'
                    ? 'bg-green-500/20 border-green-500/30 text-green-400'
                    : round.status === 'failed'
                    ? 'bg-red-500/20 border-red-500/30 text-red-400'
                    : round.status === 'in_progress'
                    ? 'bg-blue-500/20 border-blue-500/30 text-blue-400'
                    : 'bg-white/5 border-white/10 text-white/60'
                }`}
              >
                <div className="font-semibold text-sm">Round {round.round_number}</div>
                <div className="text-xs mt-1">{round.round_type}</div>
                {round.score != null && (
                  <div className="text-xs mt-1 font-medium">{Math.round(round.score)}/100</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default InterviewRoom;
