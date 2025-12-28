// frontend/src/components/Interview/InterviewModule.tsx

import React, { useState } from 'react';
import InterviewSetup from './InterviewSetup';
import InterviewRoom from './InterviewRoom';
import InterviewResults from './InterviewResults';
import InterviewAnalytics from './InterviewAnalytics';

type View = 'menu' | 'setup' | 'interview' | 'results' | 'analytics';

const InterviewModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('menu');
  const [currentInterviewId, setCurrentInterviewId] = useState<string | null>(null);

  const handleInterviewCreated = (interviewId: string) => {
    setCurrentInterviewId(interviewId);
    setCurrentView('interview');
  };

  const handleInterviewComplete = () => {
    setCurrentView('results');
  };

  const handleBackToMenu = () => {
    setCurrentInterviewId(null);
    setCurrentView('menu');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      {currentView === 'menu' && (
        <div className="max-w-4xl mx-auto p-6">
          <h1 className="text-3xl font-bold mb-8">Mock Interview System</h1>
          
          <div className="grid grid-cols-2 gap-6">
            {/* Start New Interview */}
            <button
              onClick={() => setCurrentView('setup')}
              className="p-8 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-2xl hover:shadow-xl transition-shadow"
            >
              <div className="text-4xl mb-4">🎤</div>
              <h3 className="text-2xl font-bold mb-2">Start Interview</h3>
              <p className="opacity-90">Practice with AI interviewer</p>
            </button>

            {/* View Analytics */}
            <button
              onClick={() => setCurrentView('analytics')}
              className="p-8 bg-gradient-to-br from-green-500 to-teal-600 text-white rounded-2xl hover:shadow-xl transition-shadow"
            >
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-2xl font-bold mb-2">Analytics</h3>
              <p className="opacity-90">Track your progress</p>
            </button>
          </div>

          {/* Features */}
          <div className="mt-12 grid grid-cols-3 gap-6">
            <div className="text-center p-4">
              <div className="text-3xl mb-2">🎯</div>
              <h4 className="font-semibold mb-1">Realistic Questions</h4>
              <p className="text-sm text-gray-600">AI-generated interview questions</p>
            </div>
            <div className="text-center p-4">
              <div className="text-3xl mb-2">🎙️</div>
              <h4 className="font-semibold mb-1">Voice & Text</h4>
              <p className="text-sm text-gray-600">Answer via speech or typing</p>
            </div>
            <div className="text-center p-4">
              <div className="text-3xl mb-2">📈</div>
              <h4 className="font-semibold mb-1">Detailed Feedback</h4>
              <p className="text-sm text-gray-600">Comprehensive evaluation</p>
            </div>
          </div>
        </div>
      )}

      {currentView === 'setup' && (
        <InterviewSetup
          onInterviewCreated={handleInterviewCreated}
          onCancel={handleBackToMenu}
        />
      )}

      {currentView === 'interview' && currentInterviewId && (
        <InterviewRoom
          interviewId={currentInterviewId}
          onComplete={handleInterviewComplete}
          onExit={handleBackToMenu}
        />
      )}

      {currentView === 'results' && currentInterviewId && (
        <InterviewResults
          interviewId={currentInterviewId}
          onClose={handleBackToMenu}
        />
      )}

      {currentView === 'analytics' && (
        <InterviewAnalytics />
      )}
    </div>
  );
};

export default InterviewModule;
