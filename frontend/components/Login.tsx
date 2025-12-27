import React, { useEffect, useState } from 'react';
import { authService, User } from '../services/authService';
import { Sparkles, ShieldCheck, ArrowRight, UserCheck, Loader2 } from 'lucide-react';

interface LoginProps {
  onForgotPassword: () => void;
  onSignUp: () => void;
  onDashboard: (user: User) => void;
}

const Login: React.FC<LoginProps> = ({ onForgotPassword, onSignUp, onDashboard }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isDemoLogin, setIsDemoLogin] = useState(false);

  useEffect(() => {
    // @ts-ignore
    const gsap = window.gsap;
    if (gsap) {
      gsap.from('.l-animate', { 
        y: 60, 
        opacity: 0, 
        duration: 1.4, 
        stagger: 0.15, 
        ease: 'expo.out',
        clearProps: 'opacity',
       
      });
      gsap.from('.l-form-reveal', { 
        scale: 0.95, 
        opacity: 0, 
        duration: 1.6, 
        delay: 0.4, 
        ease: 'power4.out',
        clearProps: 'opacity',
        
      });
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoggingIn(true);
    setError('');

    try {
      const user = await authService.login(email, password);
      if (user) {
        onDashboard(user);
      } else {
        setError('Invalid access credentials provided.');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleDemoAccess = async () => {
    setIsDemoLogin(true);
    setError('');

    try {
      const user = await authService.login('demo@adviceguide.ai', 'demo');
      if (user) {
        onDashboard(user);
      } else {
        setError('Demo user not available. Please check backend.');
      }
    } catch (err: any) {
      setError(err.message || 'Demo login failed.');
    } finally {
      setIsDemoLogin(false);
    }
  };

  return (
    <div className="relative w-full min-h-screen pt-48 pb-32 px-6 md:px-12 flex flex-col items-center font-inter overflow-hidden">
      <section className="w-full max-w-3xl flex flex-col gap-12 relative z-10">
        
        <div className="flex flex-col items-center text-center gap-6 l-animate opacity-100">
          <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-primary/15 text-primary border border-primary/30 shadow-xl">
            <ShieldCheck size={32} />
          </div>
          <h1 className="text-6xl md:text-8xl font-light tracking-tight text-white font-sans">
            Secure <span className="text-primary font-serif italic">Login</span>
          </h1>
          {error && (
            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400 text-sm max-w-md">
              {error}
            </div>
          )}
        </div>

        <div className="w-full l-form-reveal space-y-8 opacity-100">
          {/* Demo Option - Most prominent for first look */}
          <button 
            onClick={handleDemoAccess}
            disabled={isDemoLogin}
            className="w-full p-8 bg-white/[0.12] border border-primary/40 rounded-[3rem] group hover:bg-white/[0.18] hover:border-primary transition-all flex items-center justify-between shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex items-center gap-6">
              <div className="w-14 h-14 rounded-2xl bg-primary/25 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                {isDemoLogin ? <Loader2 size={28} className="animate-spin" /> : <UserCheck size={28}/>}
              </div>
              <div className="text-left">
                <h3 className="text-xl font-bold text-white">
                  {isDemoLogin ? 'Initializing Demo...' : 'Continue with Demo Profile'}
                </h3>
                <p className="text-white/75 text-xs italic uppercase tracking-widest mt-1">Exploration mode only</p>
              </div>
            </div>
            {!isDemoLogin && <ArrowRight size={24} className="text-primary group-hover:translate-x-3 transition-transform" />}
          </button>

          <div className="relative flex items-center gap-4 py-4">
            <div className="h-[1px] flex-1 bg-white/15"></div>
            <span className="text-[10px] font-bold text-white/40 uppercase tracking-[0.5em]">OR INITIALIZE MY OWN</span>
            <div className="h-[1px] flex-1 bg-white/15"></div>
          </div>

          <div className="relative rounded-[4rem] bg-white/[0.08] backdrop-blur-xl border border-white/20 p-10 md:p-20 shadow-2xl">
            <form onSubmit={handleLogin} className="relative z-10">
              <div className="flex flex-col gap-10">
                <FormInput 
                  label="Email Terminal" 
                  placeholder="operative@domain.com" 
                  icon="alternate_email" 
                  type="email" 
                  value={email}
                  onChange={setEmail}
                />
                <FormInput 
                  label="Secret Key" 
                  placeholder="••••••••••••" 
                  icon="lock" 
                  type="password" 
                  value={password}
                  onChange={setPassword}
                />
                
                <div className="flex justify-between items-center px-2">
                   <button type="button" onClick={onForgotPassword} className="text-[10px] font-bold text-white/75 hover:text-white uppercase tracking-[0.2em] transition-all">Recover Protocol?</button>
                   <button type="button" onClick={onSignUp} className="text-[10px] font-bold text-primary hover:text-white uppercase tracking-[0.2em] transition-all">New Identity</button>
                </div>

                <button 
                  type="submit"
                  disabled={isLoggingIn || !email || !password}
                  className="w-full h-24 rounded-[2rem] bg-primary text-[#0f231e] font-bold text-xl tracking-[0.2em] transition-all flex items-center justify-center gap-6 group active:scale-[0.98] hover:shadow-[0_0_60px_rgba(212,212,170,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoggingIn ? (
                    <>
                      <Loader2 size={28} className="animate-spin" />
                      AUTHENTICATING...
                    </>
                  ) : (
                    <>
                      AUTHENTICATE
                      <ArrowRight size={28} className="transition-transform group-hover:translate-x-3" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>
    </div>
  );
};

const FormInput = ({ label, placeholder, icon, type = "text", value, onChange }: any) => (
  <div className="space-y-4 group/field">
    <label className="text-[10px] font-bold text-white/75 uppercase tracking-[0.4em] ml-2 group-focus-within/field:text-primary transition-colors">{label}</label>
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-8 flex items-center pointer-events-none text-white/40 group-focus-within/field:text-primary z-10 transition-colors">
        <span className="material-symbols-outlined text-[24px]">{icon}</span>
      </div>
      <input 
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-white/[0.08] border border-white/20 rounded-3xl pl-20 pr-8 py-6 text-white placeholder-white/40 focus:outline-none focus:border-primary/50 focus:bg-white/[0.12] transition-all text-lg font-light shadow-inner"
        placeholder={placeholder}
        required
      />
    </div>
  </div>
);

export default Login;