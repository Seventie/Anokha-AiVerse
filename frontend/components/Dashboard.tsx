import React, { useState, useEffect } from 'react';
import { User } from '../services/authService';
import { aiService } from '../services/aiService';
import { 
  LayoutDashboard, 
  Map as MapIcon, 
  FileSearch, 
  Briefcase, 
  BookOpen, 
  Mic2, 
  LogOut, 
  Sparkles, 
  TrendingUp,
  AlertCircle,
  BrainCircuit,
  History,
  CheckCircle2,
  Loader2,
  MapPin,
  Calendar,
  ArrowRight,
  Save
} from 'lucide-react';

interface DashboardProps {
  user: User;
  onLogout: () => void;
}

type Tab = 'snapshot' | 'roadmap' | 'opportunities' | 'resume' | 'journal' | 'interviews' | 'summary';

const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState<Tab>('snapshot');
  const [reasoning, setReasoning] = useState<string>('Initializing neural strategy layer...');
  const [roadmap, setRoadmap] = useState<any[]>([]);
  const [journal, setJournal] = useState<string>('');
  const [isGeneratingRoadmap, setIsGeneratingRoadmap] = useState(false);
  const [isJournalSaving, setIsJournalSaving] = useState(false);
  
  const [alerts] = useState<string[]>([
    `Market Alert: Demand for ${user.targetRole} in ${user.preferredLocations?.[0] || 'Remote'} is up 12%.`,
    'Agent Update: Strategy evolved based on recent profile additions.'
  ]);

  // Load journal from localStorage on mount
  useEffect(() => {
    const storedJournal = localStorage.getItem(`journal_${user.id}`);
    if (storedJournal) {
      setJournal(storedJournal);
    }
  }, [user.id]);

  const fetchReasoning = async () => {
    setReasoning('Consulting AI for strategic analysis...');
    try {
      const data = await aiService.getAgentReasoning(user);
      setReasoning(data || "Strategy layer operational.");
    } catch (error: any) {
      setReasoning("Strategic layer currently recalibrating.");
    }
  };

  const fetchRoadmap = async () => {
    const cached = localStorage.getItem(`roadmap_${user.id}`);
    if (cached) {
      setRoadmap(JSON.parse(cached));
      return;
    }

    setIsGeneratingRoadmap(true);
    try {
      const data = await aiService.generateRoadmap(user);
      if (data) {
        setRoadmap(data);
        localStorage.setItem(`roadmap_${user.id}`, JSON.stringify(data));
      }
    } catch (err) {
      console.error("Roadmap generation failed", err);
    } finally {
      setIsGeneratingRoadmap(false);
    }
  };

  useEffect(() => {
    fetchReasoning();
    fetchRoadmap();
  }, [user.id]);

  const saveJournal = () => {
    setIsJournalSaving(true);
    try {
      localStorage.setItem(`journal_${user.id}`, journal);
      // Show success feedback
      setTimeout(() => setIsJournalSaving(false), 500);
    } catch (err) {
      console.error("Failed to save journal", err);
      setIsJournalSaving(false);
    }
  };

  const navItems = [
    { id: 'snapshot', label: 'Snapshot', icon: LayoutDashboard },
    { id: 'roadmap', label: 'Roadmap', icon: MapIcon },
    { id: 'opportunities', label: 'Opportunities', icon: Briefcase },
    { id: 'resume', label: 'Resume Intelligence', icon: FileSearch },
    { id: 'journal', label: 'Career Journal', icon: BookOpen },
    { id: 'interviews', label: 'Interview Practice', icon: Mic2 },
    { id: 'summary', label: 'Weekly Summary', icon: History },
  ];

  return (
    <div className="flex h-screen w-full bg-transparent overflow-hidden font-inter text-white">
      {/* 1. SIDEBAR */}
      <aside className="w-72 bg-white/[0.02] border-r border-white/10 backdrop-blur-3xl flex flex-col p-8 z-20 flex-shrink-0">
        <div className="mb-12">
          <span className="text-3xl font-serif italic text-primary">adviceguide</span>
          <p className="text-[10px] text-primary/40 uppercase tracking-[0.4em] mt-2 font-bold">Agent Active</p>
        </div>

        <nav className="flex-1 space-y-1.5 overflow-y-auto custom-scroll">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id as Tab)}
              className={`w-full flex items-center gap-4 px-5 py-3 rounded-2xl transition-all group ${
                activeTab === item.id 
                  ? 'bg-primary/10 text-primary border border-primary/20 font-medium' 
                  : 'text-white/40 hover:text-white hover:bg-white/5'
              }`}
            >
              <item.icon className={`w-4 h-4 ${activeTab === item.id ? 'text-primary' : 'group-hover:text-primary'}`} />
              <span className="text-sm tracking-wide">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="pt-8 border-t border-white/5 space-y-2">
          <button onClick={onLogout} className="w-full flex items-center gap-4 px-5 py-3 rounded-2xl text-white/40 hover:text-red-400 transition-all text-sm">
            <LogOut className="w-4 h-4" />
            <span className="text-xs uppercase font-bold tracking-widest">End Session</span>
          </button>
        </div>
      </aside>

      {/* 2. MAIN */}
      <main className="flex-1 overflow-y-auto relative p-10 lg:p-14 custom-scroll">
        <div className="max-w-4xl mx-auto space-y-10 pb-20">
          <header className="flex justify-between items-end">
            <div>
              <p className="text-primary/60 text-[10px] font-bold uppercase tracking-[0.4em] mb-1">Continuity Loop Active</p>
              <h1 className="text-4xl font-light tracking-tight text-white">
                {navItems.find(n => n.id === activeTab)?.label}
              </h1>
            </div>
            <div className="text-right">
              <p className="text-white/20 text-[10px] uppercase tracking-widest mb-1 font-bold">Authenticated Profile</p>
              <p className="text-white font-medium text-lg">{user.fullName}</p>
            </div>
          </header>

          <div className="space-y-8 min-h-[600px]">
            {activeTab === 'snapshot' && <SnapshotSection user={user} />}
            {activeTab === 'roadmap' && <RoadmapSection roadmap={roadmap} isLoading={isGeneratingRoadmap} />}
            {activeTab === 'opportunities' && <OpportunitiesSection user={user} />}
            {activeTab === 'resume' && <ResumeIntelligenceSection />}
            {activeTab === 'journal' && <JournalSection content={journal} setContent={setJournal} onSave={saveJournal} isSaving={isJournalSaving} />}
            {activeTab === 'interviews' && <InterviewSection />}
            {activeTab === 'summary' && <SummarySection user={user} />}
          </div>
        </div>
      </main>

      {/* 3. MENTOR SIDEBAR */}
      <aside className="w-80 bg-white/[0.01] border-l border-white/10 backdrop-blur-md p-8 flex flex-col gap-8 overflow-y-auto flex-shrink-0 custom-scroll">
        <section className="space-y-4">
          <div className="flex items-center gap-3 text-primary">
            <BrainCircuit className="w-4 h-4" />
            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em]">Mentor reasoning</h3>
          </div>
          <div className="bg-white/[0.03] border border-white/10 p-6 rounded-[2rem] text-sm leading-relaxed text-white/75 italic font-light shadow-xl">
            {reasoning.split('\n').map((line, i) => (
              <p key={i} className="mb-3 last:mb-0">{line}</p>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-3 text-amber-400/80">
            <AlertCircle className="w-4 h-4" />
            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em]">Environment Nudges</h3>
          </div>
          <div className="space-y-2">
            {alerts.map((alert, i) => (
              <div key={i} className="bg-white/[0.02] border border-white/10 p-4 rounded-xl text-xs text-white/75 flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                {alert}
              </div>
            ))}
          </div>
        </section>

        <section className="mt-auto space-y-4">
          <div className="bg-primary/5 border border-primary/20 rounded-2xl p-4 flex items-center justify-between">
            <div>
              <p className="text-[9px] text-primary/60 uppercase font-bold tracking-widest">System Status</p>
              <p className="text-white text-xs font-medium">Evolution Mode</p>
            </div>
            <div className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />
          </div>
          <p className="text-[9px] text-white/30 text-center uppercase tracking-widest px-4 leading-relaxed">
            Neural insights generated by AI.
          </p>
        </section>
      </aside>
    </div>
  );
};

