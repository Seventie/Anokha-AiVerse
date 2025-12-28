// frontend/src/components/Interview/InterviewPage.tsx

import React, { useState } from 'react';
import { User } from '../../services/authService';
import InterviewSetup from './InterviewSetup';
import InterviewRoom from './InterviewRoom';
import InterviewResults from './InterviewResults';
import { ArrowLeft } from 'lucide-react';

type InterviewStage = 'setup' | 'room' | 'results';

interface InterviewPageProps {
  user: User;
  onBack: () => void;
}

const InterviewPage: React.FC<InterviewPageProps> = ({ user, onBack }) => {
  const [stage, setStage] = useState<InterviewStage>('setup');
  const [interviewId, setInterviewId] = useState<string | null>(null);

  const handleInterviewCreated = (id: string) => {
    setInterviewId(id);
    setStage('room');
  };

  const handleCancelSetup = () => {
    onBack();
  };

  const handleInterviewEnd = () => {
    setStage('results');
  };

  return (
    <div className="min-h-screen bg-[#0b1714] text-white">
      {/* Header only on setup */}
      {stage === 'setup' && (
        <header className="w-full border-b border-white/10 px-8 md:px-24 py-4 flex items-center justify-between">
          <button
            onClick={onBack}
            className="inline-flex items-center gap-2 text-sm font-light text-white/70 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </button>
          <span className="text-[11px] tracking-[0.3em] text-white/40 uppercase">
            Welcome, {user?.name}
          </span>
        </header>
      )}

      {stage === 'setup' && (
        <InterviewSetup onInterviewCreated={handleInterviewCreated} onCancel={handleCancelSetup} />
      )}

      {stage === 'room' && interviewId && (
        <InterviewRoom
          interviewId={interviewId}
          onInterviewEnd={handleInterviewEnd}
          onCancel={handleCancelSetup}
        />
      )}

      {stage === 'results' && interviewId && (
        <InterviewResults interviewId={interviewId} onBackHome={onBack} />
      )}
    </div>
  );
};

export default InterviewPage;
