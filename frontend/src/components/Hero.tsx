import React, { useEffect, useRef } from 'react';
import { ChevronDown } from 'lucide-react';

export const Hero: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleEnded = () => {
      video.style.opacity = '0';
      setTimeout(() => {
        video.currentTime = 0;
        video.play();
        requestAnimationFrame(() => {
          video.style.opacity = '1';
        });
      }, 100);
    };

    video.addEventListener('ended', handleEnded);
    // Initial fade in
    requestAnimationFrame(() => {
      video.style.opacity = '1';
    });

    return () => {
      video.removeEventListener('ended', handleEnded);
    };
  }, []);

  return (
    <section className="relative min-h-screen flex flex-col overflow-hidden bg-background text-foreground">
      {/* Video Background */}
      <div className="absolute inset-0 w-full h-full overflow-hidden z-0">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full h-full object-cover transition-opacity duration-500 opacity-0"
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_065045_c44942da-53c6-4804-b734-f9e07fc22e08.mp4"
        />
      </div>

      {/* Blurred overlay shape */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[984px] h-[527px] opacity-90 bg-gray-950 blur-[82px] pointer-events-none z-0"></div>

      {/* Hero Content Wrapper */}
      <div className="relative z-10 flex flex-col flex-1 h-full">
        {/* Navbar */}
        <nav className="w-full py-5 px-8 flex flex-row items-center justify-between font-body">
          <div className="flex items-center gap-2">
            <span className="font-display font-bold text-xl tracking-wide">AKSHAT OS</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-foreground/90 font-medium text-sm">
            <button className="flex items-center gap-1 hover:text-white transition-colors">Features <ChevronDown size={14} /></button>
            <button className="hover:text-white transition-colors">Solutions</button>
            <button className="hover:text-white transition-colors">Plans</button>
            <button className="flex items-center gap-1 hover:text-white transition-colors">Learning <ChevronDown size={14} /></button>
          </div>
          <div>
            <button className="heroSecondary rounded-full px-4 py-2 text-sm font-semibold">Sign Up</button>
          </div>
        </nav>
        <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-foreground/20 to-transparent mt-[3px]"></div>

        {/* Center Content */}
        <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
          <h1 className="text-[120px] md:text-[220px] font-normal leading-[1.02] tracking-[-0.024em] font-display">
            <span className="text-foreground">Power </span>
            <span className="text-transparent bg-clip-text bg-gradient-to-l from-amber-300 via-purple-500 to-indigo-500">
              AI
            </span>
          </h1>
          <p className="text-hero-sub text-lg md:text-xl leading-8 max-w-md mt-[9px] opacity-80 font-body">
            The most powerful AI ever deployed<br />in software engineering and autonomy.
          </p>
        </div>

        {/* Marquee at bottom */}
        <div className="w-full max-w-5xl mx-auto pb-10 flex flex-col md:flex-row items-center gap-12 px-6">
          <div className="text-foreground/50 text-sm font-body text-center md:text-left shrink-0">
            Relied on by brands<br />across the globe
          </div>
          
          <div className="flex-1 overflow-hidden relative" style={{ maskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)' }}>
            <div className="flex whitespace-nowrap animate-marquee items-center gap-16 w-max">
              {/* Duplicate the array twice for seamless loop */}
              {[...Array(2)].map((_, i) => (
                <React.Fragment key={i}>
                  {['Vortex', 'Nimbus', 'Prysma', 'Cirrus', 'Kynder', 'Halcyn'].map((brand, idx) => (
                    <div key={`${i}-${idx}`} className="flex items-center gap-3">
                      <div className="liquid-glass w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold">
                        {brand[0]}
                      </div>
                      <span className="text-base font-semibold text-foreground font-body">{brand}</span>
                    </div>
                  ))}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