/* --- Section Components --- */

const SnapshotSection = ({ user }: { user: User }) => {
  const technicalSkillsCount = user.skills?.technical?.length || 0;
  const readiness = Math.min(Math.round((technicalSkillsCount / 10) * 100), 100);
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="bg-white/[0.04] border border-white/15 rounded-[2.5rem] p-8 space-y-6 shadow-xl">
        <div className="flex justify-between items-start">
          <h3 className="text-white/40 text-[10px] font-bold uppercase tracking-[0.2em]">Readiness Score</h3>
          <TrendingUp className="w-5 h-5 text-primary" />
        </div>
        <div className="text-6xl font-light text-white">{readiness}<span className="text-xl opacity-20 ml-1">%</span></div>
        <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
          <div className="bg-primary h-full transition-all duration-1000" style={{ width: `${readiness}%` }} />
        </div>
        <p className="text-white/75 text-xs leading-relaxed font-light">
          Based on {technicalSkillsCount} verified technical capability nodes aligned to {user.targetRole}.
        </p>
      </div>
      <div className="bg-white/[0.04] border border-white/15 rounded-[2.5rem] p-8 space-y-6 shadow-xl">
        <h3 className="text-white/40 text-[10px] font-bold uppercase tracking-[0.2em]">Current Memory Path</h3>
        <div className="text-3xl font-serif italic text-primary">{user.fieldOfInterest}</div>
        <div className="space-y-2">
          <div className="flex items-center gap-3 text-white/75 text-sm font-light">
            <CheckCircle2 className="w-4 h-4 text-primary" />
            <span>Target: {user.targetRole}</span>
          </div>
          <div className="flex items-center gap-3 text-white/75 text-sm font-light">
            <Calendar className="w-4 h-4 text-primary" />
            <span>Timeline: {user.timeline} Convergence</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const RoadmapSection = ({ roadmap, isLoading }: { roadmap: any[], isLoading: boolean }) => (
  <div className="bg-white/[0.04] border border-white/15 rounded-[3rem] p-10 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 shadow-xl">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
         <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary shadow-inner">
           <MapIcon className="w-6 h-6" />
         </div>
         <div>
           <h3 className="text-2xl font-light text-white">Dynamic Learning Roadmap</h3>
           <p className="text-white/40 text-sm italic font-light">Evolving via Adaptive Logic</p>
         </div>
      </div>
      {isLoading && <Loader2 className="animate-spin text-primary w-6 h-6" />}
    </div>

    <div className="space-y-4">
      {roadmap.length > 0 ? roadmap.map((phase, i) => (
        <div key={i} className="flex flex-col gap-4 p-6 bg-white/5 rounded-2xl border border-white/10 group hover:border-primary/30 transition-all">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-[10px] font-bold text-primary uppercase tracking-[0.4em]">{phase.phase}</span>
              <h4 className="text-white font-medium text-lg">{phase.title}</h4>
            </div>
            <span className={`text-[9px] uppercase font-bold tracking-widest px-3 py-1 rounded-full ${i === 0 ? 'bg-primary/20 text-primary' : 'bg-white/5 text-white/20'}`}>
              {i === 0 ? 'ACTIVE' : 'QUEUED'}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {phase.tasks.map((task: string, j: number) => (
              <div key={j} className="flex items-center gap-3 text-sm text-white/75 font-light">
                <div className="w-1.5 h-1.5 rounded-full bg-primary/40" />
                {task}
              </div>
            ))}
          </div>
        </div>
      )) : (
        <div className="py-20 text-center text-white/20 italic font-light">Generating personalized learning vectors...</div>
      )}
    </div>
  </div>
);

const OpportunitiesSection = ({ user }: { user: User }) => (
  <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
    <div className="flex items-center justify-between px-2">
      <h3 className="text-white/40 text-[10px] font-bold uppercase tracking-[0.2em]">Market Matches in {user.preferredLocations?.[0] || 'Remote'}</h3>
      <span className="text-primary text-[10px] font-bold uppercase tracking-widest">Updated {new Date().toLocaleDateString()}</span>
    </div>
    <div className="grid grid-cols-1 gap-4">
      {[
        { role: user.targetRole, company: 'Leading Edge AI', match: '94%', tag: 'High Alignment' },
        { role: `Senior ${user.targetRole}`, company: 'Global Systems', match: '89%', tag: 'Recommended' },
        { role: 'Product Solutions Architect', company: 'Future Corp', match: '82%', tag: 'Stretch Role' }
      ].map((job, i) => (
        <div key={i} className="p-8 bg-white/[0.04] border border-white/15 rounded-[2.5rem] hover:bg-white/[0.06] transition-all flex items-center justify-between group shadow-lg">
          <div className="space-y-2">
            <div className="flex items-center gap-4">
              <span className="text-xl font-medium text-white">{job.role}</span>
              <span className="px-3 py-1 bg-primary/10 text-primary text-[9px] font-bold uppercase rounded-full tracking-widest">{job.tag}</span>
            </div>
            <div className="flex items-center gap-4 text-white/40 text-xs">
              <span className="flex items-center gap-1"><Briefcase size={12}/> {job.company}</span>
              <span className="flex items-center gap-1"><MapPin size={12}/> {user.preferredLocations?.[0] || 'Remote'}</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-[10px] uppercase text-white/30 font-bold mb-1 tracking-widest">Compatibility</p>
            <p className="text-4xl font-serif text-primary">{job.match}</p>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const JournalSection = ({ content, setContent, onSave, isSaving }: any) => (
  <div className="bg-white/[0.04] border border-white/15 rounded-[3rem] p-10 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 shadow-xl">
    <div className="flex justify-between items-center">
      <div className="space-y-1">
        <h3 className="text-2xl font-serif italic text-primary">Private Career Journal</h3>
        <p className="text-white/40 text-sm font-light">Reflections are persisted locally and used for mentor context.</p>
      </div>
      <button 
        onClick={onSave} 
        disabled={isSaving}
        className="flex items-center gap-3 px-6 py-3 bg-primary text-bg-deep font-bold rounded-2xl hover:scale-[1.05] active:scale-[0.95] transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSaving ? <Loader2 size={18} className="animate-spin"/> : <Save size={18}/>}
        <span className="text-xs uppercase tracking-widest">{isSaving ? 'Saving...' : 'Persist'}</span>
      </button>
    </div>
    <textarea 
      value={content}
      onChange={(e) => setContent(e.target.value)}
      placeholder="Capture thoughts on today's evolution, friction points, or long-term vision..." 
      className="w-full bg-white/5 border border-white/10 rounded-[2rem] p-8 min-h-[400px] text-white placeholder-white/10 focus:outline-none focus:border-primary/40 transition-all font-light leading-relaxed text-lg"
    />
  </div>
);

const ResumeIntelligenceSection = () => (
  <div className="bg-white/[0.04] border border-white/15 rounded-[3rem] p-10 space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700 shadow-xl">
    <div className="flex justify-between items-start">
      <div className="space-y-2">
        <h3 className="text-2xl font-light">Resume Lab</h3>
        <p className="text-white/40 text-sm italic">Analysis powered by CareerAI Logic</p>
      </div>
      <button className="px-8 py-4 rounded-full border border-primary/40 text-primary text-[10px] font-bold uppercase hover:bg-primary hover:text-bg-deep transition-all tracking-widest shadow-lg">Analyze Latest CV</button>
    </div>
    
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="p-8 bg-white/5 rounded-[2rem] space-y-4 border border-white/10">
        <h4 className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Memory Strengths</h4>
        <ul className="space-y-4 text-sm text-white/75 font-light">
          <li className="flex items-start gap-3"><CheckCircle2 className="w-5 h-5 text-primary shrink-0" /> Quantified impact nodes detected in primary experience.</li>
          <li className="flex items-start gap-3"><CheckCircle2 className="w-5 h-5 text-primary shrink-0" /> Technical keywords align with 94% of market requirements.</li>
        </ul>
      </div>
      <div className="p-8 bg-white/5 rounded-[2rem] space-y-4 border border-amber-400/20">
        <h4 className="text-[10px] font-bold text-amber-400/60 uppercase tracking-widest">Strategic Adjustments</h4>
        <ul className="space-y-4 text-sm text-white/75 font-light">
          <li className="flex items-start gap-3"><Sparkles className="w-5 h-5 text-primary shrink-0" /> Bolster architectural leadership narratives for staff roles.</li>
          <li className="flex items-start gap-3"><Sparkles className="w-5 h-5 text-primary shrink-0" /> Synthesize project descriptions for maximum ATS resonance.</li>
        </ul>
      </div>
    </div>
  </div>
);

const InterviewSection = () => (
  <div className="bg-white/[0.04] border border-white/15 rounded-[3rem] p-12 space-y-10 text-center flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-700 shadow-xl">
    <div className="space-y-4 max-w-lg">
      <div className="w-20 h-20 rounded-3xl bg-primary/10 flex items-center justify-center text-primary mx-auto mb-4">
        <Mic2 className="w-10 h-10" />
      </div>
      <h3 className="text-4xl font-light text-white">Neural Voice Practice</h3>
      <p className="text-white/75 text-lg font-light leading-relaxed">Prepare for high-stakes conversations with a simulated interviewer. Real-time behavior feedback powered by native audio agents.</p>
    </div>
    <button className="w-full max-w-sm py-8 rounded-[2rem] bg-primary text-bg-deep font-bold text-xl tracking-[0.2em] hover:shadow-[0_0_60px_rgba(212,212,170,0.5)] transition-all transform hover:scale-105 active:scale-95">INITIALIZE MOCK ROUND</button>
    <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.3em]">Microphone Access Required</p>
  </div>
);

const SummarySection = ({ user }: { user: User }) => (
  <div className="bg-white/[0.04] border border-white/15 rounded-[3rem] p-12 space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700 shadow-xl">
    <div className="flex justify-between items-start border-b border-white/10 pb-8">
      <div>
        <h3 className="text-3xl font-serif italic text-primary">Bi-Weekly Synthesis</h3>
        <p className="text-white/40 text-sm font-light mt-1">Timeline Convergence: {user.timeline}</p>
      </div>
      <span className="text-primary/40 text-[10px] font-bold uppercase tracking-[0.3em] bg-white/5 px-4 py-2 rounded-full border border-white/5">Continuity Active</span>
    </div>
    <div className="space-y-10">
      <p className="text-white/85 font-light leading-relaxed text-xl italic">"Your trajectory has shown a significant positive delta in architectural reasoning. The transition to {user.targetRole} is currently on track for a {user.timeline} landing."</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-8 bg-white/5 rounded-3xl border border-white/5 text-center shadow-inner">
          <p className="text-primary text-5xl font-serif mb-3 italic">14</p>
          <p className="text-[10px] uppercase font-bold text-white/30 tracking-[0.3em]">Evolution Sprints</p>
        </div>
        <div className="p-8 bg-white/5 rounded-3xl border border-white/5 text-center shadow-inner">
          <p className="text-primary text-5xl font-serif mb-3 italic">6</p>
          <p className="text-[10px] uppercase font-bold text-white/30 tracking-[0.3em]">Market Signals</p>
        </div>
        <div className="p-8 bg-white/5 rounded-3xl border border-white/5 text-center shadow-inner">
          <p className="text-primary text-5xl font-serif mb-3 italic">High</p>
          <p className="text-[10px] uppercase font-bold text-white/30 tracking-[0.3em]">Agent Confidence</p>
        </div>
      </div>

      <div className="flex justify-center pt-6">
        <button className="flex items-center gap-4 text-white/40 hover:text-white transition-all group">
          <span className="text-[10px] font-bold uppercase tracking-[0.4em]">Review Historical Memory</span>
          <ArrowRight size={16} className="group-hover:translate-x-3 transition-transform" />
        </button>
      </div>
    </div>
  </div>
);

export default Dashboard;