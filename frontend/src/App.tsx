import React, { useState, useEffect, useRef } from 'react';
import { 
  Copy, 
  Check, 
  Terminal as TerminalIcon, 
  Shield, 
  Database, 
  Chrome, 
  Cpu, 
  RefreshCw, 
  Github,
  ExternalLink
} from 'lucide-react';

// Simulated terminal messages for the typewriter demo
const TERMINAL_LOGS = [
  { text: 'akshat@local:~ $ akshat run --continuous', delay: 800 },
  { text: '[SYSTEM] Initializing AKSHAT Software Engineer Daemon...', delay: 600 },
  { text: '[SYSTEM] Found GEMINI_API_KEY. Loading Gemini 3.5 Flash...', delay: 500 },
  { text: '[SYSTEM] Local sqlite memory active. 14 tasks in database.', delay: 400 },
  { text: '[MONITOR] Scanning local workspace directory: C:/Users/ijain/projects...', delay: 600 },
  { text: '[MONITOR] Detected 3 modified files in branch "master" of "resume-automation".', delay: 700 },
  { text: '[PLANNER] Action flow: [Analyze Git Changes] -> [Summarize Commit] -> [Deploy Page] -> [Sync Profile]', delay: 600 },
  { text: '[DEVELOPER] Running unit-tests locally to verify build compatibility...', delay: 1000 },
  { text: '[TESTER] 4 unit tests executed. Results: 100% success. Build compiles OK.', delay: 800 },
  { text: '[INTEGRATOR] Auto-pushing git commit "feat: update portfolio integrations" to master...', delay: 900 },
  { text: '[INTEGRATOR] Git push completed successfully.', delay: 400 },
  { text: '[SCRAPER] Playwright launching Chromium persistent browser instance...', delay: 800 },
  { text: '[SCRAPER] Copying local cookies & credentials session...', delay: 500 },
  { text: '[SCRAPER] Syncing portfolio changes to LinkedIn status...', delay: 900 },
  { text: '[SCRAPER] LinkedIn profile sync successful. Status updated.', delay: 600 },
  { text: '[SYSTEM] Task complete. Returning to background monitoring...', delay: 500 },
  { text: '[SYSTEM] Daemon sleeping for 3600 seconds... zzz', delay: 1200 },
];

