// frontend/src/components/Dashboard/InterviewModule.tsx

import React, { useState } from 'react';
import { User } from '../../services/authService';
import InterviewSetup from '../Interview/InterviewSetup';
import InterviewRoom from '../Interview/InterviewRoom';
import InterviewResults from '../Interview/InterviewResults';
import InterviewAnalytics from '../Interview/InterviewAnalytics';
import { ArrowLeft, BarChart3, Mic, PlayCircle, LineChart } from 'lucide-react';

type View = 'menu' | 'setup' | 'interview' | 'results' | 'analytics';

interface InterviewModuleProps {
  user: User;
}

const InterviewModule: React.FC<InterviewModuleProps> = ({ user }) => {
  const [currentView, setCurrentView] = useState<View>('menu');
  const [currentInterviewId, setCurrentInterviewId] = useState<string | null>(null);

  const handleInterviewCreated = (interviewId: string) => {
    console.log('✅ Interview created:', interviewId);
    setCurrentInterviewId(interviewId);
    setCurrentView('interview');
  };

  const handleInterviewComplete = () => {
    console.log('✅ Interview completed');
    setCurrentView('results');
  };

  const handleBackToMenu = () => {
    console.log('🔄 Back to menu');
    setCurrentInterviewId(null);
    setCurrentView('menu');
  };

  return (
    <div className="min-h-screen w-full text-white -m-8"> {/* -m-8 to counteract dashboard padding */}
      
      {/* Back Button */}
      {currentView !== 'menu' && (
        <header className="w-full border-b border-white/10 px-6 md:px-12 py-4 flex items-center justify-between bg-[#0b1714]">
          <button
            onClick={handleBackToMenu}
            className="inline-flex items-center gap-2 text-sm font-light text-white/70 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Interview Menu</span>
          </button>
        </header>
      )}

      {/* Menu View */}
      {currentView === 'menu' && (
        <section className="min-h-screen flex flex-col justify-center px-8 md:px-24 pt-24 bg-gradient-to-br from-[#0f231e] via-[#1a2f2a] to-[#0f231e]">
          <div className="max-w-[1400px] mx-auto hero-content space-y-16">
            <div>
              <h1 className="text-5xl md:text-7xl font-light leading-[0.95] tracking-tight text-white mb-6">
                Simulate real <span className="font-serif italic text-primary">interviews</span>
                <br /> with agentic feedback.
              </h1>
              <p className="text-white/80 max-w-xl text-lg font-light">
                Run structured mock interviews with AI, get granular feedback, and track your progress
                across multiple rounds, companies, and skills.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              {/* Start Interview Card */}
              <button
                onClick={() => setCurrentView('setup')}
                className="group relative p-10 rounded-[2.5rem] bg-white/[0.06] border border-white/15 hover:border-primary/60 transition-all duration-500 backdrop-blur-sm flex flex-col justify-between shadow-2xl shadow-black/40"
              >
                <div>
                  <div className="w-14 h-14 rounded-2xl bg-primary/15 flex items-center justify-center text-primary mb-8 group-hover:bg-primary group-hover:text-white transition-all duration-500">
                    <PlayCircle className="w-7 h-7" />
                  </div>
                  <h2 className="text-2xl md:text-3xl font-medium text-white mb-4 tracking-tight">
                    Start Mock Interview
                  </h2>
                  <p className="text-white/80 font-light text-sm md:text-base">
                    Configure company, topics, and rounds. Practice with realistic questions and live feedback.
                  </p>
                </div>
                <div className="mt-10 flex items-center gap-4 text-primary group-hover:translate-x-2 transition-transform duration-500">
                  <span className="text-[11px] font-bold tracking-[0.25em] uppercase opacity-75 group-hover:opacity-100">
                    Initialize
                  </span>
                  <div className="w-10 h-px bg-primary/70 group-hover:w-16 group-hover:bg-primary transition-all duration-500" />
                  <Mic className="w-4 h-4" />
                </div>
              </button>

              {/* Analytics Card */}
              <button
                onClick={() => setCurrentView('analytics')}
                className="group relative p-10 rounded-[2.5rem] bg-white/[0.06] border border-white/15 hover:border-primary/60 transition-all duration-500 backdrop-blur-sm flex flex-col justify-between shadow-2xl shadow-black/40"
              >
                <div>
                  <div className="w-14 h-14 rounded-2xl bg-primary/15 flex items-center justify-center text-primary mb-8 group-hover:bg-primary group-hover:text-white transition-all duration-500">
                    <BarChart3 className="w-7 h-7" />
                  </div>
                  <h2 className="text-2xl md:text-3xl font-medium text-white mb-4 tracking-tight">
                    Interview Analytics
                  </h2>
                  <p className="text-white/80 font-light text-sm md:text-base">
                    Review performance trends, scores, and areas of improvement across your interviews.
                  </p>
                </div>
                <div className="mt-10 flex items-center gap-4 text-primary group-hover:translate-x-2 transition-transform duration-500">
                  <span className="text-[11px] font-bold tracking-[0.25em] uppercase opacity-75 group-hover:opacity-100">
                    Inspect
                  </span>
                  <div className="w-10 h-px bg-primary/70 group-hover:w-16 group-hover:bg-primary transition-all duration-500" />
                  <LineChart className="w-4 h-4" />
                </div>
              </button>

              {/* Coming Soon Card */}
              <div className="relative p-10 rounded-[2.5rem] bg-white/[0.03] border border-white/10 backdrop-blur-sm flex flex-col justify-between opacity-70">
                <div>
                  <div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center text-white/70 mb-8">
                    <BarChart3 className="w-7 h-7" />
                  </div>
                  <h2 className="text-2xl md:text-3xl font-medium text-white/80 mb-4 tracking-tight">
                    Coming Soon
                  </h2>
                  <p className="text-white/60 font-light text-sm md:text-base">
                    Scenario-based roleplays and system design whiteboard interviews.
                  </p>
                </div>
              </div>
            </div>

            <p className="text-[11px] text-white/40 tracking-[0.3em] uppercase">
              Mock Interview Engine • CareerAI
            </p>
          </div>
        </section>
      )}

      {/* Setup View */}
      {currentView === 'setup' && (
        <div className="bg-[#0b1714] min-h-screen">
          <InterviewSetup 
            user={user}
            onInterviewCreated={handleInterviewCreated} 
            onCancel={handleBackToMenu} 
          />
        </div>
      )}

      {/* Interview Room View */}
      {currentView === 'interview' && currentInterviewId && (
        <div className="bg-[#0b1714] min-h-screen">
          <InterviewRoom
            interviewId={currentInterviewId}
            user={user}
            onComplete={handleInterviewComplete}
            onCancel={handleBackToMenu}
          />
        </div>
      )}

      {/* Results View */}
      {currentView === 'results' && currentInterviewId && (
        <div className="bg-[#0b1714] min-h-screen">
          <InterviewResults 
            interviewId={currentInterviewId} 
            user={user}
            onBackToSetup={handleBackToMenu} 
          />
        </div>
      )}

      {/* Analytics View */}
      {currentView === 'analytics' && (
        <div className="px-8 md:px-24 py-16 max-w-[1400px] mx-auto bg-gradient-to-br from-[#0f231e] via-[#1a2f2a] to-[#0f231e] min-h-screen">
          <h2 className="text-3xl md:text-4xl font-medium mb-8 text-white">
            Interview <span className="font-serif italic text-primary">Analytics</span>
          </h2>
          <InterviewAnalytics interviewId={currentInterviewId || ''} />
        </div>
      )}
    </div>
  );
};

export default InterviewModule;
