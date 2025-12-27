
import React, { useEffect, useState } from 'react';

interface ForgotPasswordProps {
  onBackToLogin: () => void;
}

const ForgotPassword: React.FC<ForgotPasswordProps> = ({ onBackToLogin }) => {
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    // @ts-ignore
    const gsap = window.gsap;
    if (gsap) {
      gsap.from('.fp-animate', {
        y: 60,
        opacity: 0,
        duration: 1.4,
        stagger: 0.15,
        ease: 'expo.out'
      });
      
      gsap.from('.fp-form-reveal', {
        scale: 0.95,
        opacity: 0,
        duration: 1.6,
        delay: 0.4,
        ease: 'power4.out'
      });
    }
  }, []);

  return (
    <div className="relative w-full min-h-screen pt-48 pb-32 px-6 md:px-12 flex flex-col items-center font-inter overflow-hidden">
      <section className="w-full max-w-2xl flex flex-col gap-12 relative z-10">
        <div className="flex flex-col items-center text-center gap-6 fp-animate">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary border border-primary/20">
            <span className="material-symbols-outlined text-[24px]">sync_lock</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-light tracking-tight text-white font-sans">
            Access <span className="text-primary font-serif italic">Recovery</span>
          </h1>
          <p className="text-white/40 text-lg font-light tracking-wide uppercase">Initialize password reset protocol</p>
        </div>

        <div className="w-full fp-form-reveal">
          <div className="relative rounded-[3rem] bg-white/[0.03] backdrop-blur-3xl border border-white/10 p-8 md:p-16 shadow-[0_0_80px_rgba(0,0,0,0.5)]">
            <div className="relative z-10">
              {!submitted ? (
                <>
                  <p className="text-white/50 text-center mb-12 text-lg font-light leading-relaxed">
                    Enter the email associated with your unit. <br/>
                    We will transmit a recovery link to your console.
                  </p>

                  <form className="flex flex-col gap-10" onSubmit={(e) => { e.preventDefault(); setSubmitted(true); }}>
                    <FormInput label="Email Address" placeholder="operative@domain.com" icon="alternate_email" type="email" />

                    <button type="submit" className="w-full h-20 rounded-2xl bg-primary hover:bg-primary-hover text-[#0f231e] font-bold text-lg tracking-wider transition-all flex items-center justify-center gap-4 group shadow-[0_20px_60px_rgba(212,212,170,0.15)] active:scale-[0.98]">
                      TRANSMIT RESET LINK
                      <span className="material-symbols-outlined text-[24px] transition-transform group-hover:translate-x-2">send</span>
                    </button>
                  </form>
                </>
              ) : (
                <div className="text-center py-8">
                  <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/20 text-primary border border-primary/30 mx-auto mb-10">
                    <span className="material-symbols-outlined text-[32px]">mark_email_read</span>
                  </div>
                  <h3 className="text-3xl text-white font-light mb-4 tracking-tight">Transmission Successful</h3>
                  <p className="text-white/40 text-lg font-light leading-relaxed mb-12">
                    Reset protocol has been sent to your terminal. <br/>
                    Check your communication logs.
                  </p>
                  <button onClick={() => setSubmitted(false)} className="text-primary/60 hover:text-primary uppercase tracking-[0.2em] font-bold text-xs transition-colors">
                    Resend transmission?
                  </button>
                </div>
              )}

              <div className="mt-12 pt-8 border-t border-white/5 text-center">
                <button onClick={onBackToLogin} className="flex items-center justify-center gap-3 mx-auto text-white/40 hover:text-primary transition-colors group">
                  <span className="material-symbols-outlined text-[20px] transition-transform group-hover:-translate-x-1">arrow_back</span>
                  <span className="text-xs font-bold uppercase tracking-[0.3em]">Back to Login</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

const FormInput = ({ label, placeholder, icon, type = "text" }: { label: string, placeholder: string, icon: string, type?: string }) => (
  <div className="space-y-3 group/field">
    <label className="text-[10px] font-bold text-white/30 uppercase tracking-[0.4em] ml-1 group-focus-within/field:text-primary transition-colors">
      {label}
    </label>
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none text-white/10 group-focus-within/field:text-primary transition-colors z-10">
        <span className="material-symbols-outlined text-[20px]">{icon}</span>
      </div>
      <input 
        type={type}
        className="relative z-0 w-full bg-white/5 border border-white/5 rounded-2xl pl-14 pr-6 py-5 text-white placeholder-white/5 focus:outline-none focus:border-primary/50 focus:bg-white/[0.08] focus:ring-1 focus:ring-primary/20 transition-all text-base font-light shadow-inner"
        placeholder={placeholder}
        required
      />
    </div>
  </div>
);

export default ForgotPassword;
