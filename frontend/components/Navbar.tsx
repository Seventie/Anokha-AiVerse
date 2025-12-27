
import React, { useEffect, useRef, useState } from 'react';

interface NavbarProps {
  onGetStarted: () => void;
  onLogin: () => void;
  onHome: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onGetStarted, onLogin, onHome }) => {
  const navRef = useRef<HTMLElement>(null);
  const btnsRef = useRef<HTMLDivElement>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    
    // @ts-ignore
    const gsap = window.gsap;
    if (gsap) {
      if (navRef.current) {
        gsap.fromTo(navRef.current, 
          { y: -80, opacity: 0 }, 
          { y: 0, opacity: 1, duration: 1.5, ease: 'expo.out' }
        );
      }
      
      if (btnsRef.current) {
        gsap.fromTo(btnsRef.current.children,
          { y: 20, opacity: 0 },
          { 
            y: 0,
            opacity: 1, 
            duration: 1.2, 
            stagger: 0.15,
            delay: 0.6, 
            ease: 'expo.out' 
          }
        );
      }
    }

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav 
      ref={navRef}
      className={`fixed top-0 left-0 w-full z-[100] h-32 flex items-center justify-between px-8 md:px-24 transition-all duration-500 ${
        isScrolled 
          ? 'backdrop-blur-nav bg-bg-deep/60 border-b border-white/5' 
          : 'bg-transparent border-transparent'
      }`}
    >
      <div 
        onClick={onHome}
        className="flex items-center cursor-pointer group"
      >
        <span className="text-4xl font-medium tracking-tight text-white group-hover:opacity-70 transition-opacity">
          adviceguide
        </span>
      </div>

      <div ref={btnsRef} className="flex items-center gap-6 md:gap-10">
        <button 
          onClick={onLogin}
          className="px-8 py-4 rounded-full text-white/90 text-lg font-medium hover:text-white hover:bg-white/10 transition-all"
        >
          Login
        </button>
        <button 
          onClick={onGetStarted}
          className="px-12 py-4 rounded-full bg-white text-bg-deep text-lg font-bold hover:bg-primary transition-all shadow-[0_10px_30px_rgba(0,0,0,0.1)] active:scale-95"
        >
          Get Started
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
