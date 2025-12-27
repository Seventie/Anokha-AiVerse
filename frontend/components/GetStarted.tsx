import React, { useState, useEffect, useRef } from 'react';

import { authService, User } from '../services/authService';
import { aiService } from '../services/aiService';
import { 
  ArrowRight, 
  ChevronLeft, 
  Sparkles, 
  User as UserIcon, 
  Target, 
  Cpu, 
  Keyboard,
  Clock,
  Loader2,
  CheckCircle,
  Briefcase,
  GraduationCap,
  Code2,
  Plus,
  Trash2,
  Layers,
  Search,
  CheckCircle2,
  Upload,
  MapPin,
  X,
  Map as MapIcon,
  Globe,
  ChevronDown,
  Calendar
} from 'lucide-react';

const COMMON_SKILLS = [
  "React", "TypeScript", "Node.js", "Python", "Docker", "Kubernetes", "AWS", "Google Cloud",
  "SQL", "PostgreSQL", "System Design", "Agile", "Product Management", "Machine Learning",
  "Tailwind CSS", "Next.js", "Java", "Go", "Leadership", "Communication", "Strategic Planning",
  "Figma", "Rust", "Solidity", "TensorFlow", "PyTorch", "GraphQL", "Azure", "Terraform"
];

const ROLES = [
  "Software Engineer", "Data Scientist", "ML Engineer", "Product Manager", 
  "Quant Analyst", "Backend Engineer", "Frontend Engineer", "DevOps Engineer", 
  "Cybersecurity Analyst", "UI/UX Designer", "Full Stack Developer", "Blockchain Developer",
  "Cloud Architect", "Solution Architect", "Mobile Developer"
];

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

const YEARS = Array.from({ length: 40 }, (_, i) => new Date().getFullYear() - i);

interface GetStartedProps {
  onLogin: () => void;
  onSuccess: (user: User) => void;
}

