// frontend/src/components/Interview/InterviewPage.tsx

import React, { useState } from 'react';
import { User } from '../../services/authService';
import InterviewSetup from './InterviewSetup';
import InterviewRoom from './InterviewRoom';
import InterviewResults from './InterviewResults';
import { ArrowLeft } from 'lucide-react';

interface InterviewPageProps {
  user: User;
  onBack: () => void;
}

type InterviewStage = 'setup' | 'room' | 'results';

const InterviewPage: React.FC<InterviewPageProps> = ({ user, onBack }) => {
  const [stage, setStage] = useState<InterviewStage>('setup');
  const [interviewId, setInterviewId] = useState<string | null>(null);

  // Handle interview creation from setup
  const handleInterviewCreated = (id: string) => {
    console.log('✅ Interview created with ID:', id);
    setInterviewId(id);
    setStage('room');
  };

  // Handle cancel from setup
  const handleCancelSetup = () => {
    console.log('❌ Interview setup cancelled');
    onBack(); // Go back to dashboard
  };

  // Handle interview completion
  const handleInterviewEnd = () => {
    console.log('✅ Interview ended');
    setStage('results');
  };

  // Handle back to setup from room
  const handleBackToSetup = () => {
    console.log('🔙 Back to setup');
    setStage('setup');
    setInterviewId(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header - Only show on setup stage */}
      {stage === 'setup' && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-slate-900/80 backdrop-blur-sm border-b border-white/10">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-white/60 hover:text-white transition-colors"
            >
              <ArrowLeft size={20} />
              <span>Back to Dashboard</span>
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className={stage === 'setup' ? 'pt-20' : ''}>
        {/* Setup Stage */}
        {stage === 'setup' && (
          <InterviewSetup 
            onInterviewCreated={handleInterviewCreated}
            onCancel={handleCancelSetup}
          />
        )}
        
        {/* Interview Room Stage */}
        {stage === 'room' && interviewId && (
          <InterviewRoom 
            interviewId={interviewId}
            onEnd={handleInterviewEnd}
            onBack={handleBackToSetup}
          />
        )}
        
        {/* Results Stage */}
        {stage === 'results' && interviewId && (
          <InterviewResults 
            sessionId={interviewId}
            onBackToSetup={handleBackToSetup}
            onBackToDashboard={onBack}
          />
        )}
      </div>
    </div>
  );
};

export default InterviewPage;
