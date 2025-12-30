import React, { useState, useEffect, useRef } from 'react';

import { authService, User } from '../services/authService';

import { apiService } from '../services/apiService';
import { resumeService } from '../services/resumeService';
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
  CheckCircle2,
  Upload,
  MapPin,
  X,
  Map as MapIcon,
  Globe,
  ChevronDown,
  FileText,
  AlertCircle
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

const GEOAPIFY_API_KEY = 'cd06752ba8a24ecb9ee1b3282b24c70f';

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
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  
  const [locationQuery, setLocationQuery] = useState('');
  const [locationSuggestions, setLocationSuggestions] = useState<any[]>([]);
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
    resumeFile: null,
    availability: { freeTime: '2-4 hours', studyDays: [] },
    targetRole: 'Software Engineer',
    targetIndustry: '',
    timeline: '6 Months',
    visionStatement: ''
  });

  const steps = ["Account", "Identity", "Source", "Profile", "Geography", "Time", "Goals", "Review"];

  // Skill suggestions
  useEffect(() => {
    if (skillInput.length > 1) {
      setSkillSuggestions(COMMON_SKILLS.filter(s => s.toLowerCase().includes(skillInput.toLowerCase()) && !formData.skills.technical.includes(s)));
    } else {
      setSkillSuggestions([]);
    }
  }, [skillInput, formData.skills.technical]);

  // Geoapify location autocomplete
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (locationQuery.length > 2) {
        setIsSearchingLocation(true);
        try {
          const response = await fetch(
            `https://api.geoapify.com/v1/geocode/autocomplete?text=${encodeURIComponent(locationQuery)}&apiKey=${GEOAPIFY_API_KEY}&limit=5`
          );
          const data = await response.json();
          
          if (data.features) {
            const suggestions = data.features.map((feature: any) => ({
              formatted: feature.properties.formatted,
              city: feature.properties.city,
              country: feature.properties.country,
              state: feature.properties.state
            }));
            setLocationSuggestions(suggestions);
          }
        } catch (error) {
          console.error('Location search failed:', error);
        } finally {
          setIsSearchingLocation(false);
        }
      } else {
        setLocationSuggestions([]);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [locationQuery]);

  const handleNext = () => {
    if (step === 3 && inputMethod === 'manual') { 
      setStep(4); 
      return; 
    }
    if (step === 3 && inputMethod === 'ai' && !uploadedFile) {
      setError('Please upload a resume file to continue');
      return;
    }
    if (step === 4) { setStep(5); return; }
    if (step === 5 && formData.currentStatus !== 'Student') { setStep(7); return; }
    if (step < 8) setStep(step + 1);
    else handleFinalize();
  };

  const handleBack = () => {
    if (step === 7 && formData.currentStatus !== 'Student') { setStep(5); return; }
    if (step > 1) setStep(step - 1);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploadedFile(file);
    setError('');
    
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a PDF, DOCX, or TXT file');
      setUploadedFile(null);
      return;
    }

    setFormData({ ...formData, resumeFile: file });
    await handleAIParse(file);
  };

  const handleAIParse = async (file: File) => {
  setIsParsing(true);
  setError('');

  try {
    console.log('📄 Parsing resume (no auth required)...');
    
    // ✅ USE UNAUTHENTICATED PARSE (no token needed during signup)
    const result = await resumeService.parseResumeUnauthenticated(file);
    
    console.log('✅ Resume parsed:', result.data);

    // Extract data from parsed resume
    const parsed = result.data;

    // Auto-fill form with parsed data
    setFormData(prev => ({
      ...prev,
      fullName: parsed.personal_info.fullName || prev.fullName,
      email: parsed.personal_info.email || prev.email,
      location: parsed.personal_info.location || prev.location,
      
      // Education
      education: parsed.education.length > 0 
        ? parsed.education.map(edu => ({
            institution: edu.institution,
            degree: edu.degree,
            major: edu.degree, // Using degree as major fallback
            location: '',
            duration: edu.year
          }))
        : prev.education,
      
      // Experience
      experience: parsed.experience.length > 0
        ? parsed.experience.map(exp => ({
            role: exp.title,
            company: exp.company,
            location: '',
            duration: exp.duration,
            description: exp.responsibilities.join('. ')
          }))
        : prev.experience,
      
      // Projects
      projects: parsed.projects.length > 0
        ? parsed.projects.map(proj => ({
            title: proj.name,
            description: proj.description,
            techStack: proj.technologies.join(', ')
          }))
        : prev.projects,
      
      // Skills
      skills: {
        technical: parsed.skills.technical.length > 0 ? parsed.skills.technical : prev.skills.technical,
        soft: parsed.skills.non_technical.length > 0 ? parsed.skills.non_technical : prev.skills.soft
      },
      
      // Store resume file reference
      resumeFile: file,
      resumeText: JSON.stringify(parsed) // Store full parsed data
    }));

    // Move to next step
    setStep(4);
    
  } catch (err: any) {
    console.error('❌ Resume parsing failed:', err);
    setError(`Failed to parse resume: ${err.message}. You can still fill in details manually.`);
    // Still move to manual entry on error
    setStep(4);
  } finally {
    setIsParsing(false);
  }
};



  const handleFinalize = async () => {
  setIsRegistering(true);
  setError('');

  try {
    // Transform data to match backend UserRegister schema
    const registrationData = {
      // Required fields
      email: formData.email.trim(),
      username: formData.username.trim(),
      password: formData.password,
      full_name: formData.fullName.trim() || formData.username.trim(),
      
      // Optional fields with defaults
      location: formData.location?.trim() || null,
      preferred_locations: Array.isArray(formData.preferredLocations) ? formData.preferredLocations : [],
      current_status: formData.currentStatus || "Working Professional",
      field_of_interest: formData.fieldOfInterest || "Software Engineering",
      
      // Education: Filter empty + match EducationCreate schema
      education: formData.education
        .filter((e: any) => e.institution && e.institution.trim())
        .map((edu: any) => ({
          institution: edu.institution.trim(),
          degree: edu.degree.trim() || "Bachelor's",
          major: edu.major?.trim() || null,
          location: edu.location?.trim() || null,
          duration: edu.duration?.trim() || "",
          start_date: null,
          end_date: null,
          grade: null
        })),
      
      // Experience: Filter empty + match ExperienceCreate schema
      experience: formData.experience
        .filter((e: any) => e.role && e.role.trim())
        .map((exp: any) => ({
          role: exp.role.trim(),
          company: exp.company.trim() || "",
          location: exp.location?.trim() || null,
          duration: exp.duration?.trim() || "",
          description: exp.description?.trim() || "",
          start_date: null,
          end_date: null
        })),
      
      // Projects: Filter empty + match ProjectCreate schema
      projects: formData.projects
        .filter((p: any) => p.title && p.title.trim())
        .map((proj: any) => ({
          title: proj.title.trim(),
          description: proj.description?.trim() || "",
          tech_stack: proj.techStack?.trim() || "",
          link: null
        })),
      
      // Skills: Must be dict with technical and soft arrays
      skills: {
        technical: Array.isArray(formData.skills?.technical) ? formData.skills.technical : [],
        soft: Array.isArray(formData.skills?.soft) ? formData.skills.soft : []
      },
      
      // Availability: Keep camelCase to match backend schema
      availability: formData.availability?.freeTime ? {
        freeTime: formData.availability.freeTime || "2-4 hours",  // ✅ KEPT CAMELCASE
        studyDays: Array.isArray(formData.availability.studyDays) ? formData.availability.studyDays : []  // ✅ KEPT CAMELCASE
      } : {
        freeTime: "2-4 hours",  // ✅ DEFAULT VALUE
        studyDays: []  // ✅ DEFAULT VALUE
      },
      
      // Career goals
      target_role: formData.targetRole || "Software Engineer",
      timeline: formData.timeline || "6 Months",
      vision_statement: formData.visionStatement?.trim() || ""
    };

    console.log('📤 Sending registration data:', JSON.stringify(registrationData, null, 2));

    const response = await apiService.register(registrationData);
    
    if (response.error) {
      console.error('❌ Registration error:', response.error);
      setError(response.error);
      return;
    }
    
    if (response.data) {
      console.log('✅ Registration successful:', response.data);
      
      // The response has { user, access_token, token_type }
      const user = response.data.user;
      
      onSuccess(user);
    } else {
      setError('Registration failed. Please try again.');
    }
  } catch (err: any) {
    console.error('❌ Registration exception:', err);
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

  const addPreferredLocation = (location: any) => {
    const locationString = location.formatted || location;
    if (formData.preferredLocations.length < 3 && !formData.preferredLocations.includes(locationString)) {
      setFormData({ ...formData, preferredLocations: [...formData.preferredLocations, locationString] });
    }
    setLocationQuery('');
    setLocationSuggestions([]);
  };

  return (
    <div className="relative w-full min-h-screen py-8 px-4 flex flex-col items-center overflow-hidden font-inter text-white">
      <div className="w-full max-w-3xl relative z-10">
        
        {/* Compact Progress Tracker */}
        <div className="flex flex-col gap-3 mb-6">
          <div className="flex justify-between items-center text-[8px] font-bold uppercase tracking-[0.25em] text-white/20">
            <span>Stage {step}/8</span>
            <span className="text-primary">{steps[step-1]}</span>
            <span>{Math.round((step/8)*100)}%</span>
          </div>
          <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden flex">
            {steps.map((_, i) => (
              <div key={i} className={`flex-1 h-full transition-all duration-500 ${i + 1 <= step ? 'bg-primary' : 'bg-transparent'}`} />
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-xs flex items-center gap-2">
            <AlertCircle size={16} />
            <span className="flex-1">{error}</span>
            <button onClick={() => setError('')} className="text-red-400 hover:text-red-300"><X size={14} /></button>
          </div>
        )}

        {/* Main Content Card - OPTIMIZED HEIGHT */}
        <div className="bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-3xl p-6 md:p-8 shadow-2xl">
          <div className="flex flex-col" style={{ minHeight: '400px', maxHeight: '70vh' }}>
            
            {/* STEP 1: ACCOUNT */}
            {step === 1 && (
              <StepLayout title="Account Setup" subtitle="Create your secure access" icon={<Globe size={24} />}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <DashInput label="Email" value={formData.email} onChange={(v: string) => setFormData({...formData, email: v})} placeholder="you@example.com" />
                  <DashInput label="Username" value={formData.username} onChange={(v: string) => setFormData({...formData, username: v})} placeholder="username" />
                  <div className="md:col-span-2">
                    <DashInput label="Password" type="password" value={formData.password} onChange={(v: string) => setFormData({...formData, password: v})} placeholder="••••••••" />
                  </div>
                </div>
              </StepLayout>
            )}

            {/* STEP 2: PROFILE */}
            {step === 2 && (
              <StepLayout title="Basic Info" subtitle="Tell us about yourself" icon={<UserIcon size={24} />}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <DashInput label="Full Name" value={formData.full_name} onChange={(v: string) => setFormData({...formData, full_name: v})} placeholder="John Doe" />
                  <div className="relative">
                    <label className="text-[9px] font-bold text-white/30 uppercase tracking-wider ml-3 block mb-2">Current Location</label>
                    <div className="relative">
                      <input 
                        type="text" 
                        placeholder="City, Country" 
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:border-primary/50 transition-all"
                        value={formData.location}
                        onChange={(e) => {
                          setFormData({...formData, location: e.target.value});
                          setLocationQuery(e.target.value);
                        }}
                      />
                      {isSearchingLocation && <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-primary" />}
                    </div>
                    {locationSuggestions.length > 0 && (
                      <div className="absolute top-full left-0 right-0 mt-1 bg-bg-deep border border-white/20 rounded-xl overflow-hidden z-50 shadow-xl max-h-40 overflow-y-auto">
                        {locationSuggestions.map((loc, idx) => (
                          <button
                            key={idx}
                            onClick={() => {
                              setFormData({...formData, location: loc.formatted});
                              setLocationSuggestions([]);
                              setLocationQuery('');
                            }}
                            className="w-full p-2 hover:bg-white/10 text-left transition-all flex items-center gap-2 text-xs border-b border-white/5 last:border-0"
                          >
                            <MapPin size={12} className="text-primary shrink-0" />
                            <span className="text-white">{loc.formatted}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <DashSelect label="Status" options={['Working Professional', 'Student', 'Career Switcher', 'Exploring']} value={formData.currentStatus} onChange={(v: string) => setFormData({...formData, currentStatus: v})} />
                  <DashSelect label="Field" options={['Software Engineering', 'Data Science', 'Product Management', 'Design', 'Marketing', 'Finance']} value={formData.fieldOfInterest} onChange={(v: string) => setFormData({...formData, fieldOfInterest: v})} />
                </div>
              </StepLayout>
            )}

            {/* STEP 3: INGESTION */}
            {step === 3 && (
              <StepLayout title="Data Source" subtitle="How would you like to proceed?" icon={<Layers size={24} />}>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <ChoiceCard 
                      active={inputMethod === 'ai'} 
                      icon={<Upload size={20} className="text-primary" />} 
                      title="Upload Resume" 
                      desc="AI will extract your details" 
                      onClick={() => setInputMethod('ai')} 
                    />
                    <ChoiceCard 
                      active={inputMethod === 'manual'} 
                      icon={<Keyboard size={20} className="text-white/40" />} 
                      title="Manual Entry" 
                      desc="Fill in details yourself" 
                      onClick={() => setInputMethod('manual')} 
                    />
                  </div>

                  {inputMethod === 'ai' && (
                    <div className="space-y-3 animate-in fade-in">
                      <div 
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full h-40 border-2 border-dashed border-white/10 rounded-2xl bg-white/[0.01] flex flex-col items-center justify-center cursor-pointer hover:border-primary/40 hover:bg-white/[0.03] transition-all group"
                      >
                        <input 
                          type="file" 
                          ref={fileInputRef} 
                          className="hidden" 
                          onChange={handleFileUpload} 
                          accept=".pdf,.txt,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain" 
                        />
                        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform mb-2">
                          {isParsing ? <Loader2 size={20} className="animate-spin" /> : <Upload size={20} />}
                        </div>
                        <p className="text-sm font-light text-white mb-1">
                          {isParsing ? 'Parsing resume...' : uploadedFile ? uploadedFile.name : 'Click to upload'}
                        </p>
                        <p className="text-white/30 text-[8px] font-bold uppercase tracking-wider">PDF, DOCX, TXT</p>
                      </div>
                      
                      {uploadedFile && !isParsing && (
                        <div className="p-3 bg-primary/5 border border-primary/20 rounded-xl flex items-center gap-3">
                          <FileText className="text-primary" size={18} />
                          <div className="flex-1 min-w-0">
                            <p className="text-white font-medium text-sm truncate">{uploadedFile.name}</p>
                            <p className="text-white/40 text-xs">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
                          </div>
                          <CheckCircle className="text-primary shrink-0" size={18} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </StepLayout>
            )}

            {/* STEP 4: PROFILE DETAILS - SCROLLABLE */}
            {step === 4 && (
              <StepLayout title="Your Profile" subtitle="Review and edit details" icon={<Cpu size={24} />}>
                <div className="space-y-6 overflow-y-auto pr-2 custom-scroll" style={{ maxHeight: 'calc(70vh - 200px)' }}>
                  
                  {/* Skills */}
                  <div>
                    <SectionHeader title="Skills" icon={<Code2 size={16}/>} />
                    <div className="space-y-3">
                      <div className="relative">
                        <input
                          type="text"
                          placeholder="Add skills..."
                          value={skillInput}
                          onChange={(e) => setSkillInput(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && skillInput.trim()) {
                              addSkill(skillInput.trim());
                            }
                          }}
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-primary/50 transition-all"
                        />
                        {skillSuggestions.length > 0 && (
                          <div className="absolute top-full left-0 right-0 mt-1 bg-bg-deep border border-white/20 rounded-xl overflow-hidden z-50 shadow-xl max-h-32 overflow-y-auto">
                            {skillSuggestions.map((skill, idx) => (
                              <button
                                key={idx}
                                onClick={() => addSkill(skill)}
                                className="w-full p-2 hover:bg-white/10 text-left transition-all text-white text-xs border-b border-white/5 last:border-0"
                              >
                                {skill}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      
                      <div className="flex flex-wrap gap-2">
                        {formData.skills.technical.map((skill: string, idx: number) => (
                          <div key={idx} className="px-3 py-1 bg-primary/10 border border-primary/20 rounded-full flex items-center gap-2 text-xs">
                            <span className="text-white">{skill}</span>
                            <button
                              onClick={() => {
                                setFormData({
                                  ...formData,
                                  skills: {
                                    ...formData.skills,
                                    technical: formData.skills.technical.filter((_: any, i: number) => i !== idx)
                                  }
                                });
                              }}
                              className="text-white/40 hover:text-red-400"
                            >
                              <X size={12} />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Education */}
                  <div>
                    <SectionHeader title="Education" icon={<GraduationCap size={16}/>} onAdd={() => addItem('education', { institution: '', degree: '', major: '', location: '', duration: '' })} />
                    <div className="space-y-3">
                      {formData.education.map((edu: any, i: number) => (
                        <div key={i} className="relative p-4 bg-white/5 border border-white/10 rounded-xl group hover:border-primary/20 transition-all">
                          {formData.education.length > 1 && (
                            <button onClick={() => removeItem('education', i)} className="absolute top-3 right-3 text-white/20 hover:text-red-400">
                              <Trash2 size={14}/>
                            </button>
                          )}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <DashInput label="Institution" value={edu.institution} onChange={(v: string) => updateItem('education', i, 'institution', v)} placeholder="University name" />
                            <DashInput label="Degree" value={edu.degree} onChange={(v: string) => updateItem('education', i, 'degree', v)} placeholder="B.Tech, M.Sc" />
                            <DashInput label="Major" value={edu.major} onChange={(v: string) => updateItem('education', i, 'major', v)} placeholder="Computer Science" />
                            <DashInput label="Duration" value={edu.duration} onChange={(v: string) => updateItem('education', i, 'duration', v)} placeholder="2020-2024" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Experience */}
                  <div>
                    <SectionHeader title="Experience" icon={<Briefcase size={16}/>} onAdd={() => addItem('experience', { role: '', company: '', location: '', duration: '', description: '' })} />
                    <div className="space-y-3">
                      {formData.experience.map((exp: any, i: number) => (
                        <div key={i} className="relative p-4 bg-white/5 border border-white/10 rounded-xl group hover:border-primary/20 transition-all">
                          {formData.experience.length > 1 && (
                            <button onClick={() => removeItem('experience', i)} className="absolute top-3 right-3 text-white/20 hover:text-red-400">
                              <Trash2 size={14}/>
                            </button>
                          )}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <DashInput label="Role" value={exp.role} onChange={(v: string) => updateItem('experience', i, 'role', v)} placeholder="Software Engineer" />
                            <DashInput label="Company" value={exp.company} onChange={(v: string) => updateItem('experience', i, 'company', v)} placeholder="Company name" />
                            <DashInput label="Duration" value={exp.duration} onChange={(v: string) => updateItem('experience', i, 'duration', v)} placeholder="Jan 2023 - Present" />
                            <DashInput label="Location" value={exp.location} onChange={(v: string) => updateItem('experience', i, 'location', v)} placeholder="City, Country" />
                            <div className="md:col-span-2">
                              <DashInput textarea label="Description" value={exp.description} onChange={(v: string) => updateItem('experience', i, 'description', v)} placeholder="Key achievements..." />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Projects */}
                  <div>
                    <SectionHeader title="Projects" icon={<Layers size={16}/>} onAdd={() => addItem('projects', { title: '', description: '', techStack: '' })} />
                    <div className="space-y-3">
                      {formData.projects.map((proj: any, i: number) => (
                        <div key={i} className="relative p-4 bg-white/5 border border-white/10 rounded-xl group hover:border-primary/20 transition-all">
                          {formData.projects.length > 1 && (
                            <button onClick={() => removeItem('projects', i)} className="absolute top-3 right-3 text-white/20 hover:text-red-400">
                              <Trash2 size={14}/>
                            </button>
                          )}
                          <div className="space-y-3">
                            <DashInput label="Project Title" value={proj.title} onChange={(v: string) => updateItem('projects', i, 'title', v)} placeholder="Project name" />
                            <DashInput textarea label="Description" value={proj.description} onChange={(v: string) => updateItem('projects', i, 'description', v)} placeholder="What did you build?" />
                            <DashInput label="Tech Stack" value={proj.techStack} onChange={(v: string) => updateItem('projects', i, 'techStack', v)} placeholder="React, Node.js, MongoDB" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </StepLayout>
            )}

            {/* STEP 5: PREFERRED LOCATIONS */}
            {step === 5 && (
              <StepLayout title="Preferred Locations" subtitle="Where do you want to work?" icon={<MapIcon size={24} />}>
                <div className="space-y-4">
                  <div className="relative">
                    <input 
                      type="text" 
                      placeholder="Search cities..." 
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-10 py-3 text-sm text-white focus:outline-none focus:border-primary/50 transition-all placeholder-white/20"
                      value={locationQuery}
                      onChange={(e) => setLocationQuery(e.target.value)}
                    />
                    <MapPin size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
                    {isSearchingLocation && <Loader2 size={16} className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-primary"/>}
                  </div>

                  {locationSuggestions.length > 0 && (
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {locationSuggestions.map((loc, idx) => (
                        <button
                          key={idx}
                          onClick={() => addPreferredLocation(loc)}
                          disabled={formData.preferredLocations.length >= 3}
                          className="w-full p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-left transition-all disabled:opacity-30 text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <MapPin size={14} className="text-primary shrink-0" />
                            <span className="text-white truncate">{loc.formatted}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  <p className="text-white/40 text-xs text-center">Select up to 3 locations ({formData.preferredLocations.length}/3)</p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {formData.preferredLocations.map((loc: string, i: number) => (
                      <div key={i} className="p-4 bg-primary/5 border border-primary/20 rounded-xl flex flex-col gap-2">
                        <MapPin size={20} className="text-primary" />
                        <div className="flex justify-between items-end gap-2">
                          <p className="text-sm font-medium text-white leading-tight flex-1 break-words">{loc}</p>
                          <button 
                            onClick={() => setFormData({...formData, preferredLocations: formData.preferredLocations.filter((l:any)=>l!==loc)})} 
                            className="text-white/20 hover:text-red-400 shrink-0"
                          >
                            <Trash2 size={14}/>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </StepLayout>
            )}

            {/* STEP 6: TIME AVAILABILITY */}
            {step === 6 && (
              <StepLayout title="Availability" subtitle="Your learning schedule" icon={<Clock size={24} />}>
                <div className="space-y-6">
                  <DashSelect label="Daily Study Time" options={['1-2 hours', '2-4 hours', '4-6 hours', '6+ hours']} value={formData.availability.freeTime} onChange={(v: string) => setFormData({...formData, availability: {...formData.availability, freeTime: v}})} />
                  
                  <div className="space-y-3">
                    <label className="text-[9px] font-bold text-white/30 uppercase tracking-wider ml-3">Study Days</label>
                    <div className="flex flex-wrap gap-2">
                      {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
                        <button 
                          key={day} 
                          onClick={() => {
                            const days = formData.availability.studyDays;
                            const next = days.includes(day) ? days.filter((d:any)=>d!==day) : [...days, day];
                            setFormData({...formData, availability: {...formData.availability, studyDays: next}});
                          }} 
                          className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                            formData.availability.studyDays.includes(day) 
                              ? 'bg-primary border-primary text-bg-deep' 
                              : 'bg-white/5 border-white/10 text-white/40 hover:border-white/20'
                          }`}
                        >
                          {day}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </StepLayout>
            )}

            {/* STEP 7: GOALS */}
            {step === 7 && (
              <StepLayout title="Career Goals" subtitle="What are you aiming for?" icon={<Target size={24} />}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <DashSelect label="Target Role" options={ROLES} value={formData.targetRole} onChange={(v: string) => setFormData({...formData, targetRole: v})} />
                  <DashSelect label="Timeline" options={['3 Months', '6 Months', '12 Months', 'Flexible']} value={formData.timeline} onChange={(v: string) => setFormData({...formData, timeline: v})} />
                  <div className="md:col-span-2">
                    <DashInput textarea label="Vision Statement" value={formData.visionStatement} onChange={(v: string) => setFormData({...formData, visionStatement: v})} placeholder="Describe your career aspirations..." />
                  </div>
                </div>
              </StepLayout>
            )}

            {/* STEP 8: FINAL REVIEW */}
            {step === 8 && (
              <StepLayout title="Review" subtitle="Confirm your details" icon={<CheckCircle size={24} />}>
                <div className="space-y-4 overflow-y-auto pr-2" style={{ maxHeight: 'calc(70vh - 200px)' }}>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <ReviewCard label="Name" value={formData.fullName} />
                    <ReviewCard label="Email" value={formData.email} />
                    <ReviewCard label="Location" value={formData.location} />
                    <ReviewCard label="Status" value={formData.currentStatus} />
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <ReviewCard label="Education" value={`${formData.education.filter((e:any)=>e.institution).length} entries`} />
                    <ReviewCard label="Experience" value={`${formData.experience.filter((e:any)=>e.role).length} roles`} />
                    <ReviewCard label="Skills" value={`${formData.skills.technical.length} skills`} />
                  </div>

                  <div className="p-6 bg-primary/10 border border-primary/20 rounded-2xl text-center">
                    <CheckCircle2 size={40} className="text-primary mx-auto mb-3" />
                    <h4 className="text-xl text-primary font-medium mb-2">Ready to Start</h4>
                    <p className="text-white/50 text-sm">Your AI career assistant is waiting</p>
                  </div>
                </div>
              </StepLayout>
            )}

            {/* Navigation */}
            <div className="mt-auto pt-6 flex items-center justify-between border-t border-white/10">
              <button 
                onClick={handleBack} 
                className={`flex items-center gap-2 text-white/40 hover:text-white transition-colors text-xs font-medium ${step === 1 ? 'invisible' : ''}`}
              >
                <ChevronLeft size={16}/> Back
              </button>
              <button 
                onClick={handleNext} 
                disabled={(step === 1 && (!formData.email || !formData.password || !formData.username)) || (step === 3 && inputMethod === 'ai' && !uploadedFile) || isRegistering || isParsing} 
                className="px-8 py-3 bg-primary text-bg-deep rounded-xl font-bold text-sm flex items-center gap-3 hover:shadow-lg disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                {isRegistering ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Creating...
                  </>
                ) : isParsing ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Parsing...
                  </>
                ) : (
                  <>
                    {step === 8 ? 'Complete' : 'Continue'}
                    <ArrowRight size={18} />
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

/* --- COMPACT COMPONENTS --- */

const StepLayout = ({ icon, title, subtitle, children }: any) => (
  <div className="animate-in fade-in slide-in-from-right duration-500">
    <div className="flex items-center gap-4 mb-6">
      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
        {icon}
      </div>
      <div>
        <h2 className="text-2xl font-light text-white">{title}</h2>
        <p className="text-white/40 text-xs">{subtitle}</p>
      </div>
    </div>
    {children}
  </div>
);

const ChoiceCard = ({ icon, title, desc, onClick, active }: any) => (
  <button 
    onClick={onClick} 
    className={`p-4 border rounded-xl text-left transition-all relative ${
      active ? 'bg-white/10 border-primary' : 'bg-white/5 border-white/10 hover:border-white/20'
    }`}
  >
    <div className="mb-3 w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center">{icon}</div>
    <h3 className="text-base font-semibold text-white mb-1">{title}</h3>
    <p className="text-white/50 text-xs">{desc}</p>
    {active && <CheckCircle size={18} className="absolute top-3 right-3 text-primary" />}
  </button>
);

const DashInput = ({ label, placeholder, value, onChange, textarea, type = "text" }: any) => (
  <div className="space-y-2">
    <label className="text-[9px] font-bold text-white/30 uppercase tracking-wider ml-3">{label}</label>
    {textarea ? (
      <textarea 
        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white placeholder-white/20 focus:outline-none focus:border-primary/50 transition-all resize-none" 
        placeholder={placeholder} 
        value={value} 
        onChange={(e) => onChange(e.target.value)}
        rows={3}
      />
    ) : (
      <input 
        type={type} 
        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:border-primary/50 transition-all" 
        placeholder={placeholder} 
        value={value} 
        onChange={(e) => onChange(e.target.value)} 
      />
    )}
  </div>
);

const DashSelect = ({ label, options, value, onChange }: any) => (
  <div className="space-y-2">
    <label className="text-[9px] font-bold text-white/30 uppercase tracking-wider ml-3">{label}</label>
    <div className="relative">
      <select 
        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white appearance-none focus:outline-none focus:border-primary/50 cursor-pointer" 
        value={value} 
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt: string) => <option key={opt} value={opt} className="bg-bg-deep">{opt}</option>)}
      </select>
      <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/30" />
    </div>
  </div>
);

const SectionHeader = ({ title, icon, onAdd }: any) => (
  <div className="flex items-center justify-between mb-3">
    <div className="flex items-center gap-2 text-primary">
      <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center">{icon}</div>
      <h4 className="text-xs font-bold uppercase tracking-wider">{title}</h4>
    </div>
    {onAdd && (
      <button 
        onClick={onAdd} 
        className="flex items-center gap-2 px-3 py-1 bg-white/5 hover:bg-white/10 rounded-lg text-[9px] font-bold uppercase tracking-wider transition-all border border-white/10"
      >
        <Plus size={12}/> Add
      </button>
    )}
  </div>
);

const ReviewCard = ({ label, value }: any) => (
  <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
    <h5 className="text-[8px] font-bold uppercase tracking-wider text-primary mb-1">{label}</h5>
    <p className="text-sm font-medium text-white truncate">{value}</p>
  </div>
);

export default GetStarted;
