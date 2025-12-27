import React, { useEffect, useRef } from 'react';
import { ArrowDown, ArrowRight, Layout, Sparkles, Target, Zap, BrainCircuit, History, ShieldCheck } from 'lucide-react';

interface LandingPageProps {
  onGetStarted: () => void;
  onLogin: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted, onLogin }) => {
  const marqueeRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<any>(null);

  useEffect(() => {
    // @ts-ignore
    const gsap = window.gsap;
    // @ts-ignore
    const ScrollTrigger = window.ScrollTrigger;
    
    if (gsap && ScrollTrigger) {
      // Hero animations - ensure elements start visible then animate
      gsap.from('.hero-content > *', {
        y: 40,
        opacity: 0,
        duration: 1.5,
        stagger: 0.15,
        ease: 'expo.out',
        clearProps: 'opacity'// Clear opacity after animation completes
      });

      // Reveal animations for sections
      gsap.utils.toArray('.reveal-section').forEach((section: any) => {
        gsap.from(section, {
          scrollTrigger: {
            trigger: section,
            start: 'top 85%',
            toggleActions: 'play none none none',
            
          },
          y: 60,
          opacity: 0,
          duration: 1.5,
          ease: 'power3.out',
          clearProps: 'opacity' // Clear opacity after animation completes
        });
      });

      // Infinite Marquee Animation
      if (marqueeRef.current) {
        const marqueeContent = marqueeRef.current.firstElementChild;
        if (marqueeContent) {
          const width = marqueeContent.scrollWidth;
          animationRef.current = gsap.to(marqueeRef.current, {
            x: `-${width / 2}px`,
            duration: 25,
            ease: 'none',
            repeat: -1,
          });
        }
      }

      return () => {
        ScrollTrigger.getAll().forEach((t: any) => t.kill());
        if (animationRef.current) animationRef.current.kill();
      };
    }
  }, []);

  const features = [
    { icon: <History className="w-8 h-8" />, title: "Career Memory", description: "Long-term tracking of your trajectory, evolution, and milestones." },
    { icon: <BrainCircuit className="w-8 h-8" />, title: "Agentic Reasoning", description: "AI that proactively identifies skill gaps and strategic pivots." },
    { icon: <Target className="w-8 h-8" />, title: "Dynamic Roadmaps", description: "Evolving learning paths that adjust to real-time market shifts." },
    { icon: <ShieldCheck className="w-8 h-8" />, title: "Continuous Growth", description: "Not just a chat, but a partner that evolves alongside your success." }
  ];

  const marqueeItems = [...features, ...features];

  return (
    <div className="w-full">
      {/* Hero Section */}
      <section className="min-h-screen flex flex-col justify-center px-8 md:px-24 pt-32 hero-content">
        <div className="max-w-[1400px]">
          <h1 className="text-6xl md:text-[8.5rem] font-light leading-[0.9] tracking-tight text-white mb-16 opacity-100">
            Find clarity in your <br/>
            <span className="font-serif italic text-primary">professional</span> evolution.
          </h1>

          <div className="flex gap-12 mb-24 opacity-100">
            <button className="relative pb-2 text-white font-light hover:text-white transition-colors group">
              Explore the Methodology
              <div className="absolute bottom-0 left-0 w-full h-[1px] bg-white/75 group-hover:bg-white transition-colors"></div>
            </button>
            <button 
              onClick={onGetStarted}
              className="relative pb-2 text-white font-light hover:text-white transition-colors group"
            >
              Initialize Mentor
              <div className="absolute bottom-0 left-0 w-full h-[1px] bg-white/75 group-hover:bg-white transition-colors"></div>
            </button>
          </div>

          <div className="max-w-2xl mt-12 opacity-100">
            <span className="block text-primary font-medium tracking-wide text-lg mb-8 uppercase text-xs">
              Agentic Career Mentorship
            </span>
            <p className="text-white/90 text-2xl font-light leading-relaxed max-w-2xl">
              Meet the AI companion designed to navigate your career journey. It doesn't just answer questions—it thinks, plans, and learns alongside you to turn aspirations into legacies.
            </p>
          </div>

          <div className="mt-20 opacity-100">
            <ArrowDown className="w-8 h-8 text-white/75 animate-bounce" />
          </div>
        </div>
      </section>

      {/* Think Plan Act Flow Section */}
      <section className="py-48 reveal-section bg-white/[0.06] opacity-100">
        <div className="px-8 md:px-24 max-w-[1400px] mx-auto text-center space-y-24">
          <h2 className="text-5xl font-serif italic text-primary">Think. Plan. Act. Improve.</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
            <FlowStep num="01" title="THINK" desc="AI Mentor analyzes your memory and reasons about the landscape." />
            <FlowStep num="02" title="PLAN" desc="A dynamic roadmap is generated with precise learning milestones." />
            <FlowStep num="03" title="ACT" desc="Apply with confidence using AI-optimized resumes and mock practice." />
            <FlowStep num="04" title="IMPROVE" desc="Strategy adapts weekly based on application outcomes and progress." />
          </div>
        </div>
      </section>

      {/* Infinite Horizontal Marquee Section */}
      <section className="py-48 overflow-hidden reveal-section relative opacity-100">
        <div className="px-8 md:px-24 mb-16 max-w-[1400px] mx-auto flex flex-col md:flex-row justify-between items-start md:items-end gap-8">
          <div>
            <h2 className="text-4xl md:text-6xl font-medium tracking-tight text-white">
              Intelligent <span className="font-serif italic text-primary">Capabilities</span>.
            </h2>
            <p className="text-white/80 mt-4 max-w-md font-light">Every module is adaptive, ensuring your mentor stays at the bleeding edge of career intelligence.</p>
          </div>
        </div>
        
        <div className="relative group/marquee">
          <div 
            ref={marqueeRef}
            className="flex gap-12 whitespace-nowrap"
            style={{ width: 'max-content' }}
            onMouseEnter={() => animationRef.current?.pause()}
            onMouseLeave={() => animationRef.current?.resume()}
          >
            <div className="flex gap-12 px-8">
              {marqueeItems.map((feature, index) => (
                <div 
                  key={index} 
                  className="w-[85vw] md:w-[42vw] lg:w-[32vw] flex-shrink-0"
                >
                  <FeatureCard 
                    icon={feature.icon}
                    title={feature.title}
                    description={feature.description}
                    onClick={onLogin}
                  />
                </div>
              ))}
            </div>
          </div>
          
          <div className="absolute inset-y-0 left-0 w-48 bg-gradient-to-r from-[#1a3a35]/90 to-transparent z-10 pointer-events-none"></div>
          <div className="absolute inset-y-0 right-0 w-48 bg-gradient-to-l from-[#1a3a35]/90 to-transparent z-10 pointer-events-none"></div>
        </div>
      </section>

      <footer className="max-w-[1400px] mx-auto px-8 md:px-24 py-24 border-t border-white/10 flex flex-col md:flex-row justify-between items-end gap-12 reveal-section opacity-100">
        <div>
          <h2 className="text-6xl font-medium tracking-tighter mb-8 text-white">adviceguide</h2>
          <p className="text-white/75 max-w-xs font-light text-sm">Empowering professionals through adaptive, agentic career intelligence.</p>
        </div>
        
        <div className="flex flex-col items-end gap-12">
          <div className="flex gap-16 text-xs font-medium tracking-widest uppercase opacity-75 text-white">
            <a href="#" className="hover:opacity-100 transition-opacity">Twitter</a>
            <a href="#" className="hover:opacity-100 transition-opacity">LinkedIn</a>
          </div>
          <p className="text-[10px] text-white/40 tracking-[0.3em]">© 2024 ADVICEGUIDE INC.</p>
        </div>
      </footer>
    </div>
  );
};