const GetStarted: React.FC<GetStartedProps> = ({ onLogin, onSuccess }) => {
  const [step, setStep] = useState(1);
  const [isParsing, setIsParsing] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState('');
  const [inputMethod, setInputMethod] = useState<'ai' | 'manual' | null>(null);
  const [skillInput, setSkillInput] = useState('');
  const [skillSuggestions, setSkillSuggestions] = useState<string[]>([]);
  
  const [locationQuery, setLocationQuery] = useState('');
  const [locationSuggestions, setLocationSuggestions] = useState<string[]>([]);
  const [isSearchingLocation, setIsSearchingLocation] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [formData, setFormData] = useState<any>({
    email: '',
    username: '',
    password: '',
    fullName: '',
    location: '',
    preferredLocations: [],
    currentStatus: 'Working Professional',
    fieldOfInterest: 'Software Engineering',
    education: [{ institution: '', degree: '', major: '', location: '', duration: '' }],
    experience: [{ role: '', company: '', location: '', duration: '', description: '' }],
    projects: [{ title: '', description: '', techStack: '' }],
    skills: { technical: [], soft: [] },
    resumeText: '',
    availability: { freeTime: '2-4 hours', studyDays: [] },
    targetRole: 'Software Engineer',
    targetIndustry: '',
    timeline: '6 Months',
    visionStatement: ''
  });

  const steps = ["Account", "Identity", "Source", "Timeline", "Geography", "Logistics", "Strategic", "Verification"];

  useEffect(() => {
    if (skillInput.length > 1) {
      setSkillSuggestions(COMMON_SKILLS.filter(s => s.toLowerCase().includes(skillInput.toLowerCase()) && !formData.skills.technical.includes(s)));
    } else {
      setSkillSuggestions([]);
    }
  }, [skillInput, formData.skills.technical]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (locationQuery.length > 2) {
        setIsSearchingLocation(true);
        const results = await aiService.suggestLocations(locationQuery);
        setLocationSuggestions(results);
        setIsSearchingLocation(false);
      } else {
        setLocationSuggestions([]);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [locationQuery]);

  const handleNext = () => {
    if (step === 3 && inputMethod === 'manual') { setStep(4); return; }
    if (step === 4) { setStep(5); return; }
    if (step === 5 && formData.currentStatus !== 'Student') { setStep(7); return; }
    if (step < 8) setStep(step + 1);
    else handleFinalize();
  };

  const handleBack = () => {
    if (step === 7 && formData.currentStatus !== 'Student') { setStep(5); return; }
    if (step > 1) setStep(step - 1);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async (event) => {
      const text = event.target?.result as string;
      setFormData({ ...formData, resumeText: text });
      await handleAIParse(text);
    };
    reader.readAsText(file);
  };

  const handleAIParse = async (text: string) => {
    setIsParsing(true);
    const parsed = await aiService.parseResume(text);
    if (parsed) {
      setFormData((prev: any) => ({
        ...prev,
        fullName: parsed.fullName || prev.fullName,
        location: parsed.location || prev.location,
        education: (parsed.education && parsed.education.length > 0) ? parsed.education : prev.education,
        experience: (parsed.experience && parsed.experience.length > 0) ? parsed.experience : prev.experience,
        projects: (parsed.projects && parsed.projects.length > 0) ? parsed.projects : prev.projects,
        skills: parsed.skills || prev.skills
      }));
      setStep(4);
    }
    setIsParsing(false);
  };

  const handleFinalize = async () => {
    setIsRegistering(true);
    setError('');

    try {
      // Transform data to match backend schema
      const registrationData = {
        email: formData.email,
        username: formData.username,
        password: formData.password,
        fullName: formData.fullName,
        location: formData.location,
        preferredLocations: formData.preferredLocations,
        currentStatus: formData.currentStatus,
        fieldOfInterest: formData.fieldOfInterest,
        education: formData.education.map((edu: any) => ({
          institution: edu.institution,
          degree: edu.degree,
          major: edu.major || '',
          location: edu.location || '',
          duration: edu.duration
        })),
        experience: formData.experience.map((exp: any) => ({
          role: exp.role,
          company: exp.company,
          location: exp.location || '',
          duration: exp.duration,
          description: exp.description || ''
        })),
        projects: formData.projects.map((proj: any) => ({
          title: proj.title,
          description: proj.description || '',
          techStack: proj.techStack || ''
        })),
        skills: {
          technical: formData.skills.technical || [],
          soft: formData.skills.soft || []
        },
        availability: {
          freeTime: formData.availability.freeTime,
          studyDays: formData.availability.studyDays
        },
        targetRole: formData.targetRole,
        timeline: formData.timeline,
        visionStatement: formData.visionStatement
      };

      const user = await authService.register(registrationData);
      
      if (user) {
        onSuccess(user);
      } else {
        setError('Registration failed. Please try again.');
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsRegistering(false);
    }
  };

  const addItem = (key: string, initial: any) => {
    setFormData({ ...formData, [key]: [...formData[key], initial] });
  };

  const removeItem = (key: string, index: number) => {
    const list = [...formData[key]];
    list.splice(index, 1);
    setFormData({ ...formData, [key]: list });
  };

  const updateItem = (key: string, index: number, field: string, value: any) => {
    const list = [...formData[key]];
    list[index][field] = value;
    setFormData({ ...formData, [key]: list });
  };

  const addSkill = (skill: string) => {
    if (!formData.skills.technical.includes(skill)) {
      setFormData({
        ...formData,
        skills: { ...formData.skills, technical: [...formData.skills.technical, skill] }
      });
    }
    setSkillInput('');
  };

  const addPreferredLocation = (loc: string) => {
    if (formData.preferredLocations.length < 3 && !formData.preferredLocations.includes(loc)) {
      setFormData({ ...formData, preferredLocations: [...formData.preferredLocations, loc] });
    }
    setLocationQuery('');
    setLocationSuggestions([]);
  };

  return (
    <div className="relative w-full min-h-screen pt-12 pb-24 px-6 flex flex-col items-center overflow-x-hidden font-inter text-white">
      <div className="w-full max-w-4xl relative z-10">
        
        {/* Progress Tracker */}
        <div className="flex flex-col gap-4 mb-8 px-4 max-w-xl mx-auto">
          <div className="flex justify-between items-center text-[9px] font-bold uppercase tracking-[0.3em] text-white/20">
            <span>Stage 0{step}</span>
            <span className="text-primary tracking-[0.4em]">{steps[step-1]}</span>
            <span>{Math.round((step/8)*100)}%</span>
          </div>
          <div className="w-full h-1 bg-white/5 rounded-full flex gap-1">
            {steps.map((_, i) => (
              <div key={i} className={`flex-1 h-full rounded-full transition-all duration-700 ${i + 1 <= step ? 'bg-primary shadow-[0_0_10px_rgba(212,212,170,0.3)]' : 'bg-white/5'}`} />
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400 text-sm text-center">
            {error}
          </div>
        )}

        <div className="bg-white/[0.03] backdrop-blur-3xl border border-white/10 rounded-[3rem] p-8 md:p-12 shadow-2xl relative overflow-hidden">
          <div className="min-h-[500px] flex flex-col relative z-10">
            
            {/* STEP 1: ACCOUNT */}
            {step === 1 && (
              <StepLayout title="Identity Initialize" subtitle="Secure node access." icon={<Globe size={32} />}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
                  <DashInput label="Email Node" value={formData.email} onChange={(v: string) => setFormData({...formData, email: v})} />
                  <DashInput label="Neural Handle" value={formData.username} onChange={(v: string) => setFormData({...formData, username: v})} />
                  <div className="md:col-span-2">
                    <DashInput label="Secret Key" type="password" value={formData.password} onChange={(v: string) => setFormData({...formData, password: v})} />
                  </div>
                </div>
              </StepLayout>
            )}

            {/* STEP 2: PROFILE */}
            {step === 2 && (
              <StepLayout title="Professional Persona" subtitle="Fundamental parameters." icon={<UserIcon size={32} />}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
                  <DashInput label="Full Identity Name" value={formData.fullName} onChange={(v: string) => setFormData({...formData, fullName: v})} />
                  <DashInput label="Current Origin" placeholder="e.g. London, UK" value={formData.location} onChange={(v: string) => setFormData({...formData, location: v})} />
                  <DashSelect label="Current Loop Status" options={['Working Professional', 'Student', 'Career Switcher', 'Exploring']} value={formData.currentStatus} onChange={(v: string) => setFormData({...formData, currentStatus: v})} />
                  <DashSelect label="Target Neural Field" options={['Software Engineering', 'Data Science', 'Product Management', 'Design', 'Marketing', 'Finance']} value={formData.fieldOfInterest} onChange={(v: string) => setFormData({...formData, fieldOfInterest: v})} />
                </div>
              </StepLayout>
            )}

            {/* STEP 3: INGESTION */}
            {step === 3 && (
              <StepLayout title="Knowledge Sync" subtitle="Choose ingestion protocol." icon={<Layers size={32} />}>
                <div className="mt-8 space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <ChoiceCard 
                      active={inputMethod === 'ai'} 
                      icon={<Upload size={28} className="text-primary" />} 
                      title="AI Neural Parsing" 
                      desc="Directly transmit resume for auto-filling." 
                      onClick={() => setInputMethod('ai')} 
                    />
                    <ChoiceCard 
                      active={inputMethod === 'manual'} 
                      icon={<Keyboard size={28} className="text-white/40" />} 
                      title="Manual Construct" 
                      desc="Build timeline manually for precision." 
                      onClick={() => setInputMethod('manual')} 
                    />
                  </div>

                  {inputMethod === 'ai' && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
                      <div 
                        onClick={() => fileInputRef.current?.click()}
                        className="group w-full h-56 border-2 border-dashed border-white/10 rounded-[2.5rem] bg-white/[0.01] flex flex-col items-center justify-center cursor-pointer hover:border-primary/40 hover:bg-white/[0.04] transition-all"
                      >
                        <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileUpload} accept=".pdf,.txt,.docx" />
                        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform mb-4">
                          {isParsing ? <Loader2 size={28} className="animate-spin" /> : <Upload size={28} />}
                        </div>
                        <p className="text-xl font-light text-white mb-1">{isParsing ? 'Deconstructing Narrative...' : 'Drop Transmission or Click'}</p>
                        <p className="text-white/20 text-[9px] font-bold uppercase tracking-[0.2em]">Supported: PDF, DOCX, TXT</p>
                      </div>
                    </div>
                  )}
                </div>
              </StepLayout>
            )}

            {/* STEP 4: DETAIL MATRIX */}
            {step === 4 && (
              <StepLayout title="Detailed Chronology" subtitle="Verify milestones." icon={<Cpu size={32} />}>
                <div className="mt-6 space-y-12 max-h-[500px] overflow-y-auto pr-4 custom-scroll">
                  <SectionHeader title="Academic History" icon={<GraduationCap size={18}/>} onAdd={() => addItem('education', { institution: '', degree: '', major: '', location: '', duration: '' })} />
                  <div className="space-y-6">
                    {formData.education.map((edu: any, i: number) => (
                      <div key={i} className="relative p-8 bg-white/5 border border-white/10 rounded-[2.5rem] group hover:border-primary/20 transition-all">
                        {formData.education.length > 1 && <button onClick={() => removeItem('education', i)} className="absolute top-6 right-6 text-white/10 hover:text-red-400 transition-colors"><Trash2 size={16}/></button>}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                          <DashInput label="Institution" value={edu.institution} onChange={(v: string) => updateItem('education', i, 'institution', v)} />
                          <DashInput label="Degree Level" value={edu.degree} onChange={(v: string) => updateItem('education', i, 'degree', v)} />
                          <div className="md:col-span-2">
                            <DashInput label="Specialization" value={edu.major} onChange={(v: string) => updateItem('education', i, 'major', v)} />
                          </div>
                          <div className="md:col-span-2">
                            <ProfessionalMilestoneComponent 
                               label="Journey Duration & Location"
                               duration={edu.duration}
                               onDurationChange={(v: string) => updateItem('education', i, 'duration', v)}
                               location={edu.location}
                               onLocationChange={(v: string) => updateItem('education', i, 'location', v)}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <SectionHeader title="Professional Loop" icon={<Briefcase size={18}/>} onAdd={() => addItem('experience', { role: '', company: '', location: '', duration: '', description: '' })} />
                  <div className="space-y-6">
                    {formData.experience.map((exp: any, i: number) => (
                      <div key={i} className="relative p-8 bg-white/5 border border-white/10 rounded-[2.5rem] group hover:border-primary/20 transition-all">
                        {formData.experience.length > 1 && <button onClick={() => removeItem('experience', i)} className="absolute top-6 right-6 text-white/10 hover:text-red-400 transition-colors"><Trash2 size={16}/></button>}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                          <DashInput label="Role" value={exp.role} onChange={(v: string) => updateItem('experience', i, 'role', v)} />
                          <DashInput label="Entity" value={exp.company} onChange={(v: string) => updateItem('experience', i, 'company', v)} />
                          <div className="md:col-span-2">
                             <ProfessionalMilestoneComponent 
                                label="Career Node Details"
                                duration={exp.duration}
                                onDurationChange={(v: string) => updateItem('experience', i, 'duration', v)}
                                location={exp.location}
                                onLocationChange={(v: string) => updateItem('experience', i, 'location', v)}
                             />
                          </div>
                          <div className="md:col-span-2"><DashInput textarea label="Core Mission Results" value={exp.description} onChange={(v: string) => updateItem('experience', i, 'description', v)} /></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </StepLayout>
            )}

            {/* STEP 5: PREFERRED LOCATIONS */}
            {step === 5 && (
              <StepLayout title="Spatial Vectors" subtitle="Deployment zones." icon={<MapIcon size={32} />}>
                <div className="mt-8 space-y-8">
                  <div className="relative">
                    <div className="absolute left-6 top-1/2 -translate-y-1/2 text-white/20"><MapPin size={22}/></div>
                    <input 
                      type="text" 
                      placeholder="Sync with Maps..." 
                      className="w-full bg-white/5 border border-white/10 rounded-[2rem] pl-16 pr-6 py-6 text-xl text-white focus:outline-none focus:border-primary/50 transition-all font-light"
                      value={locationQuery}
                      onChange={(e) => setLocationQuery(e.target.value)}
                    />
                    {isSearchingLocation && <div className="absolute right-6 top-1/2 -translate-y-1/2"><Loader2 size={20} className="animate-spin text-primary"/></div>}
                  </div>

                  {locationSuggestions.length > 0 && (
                    <div className="space-y-2">
                      {locationSuggestions.map((loc, idx) => (
                        <button
                          key={idx}
                          onClick={() => addPreferredLocation(loc)}
                          className="w-full p-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-left transition-all"
                        >
                          <div className="flex items-center gap-3">
                            <MapPin size={18} className="text-primary" />
                            <span className="text-white">{loc}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {formData.preferredLocations.map((loc: string, i: number) => (
                      <div key={i} className="p-8 bg-primary/5 border border-primary/20 rounded-[2.5rem] flex flex-col justify-between items-start group">
                        <MapPin size={28} className="text-primary mb-6" />
                        <div className="w-full flex justify-between items-end">
                          <p className="text-xl font-medium text-white tracking-tight">{loc}</p>
                          <button onClick={() => setFormData({...formData, preferredLocations: formData.preferredLocations.filter((l:any)=>l!==loc)})} className="text-white/20 hover:text-red-400 transition-colors"><Trash2 size={16}/></button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </StepLayout>
            )}

            {/* STEP 6: TEMPORAL LOGISTICS */}
            {step === 6 && (
              <StepLayout title="Temporal Sync" subtitle="Growth cycle sync." icon={<Clock size={32} />}>
                <div className="mt-8 space-y-12">
                  <DashSelect label="Free Energy Per Cycle (Daily)" options={['1-2 hours', '2-4 hours', '4-6 hours', '6+ hours']} value={formData.availability.freeTime} onChange={(v: string) => setFormData({...formData, availability: {...formData.availability, freeTime: v}})} />
                  <div className="space-y-6">
                    <label className="text-[10px] font-bold text-white/20 uppercase tracking-[0.4em] ml-4">Intensive Study Cycles</label>
                    <div className="flex flex-wrap gap-4">
                      {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
                        <button key={day} onClick={() => {
                          const days = formData.availability.studyDays;
                          const next = days.includes(day) ? days.filter((d:any)=>d!==day) : [...days, day];
                          setFormData({...formData, availability: {...formData.availability, studyDays: next}});
                        }} className={`w-16 h-16 rounded-[1.5rem] border flex items-center justify-center font-bold text-sm transition-all ${formData.availability.studyDays.includes(day) ? 'bg-primary border-primary text-bg-deep shadow-[0_0_20px_rgba(212,212,170,0.3)] scale-110' : 'bg-white/5 border-white/5 text-white/30 hover:border-white/20'}`}>{day}</button>
                      ))}
                    </div>
                  </div>
                </div>
              </StepLayout>
            )}

            {/* STEP 7: STRATEGIC GOALS */}
            {step === 7 && (
              <StepLayout title="Strategic Terminal" subtitle="Terminal objective." icon={<Target size={32} />}>
                <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-10">
                  <DashSelect label="Target Neural Role" options={ROLES} value={formData.targetRole} onChange={(v: string) => setFormData({...formData, targetRole: v})} />
                  <DashSelect label="Timeline Convergence" options={['3 Months', '6 Months', '12 Months', 'Flexible']} value={formData.timeline} onChange={(v: string) => setFormData({...formData, timeline: v})} />
                  <div className="md:col-span-2"><DashInput textarea label="Mission Vision Directive" value={formData.visionStatement} onChange={(v: string) => setFormData({...formData, visionStatement: v})} /></div>
                </div>
              </StepLayout>
            )}

            {/* STEP 8: FINAL REVIEW */}
            {step === 8 && (
              <StepLayout title="Neural Finalization" subtitle="Verify dataset." icon={<CheckCircle size={32} />}>
                <div className="mt-6 space-y-8 max-h-[500px] overflow-y-auto pr-4 custom-scroll">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <FinalReviewCard label="Identity" value={formData.fullName} sub={formData.email} />
                    <FinalReviewCard label="State" value={formData.currentStatus} sub={formData.fieldOfInterest} />
                    <FinalReviewCard label="Origin" value={formData.location} sub={`${formData.preferredLocations.length} Vectors`} />
                    <FinalReviewCard label="Mission" value={formData.targetRole} sub={formData.timeline} />
                  </div>

                  <div className="p-16 bg-primary/10 border border-primary/20 rounded-[4rem] text-center mt-8 shadow-2xl">
                    <CheckCircle2 size={60} className="text-primary mx-auto mb-6 animate-pulse" />
                    <h4 className="text-4xl text-primary font-serif italic mb-4">Neural Sync Ready</h4>
                    <p className="text-white/40 text-lg font-light">Agent architecture primed for initialization.</p>
                  </div>
                </div>
              </StepLayout>
            )}

            <div className="mt-auto pt-16 flex items-center justify-between">
              <button onClick={handleBack} className={`flex items-center gap-3 text-white/20 hover:text-white transition-colors uppercase text-[10px] font-bold tracking-[0.3em] ${step === 1 ? 'invisible' : ''}`}><ChevronLeft size={16}/> Previous</button>
              <button 
                onClick={handleNext} 
                disabled={(step === 1 && (!formData.email || !formData.password || !formData.username)) || isRegistering} 
                className="group px-16 py-6 bg-primary text-bg-deep rounded-[2rem] font-bold tracking-[0.2em] flex items-center gap-8 hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] disabled:opacity-20 disabled:cursor-not-allowed transition-all transform active:scale-95 text-base"
              >
                {isRegistering ? (
                  <>
                    <Loader2 size={22} className="animate-spin" />
                    SYNCING...
                  </>
                ) : (
                  <>
                    {step === 8 ? 'FINALIZE SYNC' : 'CONTINUE'}
                    <ArrowRight size={22} className="group-hover:translate-x-3 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
const DashDropdown = ({ value, options, onChange }: any) => (
  <div className="relative flex-1 group">
    <select value={value} onChange={(e) => onChange(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white appearance-none focus:outline-none focus:border-primary/50 text-xs font-light hover:bg-white/[0.08] transition-all cursor-pointer shadow-sm">
      {options.map((opt: string) => <option key={opt} value={opt} className="bg-bg-deep text-white">{opt}</option>)}
    </select>
    <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-white/20 group-hover:text-primary transition-colors"><ChevronDown size={12} /></div>
  </div>
);

/* --- Compact Helper Components --- */
const StepLayout = ({ icon, title, subtitle, children }: any) => (
  <div className="animate-in fade-in slide-in-from-right-10 duration-700">
    <div className="flex items-center gap-6 mb-8">
      <div className="w-16 h-16 rounded-[1.5rem] bg-primary/10 flex items-center justify-center text-primary shadow-inner flex-shrink-0">
        {icon}
      </div>
      <div>
        <h2 className="text-4xl font-light text-white tracking-tighter leading-tight">{title}</h2>
        <p className="text-white/30 text-base italic font-light tracking-wide">{subtitle}</p></div>
    </div>
    <div className="w-full">{children}</div>
  </div>
);

const ChoiceCard = ({ icon, title, desc, onClick, active }: any) => (
  <button onClick={onClick} className={`p-8 border rounded-[2.5rem] text-left transition-all group relative overflow-hidden h-full flex flex-col ${active ? 'bg-white/10 border-primary shadow-xl scale-[1.02]' : 'bg-white/5 border-white/5 hover:border-white/20'}`}>
    <div className="mb-6 w-16 h-16 rounded-[1.5rem] bg-white/5 flex items-center justify-center group-hover:bg-primary/10 transition-colors">{icon}</div>
    <h3 className="text-2xl font-bold text-white mb-3 tracking-tight">{title}</h3>
    <p className="text-white/40 text-sm leading-relaxed font-light">{desc}</p>
    {active && <div className="absolute top-6 right-6 text-primary"><CheckCircle size={24} /></div>}
  </button>
);

const DashInput = ({ label, placeholder, value, onChange, textarea, type = "text" }: any) => (
  <div className="space-y-3 w-full text-white">
    <label className="text-[10px] font-bold text-white/20 uppercase tracking-[0.3em] ml-4">{label}</label>
    {textarea ? (
      <textarea className="w-full bg-white/5 border border-white/10 rounded-[2rem] p-6 text-white placeholder-white/5 focus:outline-none focus:border-primary/50 transition-all text-base font-light min-h-[160px] resize-none shadow-sm" placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} />
    ) : (
      <input type={type} className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white placeholder-white/5 focus:outline-none focus:border-primary/50 transition-all text-base font-light shadow-sm" placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} />
    )}
  </div>
);

const DashSelect = ({ label, options, value, onChange }: any) => (
  <div className="space-y-3 w-full text-white">
    <label className="text-[10px] font-bold text-white/20 uppercase tracking-[0.3em] ml-4">{label}</label>
    <div className="relative">
      <select className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white appearance-none focus:outline-none focus:border-primary/50 text-base font-light cursor-pointer shadow-sm" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((opt: string) => <option key={opt} value={opt} className="bg-bg-deep text-white">{opt}</option>)}
      </select>
      <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-white/20"><ChevronDown size={18}/></div>
    </div>
  </div>
);

const SectionHeader = ({ title, icon, onAdd }: any) => (
  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-white/10 pb-6 mb-8 mt-12 gap-4">
    <div className="flex items-center gap-4 text-primary">
      <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">{icon}</div>
      <h4 className="text-sm font-bold uppercase tracking-[0.4em]">{title}</h4>
    </div>
    {onAdd && <button onClick={onAdd} className="flex items-center gap-3 px-6 py-2.5 bg-white/5 hover:bg-white/10 rounded-full text-[9px] font-bold uppercase tracking-widest transition-all border border-white/5"><Plus size={16}/> New Entry</button>}
  </div>
);

const FinalReviewCard = ({ label, value, sub }: any) => (
  <div className="p-6 bg-white/5 border border-white/10 rounded-[2rem] flex items-center justify-between group hover:border-primary/20 transition-all shadow-lg overflow-hidden">
    <div className="max-w-[80%] overflow-hidden">
      <h5 className="text-[9px] font-bold uppercase tracking-[0.3em] text-primary mb-2">{label}</h5>
      <p className="text-lg font-medium text-white tracking-tight leading-tight mb-1 truncate">{value}</p>
      <p className="text-white/30 text-xs italic font-light truncate">{sub}</p>
    </div>
    <div className="text-primary/10 group-hover:text-primary transition-colors flex-shrink-0"><CheckCircle size={24}/></div>
  </div>
);


const ProfessionalMilestoneComponent = ({ label, duration, onDurationChange, location, onLocationChange }: any) => {
  const [startMonth, setStartMonth] = useState('Jan');
  const [startYear, setStartYear] = useState(new Date().getFullYear().toString());
  const [endMonth, setEndMonth] = useState('Jan');
  const [endYear, setEndYear] = useState(new Date().getFullYear().toString());
  const [isPresent, setIsPresent] = useState(false);

  useEffect(() => {
    const startStr = `${startMonth} ${startYear}`;
    const endStr = isPresent ? 'Present' : `${endMonth} ${endYear}`;
    onDurationChange(`${startStr} - ${endStr}`);
  }, [startMonth, startYear, endMonth, endYear, isPresent]);

  return (
    <div className="space-y-3 w-full">
      <label className="text-[10px] font-bold text-white/20 uppercase tracking-[0.3em] ml-4">{label}</label>
      <div className="bg-white/[0.02] p-6 rounded-[2rem] border border-white/5 relative overflow-hidden space-y-6">
        <div className="absolute left-10 top-12 bottom-12 w-[1px] bg-gradient-to-b from-primary/30 to-white/5 z-0" />
        <div className="flex items-center gap-6 relative z-10">
          <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0"><MapPin size={16} className="text-primary" /></div>
          <div className="flex-1"><input type="text" placeholder="Milestone Origin" value={location} onChange={(e) => onLocationChange(e.target.value)} className="w-full bg-transparent border-b border-white/10 text-base font-light py-1 text-white placeholder-white/10 focus:outline-none focus:border-primary/50 transition-all" /></div>
        </div>
        <div className="flex items-center gap-6 relative z-10">
          <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center shrink-0"><div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_rgba(212,212,170,1)]" /></div>
          <div className="flex-1 flex gap-3"><DashDropdown value={startMonth} options={MONTHS} onChange={setStartMonth} /><DashDropdown value={startYear} options={YEARS.map(y => y.toString())} onChange={setStartYear} /></div>
        </div>
        <div className="flex items-center gap-6 relative z-10">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border transition-all duration-700 ${isPresent ? 'bg-primary border-primary' : 'bg-white/5 border-white/10'}`}><div className={`w-2 h-2 rounded-full transition-all duration-700 ${isPresent ? 'bg-bg-deep' : 'bg-white/10'}`} /></div>
          <div className="flex-1 flex flex-col gap-3">
             <div className={`flex gap-3 transition-all duration-500 ${isPresent ? 'opacity-20 grayscale pointer-events-none blur-[1px]' : 'opacity-100'}`}><DashDropdown value={endMonth} options={MONTHS} onChange={setEndMonth} /><DashDropdown value={endYear} options={YEARS.map(y => y.toString())} onChange={setEndYear} /></div>
             <button onClick={() => setIsPresent(!isPresent)} className={`flex items-center gap-2 self-end text-[9px] font-bold uppercase tracking-[0.1em] transition-all px-4 py-2 rounded-full border ${isPresent ? 'bg-primary/20 border-primary text-primary shadow-sm' : 'bg-white/5 border-white/10 text-white/20 hover:text-white/40'}`}>Ongoing Engagement</button>
          </div>
        </div>
      </div>
    </div>
  );
};



export default GetStarted;