export const App: React.FC = () => {
  const [osTab, setOsTab] = useState<'unix' | 'windows'>('unix');
  const [copiedStep, setCopiedStep] = useState<number | null>(null);
  
  // Terminal Typing Simulation State
  const [terminalLines, setTerminalLines] = useState<string[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [typedText, setTypedText] = useState('');
  const [charIndex, setCharIndex] = useState(0);
  const terminalBottomRef = useRef<HTMLDivElement | null>(null);

  // Copy-to-clipboard handler
  const handleCopy = (text: string, stepId: number) => {
    navigator.clipboard.writeText(text);
    setCopiedStep(stepId);
    setTimeout(() => {
      setCopiedStep(null);
    }, 2000);
  };

  // Typewriter effect for terminal simulation
  useEffect(() => {
    if (currentLineIndex >= TERMINAL_LOGS.length) {
      // Pause at the end, then restart simulation
      const timer = setTimeout(() => {
        setTerminalLines([]);
        setCurrentLineIndex(0);
        setTypedText('');
        setCharIndex(0);
      }, 4000);
      return () => clearTimeout(timer);
    }

    const currentLog = TERMINAL_LOGS[currentLineIndex];
    
    // Typing simulation for the current line
    if (charIndex < currentLog.text.length) {
      const charTimer = setTimeout(() => {
        setTypedText((prev) => prev + currentLog.text[charIndex]);
        setCharIndex((prev) => prev + 1);
      }, Math.max(10, 30 - charIndex)); // speed up typing
      return () => clearTimeout(charTimer);
    } else {
      // Completed typing current line, add it to list and move to next
      const lineTimer = setTimeout(() => {
        setTerminalLines((prev) => [...prev, currentLog.text]);
        setTypedText('');
        setCharIndex(0);
        setCurrentLineIndex((prev) => prev + 1);
      }, currentLog.delay);
      return () => clearTimeout(lineTimer);
    }
  }, [currentLineIndex, charIndex]);

  // Autoscroll terminal
  useEffect(() => {
    if (terminalBottomRef.current) {
      terminalBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalLines, typedText]);

  // Install codes based on tab selection
  const installCmd = osTab === 'unix' 
    ? 'git clone https://github.com/akshat2685/AKSHAT_software_engineer.git && cd AKSHAT_software_engineer'
    : 'git clone https://github.com/akshat2685/AKSHAT_software_engineer.git ; cd AKSHAT_software_engineer';

  const configureCmd = osTab === 'unix'
    ? 'pip install -r requirements.txt && python src/akshat_local.py'
    : 'pip install -r requirements.txt ; python src/akshat_local.py';

  return (
    <div className="relative min-h-screen bg-[#faf8f5] text-[#1c1917] selection:bg-[#ff2702] selection:text-[#faf8f5] font-body paper-overlay">
      {/* Outer wrapper max width matching Nous style */}
      <div className="mx-auto max-w-[1400px] p-6 md:p-10">
        
        {/* Navigation Header */}
        <header className="border-b border-[#1c1917]/20 pb-4 mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="font-display text-4xl tracking-wider font-bold text-[#1c1917]">
                AKSHAT / AGENT
              </span>
              <span className="border border-[#1c1917]/40 px-2 py-0.5 text-[10px] tracking-widest font-mono uppercase opacity-70">
                v1.2.0
              </span>
            </div>
            
            <nav className="flex items-center gap-6 font-sharetech text-sm tracking-widest uppercase">
              <a href="#demo" className="group relative hover:text-[#ff2702] transition-colors py-1">
                Demo
                <span className="blink hidden group-hover:inline-block ml-1 font-bold">■</span>
              </a>
              <a href="#features" className="group relative hover:text-[#ff2702] transition-colors py-1">
                Features
                <span className="blink hidden group-hover:inline-block ml-1 font-bold">■</span>
              </a>
              <a 
                href="https://github.com/akshat2685/AKSHAT_software_engineer" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="flex items-center gap-1 hover:text-[#ff2702] transition-colors py-1"
              >
                GitHub <Github size={14} />
              </a>
            </nav>
          </div>
        </header>

        {/* Hero Section */}
        <section className="flex flex-col items-center justify-center text-center py-12 md:py-20 border-b border-[#1c1917]/20">
          <div className="mb-4">
            <span className="font-sharetech text-xs tracking-[0.2em] uppercase opacity-70 bg-[#1c1917]/5 px-3 py-1 border border-[#1c1917]/10 rounded-full">
              Open Source • MIT License • Local-First
            </span>
          </div>
          
          <h1 className="font-display text-5xl sm:text-7xl font-bold uppercase tracking-tight text-[#1c1917] max-w-4xl leading-[0.95] mt-4">
            The Software Agent<br/>That Lives in Your Workspace.
          </h1>
          
          <p className="mt-6 text-base sm:text-lg max-w-2xl text-[#1c1917]/75 font-body leading-relaxed">
            Not an IDE-tethered copilot or a simple API wrapper. AKSHAT is an autonomous workspace daemon that runs locally on your machine, continuously monitors your repositories, deploys static bundles, and updates your professional profile.
          </p>

          {/* Setup / Instructions Block */}
          <div className="w-full max-w-[580px] mt-10 text-left border border-[#1c1917]/20 bg-white/50 backdrop-blur-sm p-5 md:p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#1c1917]/15 pb-2 mb-4">
              <span className="font-sharetech text-xs tracking-wider uppercase text-[#1c1917]/70">
                Setup Instructions
              </span>
              <div className="inline-flex border border-[#1c1917]/20 bg-white/80 p-0.5 text-xs font-sharetech tracking-wider uppercase">
                <button 
                  onClick={() => setOsTab('unix')}
                  className={`px-3 py-1 cursor-pointer transition-colors ${osTab === 'unix' ? 'bg-[#1c1917] text-[#faf8f5]' : 'text-[#1c1917]/60 hover:text-[#1c1917]'}`}
                >
                  macOS / Linux
                </button>
                <button 
                  onClick={() => setOsTab('windows')}
                  className={`px-3 py-1 cursor-pointer transition-colors ${osTab === 'windows' ? 'bg-[#1c1917] text-[#faf8f5]' : 'text-[#1c1917]/60 hover:text-[#1c1917]'}`}
                >
                  Windows
                </button>
              </div>
            </div>

            {/* Step 1 */}
            <div className="flex flex-col gap-1.5 mb-4">
              <div className="flex items-center justify-between text-xs font-sharetech uppercase tracking-wider text-[#1c1917]/50">
                <span>1. Clone & Navigate</span>
                <button 
                  onClick={() => handleCopy(installCmd, 1)}
                  className="hover:text-[#ff2702] transition-colors flex items-center gap-1 font-mono text-[10px] uppercase cursor-pointer"
                >
                  {copiedStep === 1 ? <Check size={11} className="text-green-600" /> : <Copy size={11} />}
                  {copiedStep === 1 ? 'Copied' : 'Copy'}
                </button>
              </div>
              <div className="font-mono bg-[#1c1917]/5 border border-[#1c1917]/15 px-3 py-2 text-xs text-[#1c1917] break-all overflow-x-auto whitespace-pre-wrap select-all">
                <code>{installCmd}</code>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-xs font-sharetech uppercase tracking-wider text-[#1c1917]/50">
                <span>2. Bootstrap & Launch Daemon</span>
                <button 
                  onClick={() => handleCopy(configureCmd, 2)}
                  className="hover:text-[#ff2702] transition-colors flex items-center gap-1 font-mono text-[10px] uppercase cursor-pointer"
                >
                  {copiedStep === 2 ? <Check size={11} className="text-green-600" /> : <Copy size={11} />}
                  {copiedStep === 2 ? 'Copied' : 'Copy'}
                </button>
              </div>
              <div className="font-mono bg-[#1c1917]/5 border border-[#1c1917]/15 px-3 py-2 text-xs text-[#1c1917] break-all overflow-x-auto whitespace-pre-wrap select-all">
                <code>{configureCmd}</code>
              </div>
            </div>
          </div>
        </section>

        {/* Action Demo Section */}
        <section id="demo" className="py-12 md:py-16 border-b border-[#1c1917]/20">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-2 mb-3">
              <span className="font-sharetech text-xs tracking-widest uppercase opacity-75">
                [ See It in Action ]
              </span>
            </div>

            {/* Retro Double-Border Terminal Mockup */}
            <div className="border-double-custom border-[#1c1917] bg-[#1c1917] text-[#faf8f5] shadow-lg crt-effect">
              {/* Header Bar */}
              <div className="flex items-center justify-between border-b border-[#faf8f5]/15 px-4 py-2 bg-[#1c1917]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#ff2702]" />
                  <span className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
                  <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
                </div>
                <span className="font-mono text-xs tracking-wider text-[#faf8f5]/60">
                  akshat@workspace-agent:~
                </span>
                <span className="font-mono text-xs text-[#faf8f5]/40 uppercase tracking-widest">
                  ttyS0
                </span>
              </div>

              {/* Terminal Screen Console */}
              <div className="p-4 font-mono text-xs leading-[1.6] h-[340px] overflow-y-auto select-text selection:bg-[#faf8f5] selection:text-[#1c1917]">
                {terminalLines.map((line, idx) => {
                  const isCmd = line.startsWith('akshat@local');
                  const isError = line.includes('[ERROR]');
                  const isSystem = line.includes('[SYSTEM]');
                  const isScraper = line.includes('[SCRAPER]');
                  const isDev = line.includes('[DEVELOPER]') || line.includes('[TESTER]');
                  
                  let colorClass = 'text-[#faf8f5]/90';
                  if (isCmd) colorClass = 'text-[#ff2702] font-bold';
                  else if (isError) colorClass = 'text-red-400';
                  else if (isSystem) colorClass = 'text-cyan';
                  else if (isScraper) colorClass = 'text-amber-300';
                  else if (isDev) colorClass = 'text-emerald-400';

                  return (
                    <div key={idx} className={`${colorClass} whitespace-pre-wrap break-all mb-1`}>
                      {line}
                    </div>
                  );
                })}
                
                {/* Currently typing line */}
                {currentLineIndex < TERMINAL_LOGS.length && (
                  <div className={`${TERMINAL_LOGS[currentLineIndex].text.startsWith('akshat@local') ? 'text-[#ff2702] font-bold' : 'text-[#faf8f5]/90'} whitespace-pre-wrap break-all`}>
                    {typedText}
                    <span className="blink inline-block w-[1.2ch] h-[1.1em] bg-white -mb-[0.1em] ml-0.5" />
                  </div>
                )}
                
                {/* Idle Blinking Cursor when simulation is completed */}
                {currentLineIndex >= TERMINAL_LOGS.length && (
                  <div className="text-[#faf8f5]/50 italic text-[10px] mt-3">
                    Simulation finished. Restarting in 4s...
                    <span className="blink inline-block w-[1.2ch] h-[1.1em] bg-[#faf8f5]/50 -mb-[0.1em] ml-1" />
                  </div>
                )}
                
                <div ref={terminalBottomRef} />
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-12 md:py-20 border-b border-[#1c1917]/20">
          <div className="mb-6">
            <span className="font-sharetech text-xs tracking-widest uppercase opacity-75">
              [ Core Features ]
            </span>
          </div>

          {/* Grid Layout mimicking Nous Research retro-grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 border-collapse border border-[#1c1917]/20 bg-white/40">
            
            {/* Feature 1 */}
            <div className="border border-[#1c1917]/10 p-6 md:p-8 hover:bg-[#1c1917]/5 transition-colors duration-250 relative group">
              <div className="flex items-center gap-3 mb-3">
                <Shield size={20} className="text-[#ff2702]" />
                <h3 className="font-display text-2xl font-bold uppercase tracking-wider text-[#1c1917]">
                  Local-First Security
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-[#1c1917]/75 font-body normal-case">
                Your credentials, private API tokens, session cookies, and git history remain securely on your local file system. AKSHAT never uploads private developer access keys to external cloud databases.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="border border-[#1c1917]/10 p-6 md:p-8 hover:bg-[#1c1917]/5 transition-colors duration-250 relative group">
              <div className="flex items-center gap-3 mb-3">
                <RefreshCw size={20} className="text-[#ff2702]" />
                <h3 className="font-display text-2xl font-bold uppercase tracking-wider text-[#1c1917]">
                  Git Monitor Daemon
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-[#1c1917]/75 font-body normal-case">
                A background file watcher periodically scans local git branches, reads modified files, structures logical updates, and logs weekly summaries directly to your developer profile automatically.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="border border-[#1c1917]/10 p-6 md:p-8 hover:bg-[#1c1917]/5 transition-colors duration-250 relative group">
              <div className="flex items-center gap-3 mb-3">
                <Chrome size={20} className="text-[#ff2702]" />
                <h3 className="font-display text-2xl font-bold uppercase tracking-wider text-[#1c1917]">
                  Profile Syncer
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-[#1c1917]/75 font-body normal-case">
                Leverages custom Playwright instances to copy Chrome or Edge persistent profiles. Securely bypasses auth-walls to synchronize your workspace developments with platforms like LinkedIn.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="border border-[#1c1917]/10 p-6 md:p-8 hover:bg-[#1c1917]/5 transition-colors duration-250 relative group">
              <div className="flex items-center gap-3 mb-3">
                <Cpu size={20} className="text-[#ff2702]" />
                <h3 className="font-display text-2xl font-bold uppercase tracking-wider text-[#1c1917]">
                  Gemini Reasoning
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-[#1c1917]/75 font-body normal-case">
                Powered by Google Gemini 3.5 Flash. It rapidly generates commit messages, details architectural designs, parses developer events, and analyzes logs using lightweight but high-context prompting.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="border border-[#1c1917]/10 p-6 md:p-8 hover:bg-[#1c1917]/5 transition-colors duration-250 relative group">
              <div className="flex items-center gap-3 mb-3">
                <TerminalIcon size={20} className="text-[#ff2702]" />
                <h3 className="font-display text-2xl font-bold uppercase tracking-wider text-[#1c1917]">
                  Self-Healing Deploys
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-[#1c1917]/75 font-body normal-case">
                Validates the workspace frontend builds, verifies local unit test suites, fixes compilation warnings, and commits stable files to your remote repository without human intervention.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="border border-[#1c1917]/10 p-6 md:p-8 hover:bg-[#1c1917]/5 transition-colors duration-250 relative group">
              <div className="flex items-center gap-3 mb-3">
                <Database size={20} className="text-[#ff2702]" />
                <h3 className="font-display text-2xl font-bold uppercase tracking-wider text-[#1c1917]">
                  Zero Admin Task
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-[#1c1917]/75 font-body normal-case">
                Registers background daemons seamlessly as non-elevated Windows Startup tasks or persistent Task Scheduler items, allowing offline execution without needing persistent root privileges.
              </p>
            </div>

          </div>
        </section>

        {/* Footer */}
        <footer className="pt-8 pb-16 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 text-xs font-sharetech tracking-wider uppercase text-[#1c1917]/60">
          <div>
            AKSHAT AGENT • MIT LICENSE • 2026
          </div>
          <div className="flex items-center gap-6">
            <a 
              href="https://github.com/akshat2685/AKSHAT_software_engineer" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="flex items-center gap-1 hover:text-[#ff2702] transition-colors"
            >
              GitHub <ExternalLink size={12} />
            </a>
            <a 
              href="https://hermes-agent.nousresearch.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[#ff2702] transition-colors"
            >
              Inspired by Nous Research ↗
            </a>
          </div>
        </footer>

      </div>
    </div>
  );
};

export default App;