const FlowStep = ({ num, title, desc }: any) => (
  <div className="space-y-6">
    <div className="text-5xl font-serif text-primary/50">{num}</div>
    <h3 className="text-xl font-bold tracking-widest text-white">{title}</h3>
    <p className="text-white/80 font-light leading-relaxed text-sm">{desc}</p>
  </div>
);

const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick: () => void;
}> = ({ icon, title, description, onClick }) => {
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = (y - centerY) / 25;
    const rotateY = (centerX - x) / 25;

    // @ts-ignore
    if (window.gsap) {
      // @ts-ignore
      window.gsap.to(cardRef.current, {
        rotateX: rotateX,
        rotateY: rotateY,
        scale: 1.01,
        duration: 0.4,
        ease: 'power2.out'
      });
    }
  };

  const handleMouseLeave = () => {
    if (!cardRef.current) return;
    // @ts-ignore
    if (window.gsap) {
      // @ts-ignore
      window.gsap.to(cardRef.current, { 
        rotateX: 0, 
        rotateY: 0, 
        scale: 1, 
        duration: 0.8, 
        ease: 'elastic.out(1, 0.5)' 
      });
    }
  };

  return (
    <div 
      ref={cardRef}
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative p-12 md:p-16 rounded-[3.5rem] bg-white/[0.09] border border-white/20 hover:border-primary/50 transition-colors duration-500 group backdrop-blur-sm h-full flex flex-col justify-between whitespace-normal cursor-pointer overflow-hidden shadow-2xl shadow-black/30 perspective-1000"
      style={{ transformStyle: 'preserve-3d' }}
    >
      <div className="relative z-10" style={{ transform: 'translateZ(40px)' }}>
        <div className="w-20 h-20 rounded-3xl bg-primary/15 flex items-center justify-center text-primary mb-12 group-hover:bg-primary group-hover:text-white transition-all duration-500">
          {icon}
        </div>
        <h3 className="text-4xl font-medium mb-8 text-white group-hover:text-primary transition-colors duration-500 tracking-tight">{title}</h3>
        <p className="text-white/85 leading-relaxed font-light text-xl group-hover:text-white/95 transition-colors duration-500">{description}</p>
      </div>
      <div className="mt-16 flex items-center gap-6 text-primary group-hover:translate-x-3 transition-transform duration-500 relative z-10" style={{ transform: 'translateZ(20px)' }}>
        <span className="text-xs font-bold tracking-[0.3em] uppercase opacity-75 group-hover:opacity-100">Initialize</span>
        <div className="w-12 h-[1px] bg-primary/75 group-hover:w-20 group-hover:bg-primary transition-all duration-500"></div>
        <ArrowRight className="w-5 h-5" />
      </div>
    </div>
  );
};

export default LandingPage;