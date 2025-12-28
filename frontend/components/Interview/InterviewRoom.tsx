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
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioMode] = useState(true);
  const [error, setError] = useState<string>('');
  const [isSpeakingQuestion, setIsSpeakingQuestion] = useState(false);
  const [isListeningAnswer, setIsListeningAnswer] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const sessionStreamRef = useRef<MediaStream | null>(null);
  const sessionRecorderRef = useRef<MediaRecorder | null>(null);
  const sessionChunksRef = useRef<Blob[]>([]);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const isMountedRef = useRef(true);
  const isBusyRef = useRef(false);
  const questionCounterRef = useRef(0);
  const activeRoundRef = useRef<Round | null>(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    isMountedRef.current = true;
    void bootstrap();
    return () => {
      isMountedRef.current = false;
      cleanupMedia();
      if (videoPreviewUrl) {
        URL.revokeObjectURL(videoPreviewUrl);
      }
    };
  }, []);

  const bootstrap = async () => {
    try {
      setError('');
      await startCameraAndRecording();
      await loadRounds(true);
    } catch (e: any) {
      setError(e?.message || 'Failed to start interview');
    }
  };

  const cleanupMedia = () => {
    try {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
        audioRef.current = null;
      }
    } catch {
    }

    try {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    } catch {
    }

    try {
      if (sessionRecorderRef.current && sessionRecorderRef.current.state !== 'inactive') {
        sessionRecorderRef.current.stop();
      }
    } catch {
    }

    try {
      sessionStreamRef.current?.getTracks().forEach(t => t.stop());
      sessionStreamRef.current = null;
    } catch {
    }
  };

  const startCameraAndRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user' },
      audio: { echoCancellation: true, noiseSuppression: true }
    });

    sessionStreamRef.current = stream;

    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play().catch(() => undefined);
    }

    sessionChunksRef.current = [];
    const sessionRecorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8,opus' });
    sessionRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) sessionChunksRef.current.push(e.data);
    };
    sessionRecorder.start(1000);
    sessionRecorderRef.current = sessionRecorder;
  };

  const loadRounds = async (autoStart: boolean = false) => {
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
        if (autoStart) {
          await startRound(firstUnlocked);
        }
      } else if (autoStart) {
        const allDone = roundsData.length > 0 && roundsData.every(r => r.status === 'passed' || r.status === 'failed');
        if (allDone) {
          await finishInterview();
        }
      }
    } catch (error: any) {
      console.error('❌ Failed to load rounds:', error);
      setError(error.message || 'Failed to load rounds');
    }
  };

  const startRound = async (roundOverride?: Round) => {
    const roundToStart = roundOverride || currentRound;
    if (!roundToStart) return;
    if (isBusyRef.current) return;
    
    setLoading(true);
    setError('');
    try {
      // Block concurrent round starts, but do NOT keep the lock during Q&A loop.
      isBusyRef.current = true;
      console.log('▶️ Starting round:', roundToStart.id);
      const question = await interviewService.startRound(interviewId, roundToStart.id);
      console.log('✅ Question received:', question);
      setCurrentRound(roundToStart);
      activeRoundRef.current = roundToStart;
      setCurrentQuestion(question);
      questionCounterRef.current += 1;

      // Release lock before entering the ask/listen loop
      isBusyRef.current = false;

      await handleQuestionAsked(question);
    } catch (error: any) {
      console.error('❌ Failed to start round:', error);
      setError(error.message || 'Failed to start round');
    } finally {
      // Ensure lock is released even if the API call fails
      isBusyRef.current = false;
      setLoading(false);
    }
  };

  const playQuestionAudio = async (audioUrl: string) => {
    return new Promise<boolean>((resolve) => {
      const audio = new Audio(`${API_BASE_URL}${audioUrl}`);
      audioRef.current = audio;
      audio.onended = () => resolve(true);
      audio.onerror = () => resolve(false);
      audio.play().catch(() => resolve(false));
    });
  };

  const speakWithBrowserTTS = async (text: string) => {
    if (!(window as any).speechSynthesis) return;

    await new Promise<void>((resolve) => {
      try {
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = 'en-US';
        utter.rate = 1;
        utter.onend = () => resolve();
        utter.onerror = () => resolve();
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utter);
      } catch {
        resolve();
      }
    });
  };

  const handleQuestionAsked = async (question: Question) => {
    if (!isMountedRef.current) return;

    setFeedback(null);
    setLiveTranscript('');
    setFinalTranscript('');

    if (audioMode) {
      setIsSpeakingQuestion(true);
      let played = false;
      if (question.audio_url) {
        played = await playQuestionAudio(question.audio_url);
      }
      if (!played) {
        await speakWithBrowserTTS(question.question_text);
      }
      setIsSpeakingQuestion(false);
    }

    await captureAndSubmitAnswer(question);
  };

  const captureAndSubmitAnswer = async (question: Question) => {
    if (isBusyRef.current) return;
    isBusyRef.current = true;

    const round = activeRoundRef.current;
    if (!round) {
      isBusyRef.current = false;
      return;
    }

    let result: AnswerFeedback | null = null;

    try {
      setIsListeningAnswer(true);

      const speechText = await transcribeWithSpeechRecognition();
      if (speechText && speechText.trim().length > 0) {
        setFinalTranscript(speechText);
        result = await submitTextAnswer(round.id, question.question_id, speechText);
      } else {
        const audioBlob = await recordAnswerWithVAD();
        result = await submitAudioAnswer(round.id, question.question_id, audioBlob);
      }
    } finally {
      setIsListeningAnswer(false);
      isBusyRef.current = false;
    }

    if (!isMountedRef.current || !result) return;

    setFeedback(result);

    if (result.next_question) {
      setCurrentQuestion(result.next_question);
      questionCounterRef.current += 1;
      await handleQuestionAsked(result.next_question);
      return;
    }

    setCurrentQuestion(null);
    setFeedback(null);
    await loadRounds(true);
  };

  const transcribeWithSpeechRecognition = async (): Promise<string> => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return '';

    return new Promise<string>((resolve) => {
      try {
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = true;
        recognition.continuous = false;

        let finalText = '';

        recognition.onresult = (event: any) => {
          let interim = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const res = event.results[i];
            const text = res[0]?.transcript || '';
            if (res.isFinal) {
              finalText += text;
            } else {
              interim += text;
            }
          }
          setLiveTranscript((finalText + ' ' + interim).trim());
        };

        recognition.onerror = () => resolve(finalText.trim());
        recognition.onend = () => resolve(finalText.trim());

        recognition.start();
      } catch {
        resolve('');
      }
    });
  };

  const recordAnswerWithVAD = async (): Promise<Blob> => {
    const stream = sessionStreamRef.current || (await navigator.mediaDevices.getUserMedia({ audio: true }));
    const audioStream = new MediaStream(stream.getAudioTracks());

    audioChunksRef.current = [];

    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm;codecs=opus' });
    } catch {
      recorder = new MediaRecorder(audioStream);
    }

    mediaRecorderRef.current = recorder;

    return new Promise<Blob>((resolve) => {
      let startedSpeaking = false;
      let silenceSince: number | null = null;

      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const source = ctx.createMediaStreamSource(audioStream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      const data = new Uint8Array(analyser.fftSize);

      const stopAll = () => {
        try {
          if (recorder.state !== 'inactive') recorder.stop();
        } catch {
        }
      };

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        try {
          source.disconnect();
        } catch {
        }
        try {
          analyser.disconnect();
        } catch {
        }
        ctx.close().catch(() => undefined);

        const blobType = recorder.mimeType || 'audio/webm';
        resolve(new Blob(audioChunksRef.current, { type: blobType }));
      };

      recorder.start();
      setIsRecording(true);

      const tick = () => {
        if (recorder.state === 'inactive') return;
        analyser.getByteTimeDomainData(data);

        let sum = 0;
        for (let i = 0; i < data.length; i++) {
          const v = (data[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / data.length);

        const now = performance.now();
        const speaking = rms > 0.03;

        if (speaking) {
          startedSpeaking = true;
          silenceSince = null;
        } else if (startedSpeaking) {
          if (silenceSince == null) silenceSince = now;
          if (now - silenceSince > 1400) {
            setIsRecording(false);
            stopAll();
            return;
          }
        }

        requestAnimationFrame(tick);
      };

      requestAnimationFrame(tick);

      setTimeout(() => {
        if (recorder.state !== 'inactive') {
          setIsRecording(false);
          stopAll();
        }
      }, 45000);
    });
  };

  const submitTextAnswer = async (roundId: string, questionId: number, answerText: string): Promise<AnswerFeedback> => {
    if (!answerText.trim()) {
      throw new Error('Answer cannot be empty');
    }
    
    setLoading(true);
    setError('');
    try {
      const result = await interviewService.submitTextAnswer(
        interviewId,
        roundId,
        questionId,
        answerText
      );

      return result;
    } catch (error: any) {
      console.error('❌ Failed to submit answer:', error);
      setError(error.message || 'Failed to submit answer');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const submitAudioAnswer = async (roundId: string, questionId: number, audioBlob: Blob): Promise<AnswerFeedback> => {
    
    setLoading(true);
    setError('');
    try {
      const result = await interviewService.submitAudioAnswer(
        interviewId,
        roundId,
        questionId,
        audioBlob
      );

      return result;
    } catch (error: any) {
      console.error('❌ Failed to submit audio:', error);
      setError(error.message || 'Failed to submit audio answer');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const finishInterview = async () => {
    try {
      await interviewService.completeInterview(interviewId);
      await stopAndPreviewRecording();
    } catch (error) {
      console.error('Failed to complete interview:', error);
    }
  };

  const stopAndPreviewRecording = async () => {
    try {
      if (!sessionRecorderRef.current) {
        onEnd();
        return;
      }

      await new Promise<void>((resolve) => {
        const recorder = sessionRecorderRef.current!;
        if (recorder.state === 'inactive') {
          resolve();
          return;
        }
        recorder.onstop = () => resolve();
        recorder.stop();
      });

      const blob = new Blob(sessionChunksRef.current, { type: 'video/webm' });
      const url = URL.createObjectURL(blob);
      setVideoPreviewUrl(url);
    } catch {
      onEnd();
    } finally {
      cleanupMedia();
    }
  };

  const closeVideoPreview = () => {
    if (videoPreviewUrl) {
      URL.revokeObjectURL(videoPreviewUrl);
    }
    setVideoPreviewUrl(null);
    onEnd();
  };

  return (
    <div className="max-w-4xl mx-auto p-6 min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {videoPreviewUrl && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-6">
          <div className="w-full max-w-3xl bg-slate-900 border border-white/10 rounded-3xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Interview Recording Preview</h3>
              <button
                onClick={closeVideoPreview}
                className="px-4 py-2 border border-white/20 rounded-xl hover:bg-white/10 transition-all"
              >
                Continue
              </button>
            </div>
            <video
              src={videoPreviewUrl}
              controls
              autoPlay
              className="w-full rounded-2xl bg-black"
            />
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-6 flex justify-between items-center bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
        <h2 className="text-2xl font-light">Mock Interview</h2>
        <div className="flex gap-4">
          <button
            onClick={onBack}
            className="px-4 py-2 border border-white/20 rounded-xl hover:bg-white/10 transition-all"
          >
            Exit
          </button>
        </div>
      </div>

      <div className="mb-6 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
          <div className="rounded-2xl overflow-hidden bg-black">
            <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
          </div>
          <div className="space-y-3">
            <div className="text-sm text-white/60">Status</div>
            <div className="text-white">
              {isSpeakingQuestion ? 'Asking question…' : isListeningAnswer ? 'Listening…' : loading ? 'Working…' : 'Ready'}
            </div>
            {liveTranscript && (
              <div className="p-3 bg-white/5 border border-white/10 rounded-2xl">
                <div className="text-xs text-white/60 mb-1">Transcript</div>
                <div className="text-sm text-white/90 whitespace-pre-wrap">{liveTranscript}</div>
              </div>
            )}
            {isRecording && (
              <div className="text-sm text-red-300">Recording answer…</div>
            )}
          </div>
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
            onClick={() => startRound()}
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
          <div className="text-center py-8 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl">
            <p className="text-sm text-white/60 mb-2">Voice mode is enabled</p>
            <p className="text-white/80">
              {isSpeakingQuestion ? 'Please listen to the question…' : isListeningAnswer ? 'Answer now…' : 'Preparing…'}
            </p>
          </div>
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
                  void loadRounds(true);
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
            onClick={finishInterview}
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
