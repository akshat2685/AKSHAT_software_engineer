import React, { useState, useEffect, useRef } from 'react';
import { useStore } from './stores/projectStore';
import { WebSocketClient } from './services/websocket';
import { Dashboard } from './pages/Dashboard';
import { Projects } from './pages/Projects';
import { Timeline } from './pages/Timeline';
import { SettingsModal } from './components/SettingsModal';
import { 
  LogOut, 
  Layers, 
  LayoutDashboard, 
  FolderGit2, 
  Lock, 
  Mail,
  Settings,
  Copy, 
  Check, 
  Terminal as TerminalIcon, 
  Shield, 
  Database, 
  Chrome, 
  Cpu, 
  RefreshCw, 
  Github,
  ExternalLink,
  Home
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
  const { 
    token, 
    email,
    isAuthenticated, 
    login, 
    registerUser, 
    logout,
    currentPage,
    setCurrentPage,
    selectedProject,
    systemState, 
    theme, 
    density, 
    fetchStatus, 
    setTheme, 
    setDensity, 
    setSystemState,
    setSettingsOpen
  } = useStore();

  // Navigation state (landing page vs functional app dashboard)
  const [viewMode, setViewMode] = useState<'landing' | 'app'>('landing');

  // Auth local state
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authRememberMe, setAuthRememberMe] = useState(false);

  // Landing Page Local State
  const [osTab, setOsTab] = useState<'unix' | 'windows'>('unix');
  const [copiedStep, setCopiedStep] = useState<number | null>(null);
  const [terminalLines, setTerminalLines] = useState<string[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [typedText, setTypedText] = useState('');
  const [charIndex, setCharIndex] = useState(0);

  const bgCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const terminalBottomRef = useRef<HTMLDivElement | null>(null);

  // Connection status & details
  useEffect(() => {
    if (!isAuthenticated() || viewMode !== 'app') return;
    fetchStatus();

    const ws = new WebSocketClient((payload) => {
      if (payload.data) {
        const data = payload.data;
        const workflow = data.workflow || {};
        setSystemState({
          project_id: data.task_id || 'idle',
          project_name: data.project_name || 'AKSHAT Engineering OS',
          status: data.status || 'idle',
          avatar_state: data.avatar_state || 'Idle',
          current_agent: data.current_agent || workflow.current_agent || 'Idle',
          current_action: data.status === 'success' ? 'Ready for next prompt' : data.current_action || 'Waiting for prompt',
          task_type: data.task_type || workflow.task_type || 'general',
          requirements: workflow.requirements || data.requirements || [],
          architecture: workflow.architecture || data.architecture || [],
          tasks: data.plan || workflow.tasks || [],
          todo_list: data.todo_list || [],
          steps_done: data.steps_done || [],
          events: workflow.events || [],
          quality_score: data.quality_score ?? workflow.quality_score ?? 0,
          security_score: data.security_score ?? workflow.security_score ?? 0,
          iteration_count: data.iteration_count ?? workflow.iteration_count ?? 0,
          created_files: data.created_files || workflow.created_files || [],
          deployment_url: data.deployment_url || workflow.deployment_url || '',
          deployment_status: data.deployment_status || 'pending',
          final_deliverable: data.final_deliverable || '',
          final_result: data.final_result || '',
          active_tools: data.active_tools || [],
          chat: data.chat || [],
        });
      }
    });

    ws.connect();
    return () => {
      ws.disconnect();
    };
  }, [token, viewMode]);

  // Neural network background effect for app view
  useEffect(() => {
    if (viewMode !== 'app' || !bgCanvasRef.current) return;
    const canvas = bgCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let isScrolling = false;
    let scrollTimer: ReturnType<typeof setTimeout>;
    let particles: Array<{ x: number; y: number; vx: number; vy: number; r: number }> = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      // Reduced max from 80 → 40 to cut the O(n²) connection loop cost
      const count = Math.max(20, Math.min(40, Math.floor((canvas.width * canvas.height) / 40000)));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: 1 + Math.random() * 1.2,
      }));
    };

    // Pause animation during scroll to eliminate jank
    const onScroll = () => {
      isScrolling = true;
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(() => { isScrolling = false; }, 150);
    };

    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('scroll', onScroll, { passive: true });

    const strokeColor = theme === 'violet' ? '#8b5cf6' : theme === 'emerald' ? '#10b981' : '#3b82f6';
    const fillColor = strokeColor;

    const draw = () => {
      animId = requestAnimationFrame(draw);
      // Skip render during scroll to prevent layout jank
      if (isScrolling) return;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = strokeColor;
      ctx.fillStyle = fillColor;

      // Reduced connection distance from 150 → 120
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.globalAlpha = (1 - dist / 120) * 0.12;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      ctx.globalAlpha = 0.45;
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
    };

    draw();
    return () => {
      cancelAnimationFrame(animId);
      clearTimeout(scrollTimer);
      window.removeEventListener('resize', resize);
      window.removeEventListener('scroll', onScroll);
    };
  }, [theme, viewMode]);


  // Copy-to-clipboard handler for Quick Start
  const handleCopy = (text: string, stepId: number) => {
    navigator.clipboard.writeText(text);
    setCopiedStep(stepId);
    setTimeout(() => {
      setCopiedStep(null);
    }, 2000);
  };

  // Typewriter effect for terminal simulation
  useEffect(() => {
    if (viewMode !== 'landing') return;
    if (currentLineIndex >= TERMINAL_LOGS.length) {
      const timer = setTimeout(() => {
        setTerminalLines([]);
        setCurrentLineIndex(0);
        setTypedText('');
        setCharIndex(0);
      }, 4000);
      return () => clearTimeout(timer);
    }

    const currentLog = TERMINAL_LOGS[currentLineIndex];
    
    if (charIndex < currentLog.text.length) {
      const charTimer = setTimeout(() => {
        setTypedText((prev) => prev + currentLog.text[charIndex]);
        setCharIndex((prev) => prev + 1);
      }, Math.max(10, 30 - charIndex));
      return () => clearTimeout(charTimer);
    } else {
      const lineTimer = setTimeout(() => {
        setTerminalLines((prev) => [...prev, currentLog.text]);
        setTypedText('');
        setCharIndex(0);
        setCurrentLineIndex((prev) => prev + 1);
      }, currentLog.delay);
      return () => clearTimeout(lineTimer);
    }
  }, [currentLineIndex, charIndex, viewMode]);

  // Autoscroll terminal
  useEffect(() => {
    if (terminalBottomRef.current) {
      terminalBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalLines, typedText]);

  // Auth actions handlers
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authEmail || !authPassword) {
      setAuthError('Please fill in all fields.');
      return;
    }
    setAuthError('');
    setAuthLoading(true);

    try {
      const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register';
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      if (authMode === 'login') {
        login(data.token, data.email, data.user_id, authRememberMe);
      } else {
        registerUser(data.token, data.email, data.user_id, authRememberMe);
      }
      setAuthEmail('');
      setAuthPassword('');
    } catch (err: any) {
      setAuthError(err.message || 'Server error occurred.');
    } finally {
      setAuthLoading(false);
    }
  };

  const installCmd = osTab === 'unix' 
    ? 'git clone https://github.com/akshat2685/AKSHAT_software_engineer.git && cd AKSHAT_software_engineer'
    : 'git clone https://github.com/akshat2685/AKSHAT_software_engineer.git ; cd AKSHAT_software_engineer';

  const configureCmd = osTab === 'unix'
    ? 'pip install -r requirements.txt && python src/akshat_local.py'
    : 'pip install -r requirements.txt ; python src/akshat_local.py';

  const activeAgent = systemState?.current_agent || 'Ready';

  // --- VIEW 1: LANDING PAGE ---
  if (viewMode === 'landing') {
    return (
      <div className="relative min-h-screen text-foreground overflow-hidden">
        {/* Animated Background Blobs */}
        <div className="blob-bg blob-1"></div>
        <div className="blob-bg blob-2"></div>

        {/* Main Content Wrapper */}
        <div className="relative z-10 mx-auto max-w-7xl px-6 lg:px-8 flex flex-col min-h-screen">
          
          {/* Navbar */}
          <header className="py-6 flex items-center justify-between border-b border-white/10 animate-fade-in-up">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                A
              </div>
              <span className="font-display text-xl font-bold tracking-tight text-white">
                AKSHAT<span className="text-white/50 font-normal"> / AGENT</span>
              </span>
              <span className="ml-2 rounded-full bg-primary/20 border border-primary/30 px-2.5 py-0.5 text-xs font-semibold text-primary">
                v1.2.0
              </span>
            </div>
            
            <nav className="flex items-center gap-4 md:gap-8 font-medium text-sm text-slate-300">
              <a href="#features" className="hover:text-white transition-colors hidden sm:inline-block">Features</a>
              <a 
                href="https://github.com/akshat2685/AKSHAT_software_engineer" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="items-center gap-2 hover:text-white transition-colors hidden sm:flex"
              >
                <Github size={16} />
                GitHub
              </a>
              <button 
                onClick={() => setViewMode('app')}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-primary to-accent text-white font-semibold text-xs hover:brightness-110 transition-all shadow-[0_0_15px_rgba(59,130,246,0.3)]"
              >
                Launch App
              </button>
            </nav>
          </header>

          {/* Hero Section */}
          <section className="flex flex-col lg:flex-row items-center justify-between py-20 gap-16 lg:gap-8 flex-1 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            
            {/* Left: Text & CTA */}
            <div className="lg:w-1/2 flex flex-col items-start">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300 mb-6 backdrop-blur-md">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                Local-First & Open Source
              </div>
              
              <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.1] mb-6">
                The Agent That <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent text-glow">
                  Lives in Your Workspace.
                </span>
              </h1>
              
              <p className="text-lg text-slate-400 font-body leading-relaxed max-w-xl mb-8">
                Not an IDE-tethered copilot or a simple API wrapper. AKSHAT is an autonomous workspace daemon that runs locally on your machine, continuously monitors your repositories, deploys static bundles, and updates your professional profile.
              </p>

              <button 
                onClick={() => setViewMode('app')}
                className="mb-8 px-6 py-3 rounded-lg bg-gradient-to-r from-primary to-accent text-white font-bold hover:scale-102 hover:brightness-110 active:scale-98 transition-all shadow-lg shadow-primary/20 flex items-center gap-2"
              >
                <Cpu size={16} />
                Open Agent Dashboard
              </button>
              
              {/* Glass Setup Block */}
              <div className="w-full max-w-lg glass-panel rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-semibold text-slate-300">Quick Start</span>
                  <div className="flex bg-slate-900/50 rounded-lg p-1 border border-white/5">
                    <button 
                      onClick={() => setOsTab('unix')}
                      className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${osTab === 'unix' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
                    >
                      macOS / Linux
                    </button>
                    <button 
                      onClick={() => setOsTab('windows')}
                      className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${osTab === 'windows' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
                    >
                      Windows
                    </button>
                  </div>
                </div>

                {/* Step 1 */}
                <div className="mb-4">
                  <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
                    <span>1. Clone & Navigate</span>
                    <button onClick={() => handleCopy(installCmd, 1)} className="hover:text-primary transition-colors flex items-center gap-1">
                      {copiedStep === 1 ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                    </button>
                  </div>
                  <div className="bg-slate-950/80 border border-white/5 rounded-lg p-3 overflow-x-auto font-mono text-sm text-slate-300">
                    <code>{installCmd}</code>
                  </div>
                </div>

                {/* Step 2 */}
                <div>
                  <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
                    <span>2. Bootstrap Daemon</span>
                    <button onClick={() => handleCopy(configureCmd, 2)} className="hover:text-primary transition-colors flex items-center gap-1">
                      {copiedStep === 2 ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                    </button>
                  </div>
                  <div className="bg-slate-950/80 border border-white/5 rounded-lg p-3 overflow-x-auto font-mono text-sm text-slate-300">
                    <code>{configureCmd}</code>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Modern Terminal */}
            <div className="lg:w-1/2 w-full max-w-2xl mt-10 lg:mt-0">
              <div className="glass-panel rounded-xl overflow-hidden shadow-2xl border border-white/10 flex flex-col h-[450px]">
                {/* Terminal Header with Non-overlapping 3-column layout */}
                <div className="bg-slate-900/80 border-b border-white/5 px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-2 w-16">
                    <span className="mac-btn mac-close"></span>
                    <span className="mac-btn mac-minimize"></span>
                    <span className="mac-btn mac-maximize"></span>
                  </div>
                  <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
                    <TerminalIcon size={14} /> akshat@workspace:~
                  </div>
                  <div className="w-16"></div>
                </div>

                {/* Terminal Body */}
                <div className="flex-1 p-5 font-mono text-sm leading-relaxed overflow-y-auto bg-slate-950/50">
                  {terminalLines.map((line, idx) => {
                    const isCmd = line.startsWith('akshat@local');
                    const isError = line.includes('[ERROR]');
                    const isSystem = line.includes('[SYSTEM]');
                    const isScraper = line.includes('[SCRAPER]');
                    const isDev = line.includes('[DEVELOPER]') || line.includes('[TESTER]');
                    
                    let colorClass = 'text-slate-300';
                    if (isCmd) colorClass = 'text-primary font-bold';
                    else if (isError) colorClass = 'text-red-400';
                    else if (isSystem) colorClass = 'text-cyan-400';
                    else if (isScraper) colorClass = 'text-amber-400';
                    else if (isDev) colorClass = 'text-green-400';

                    return (
                      <div key={idx} className={`${colorClass} whitespace-pre-wrap break-all mb-1`}>
                        {line}
                      </div>
                    );
                  })}
                  
                  {/* Currently typing line */}
                  {currentLineIndex < TERMINAL_LOGS.length && (
                    <div className={`${TERMINAL_LOGS[currentLineIndex].text.startsWith('akshat@local') ? 'text-primary font-bold' : 'text-slate-300'} whitespace-pre-wrap break-all`}>
                      {typedText}
                      <span className="blink inline-block w-[1.2ch] h-[1.1em] bg-white/80 align-middle ml-1 rounded-sm" />
                    </div>
                  )}
                  
                  {currentLineIndex >= TERMINAL_LOGS.length && (
                    <div className="text-slate-500 italic text-xs mt-4">
                      Simulation finished. Restarting in 4s...
                      <span className="blink inline-block w-[1.2ch] h-[1.1em] bg-slate-500/50 align-middle ml-1 rounded-sm" />
                    </div>
                  )}
                  <div ref={terminalBottomRef} />
                </div>
              </div>
            </div>
          </section>

          {/* Features Section */}
          <section id="features" className="py-24 border-t border-white/5 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Autonomous Capabilities</h2>
              <p className="text-slate-400 max-w-2xl mx-auto">Everything you need for an AI developer that continuously works in the background.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Feature 1 */}
              <div className="glass-card rounded-2xl p-8 group">
                <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Shield className="text-blue-400" size={24} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Local-First Security</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Your credentials, private API tokens, session cookies, and git history remain securely on your local file system. Never uploads private keys to the cloud.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="glass-card rounded-2xl p-8 group">
                <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <RefreshCw className="text-emerald-400" size={24} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Git Monitor Daemon</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  A background file watcher scans local git branches, reads modified files, structures logical updates, and logs weekly summaries directly to your profile.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="glass-card rounded-2xl p-8 group">
                <div className="w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Chrome className="text-amber-400" size={24} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Profile Syncer</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Leverages custom Playwright instances to securely copy browser profiles. Bypass auth-walls to synchronize your workspace developments with LinkedIn.
                </p>
              </div>

              {/* Feature 4 */}
              <div className="glass-card rounded-2xl p-8 group">
                <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Cpu className="text-purple-400" size={24} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Gemini Reasoning</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Powered by Gemini 3.5 Flash. Rapidly generates commit messages, details architectural designs, parses developer events, and analyzes logs efficiently.
                </p>
              </div>

              {/* Feature 5 */}
              <div className="glass-card rounded-2xl p-8 group">
                <div className="w-12 h-12 rounded-lg bg-cyan-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <TerminalIcon className="text-cyan-400" size={24} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Self-Healing Deploys</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Validates the workspace frontend builds, verifies local unit test suites, fixes compilation warnings, and commits stable files without human intervention.
                </p>
              </div>

              {/* Feature 6 */}
              <div className="glass-card rounded-2xl p-8 group">
                <div className="w-12 h-12 rounded-lg bg-rose-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Database className="text-rose-400" size={24} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Zero Admin Task</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Registers background daemons seamlessly as non-elevated Windows Startup tasks, allowing offline execution without needing persistent root privileges.
                </p>
              </div>
            </div>
          </section>

          {/* Footer */}
          <footer className="mt-auto py-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-slate-500">
            <p>© 2026 AKSHAT Agent. Released under MIT License.</p>
            <div className="flex items-center gap-6">
              <a href="https://github.com/akshat2685/AKSHAT_software_engineer" className="hover:text-white transition-colors flex items-center gap-1">
                GitHub <ExternalLink size={14} />
              </a>
            </div>
          </footer>
        </div>
      </div>
    );
  }

  // --- VIEW 2: DASHBOARD APPLICATION ---
  // A. Render Login/Register if not authenticated
  if (!isAuthenticated()) {
    return (
      <div className="relative min-h-screen flex items-center justify-center bg-slate-950 text-foreground overflow-hidden">
        {/* Animated Blobs */}
        <div className="blob-bg blob-1"></div>
        <div className="blob-bg blob-2"></div>

        <div className="w-full max-w-md p-8 rounded-2xl glass-panel relative z-10 shadow-2xl border border-white/10 flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold">
                A
              </div>
              <span className="font-display text-lg font-bold text-white">AKSHAT Command Center</span>
            </div>
            <button 
              onClick={() => setViewMode('landing')}
              className="text-slate-400 hover:text-white transition-colors flex items-center gap-1 text-xs font-semibold"
            >
              <Home size={14} /> Home
            </button>
          </div>

          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2">Welcome Back</h2>
            <p className="text-xs text-slate-400">
              {authMode === 'login' ? 'Please log in to manage your agent daemon' : 'Create an account to startup the orchestrator'}
            </p>
          </div>

          <form onSubmit={handleAuth} className="flex flex-col gap-4">
            {authError && (
              <div className="p-3 border border-red-500/30 bg-red-500/10 rounded-lg text-xs text-red-400 text-center font-semibold">
                {authError}
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Email Address</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"><Mail size={16} /></span>
                <input 
                  type="email" 
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  placeholder="dev@example.com"
                  className="w-full bg-slate-900 border border-white/10 focus:border-primary/50 outline-none rounded-lg pl-10 pr-4 py-2.5 text-sm text-white font-mono"
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Password</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"><Lock size={16} /></span>
                <input 
                  type="password" 
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-900 border border-white/10 focus:border-primary/50 outline-none rounded-lg pl-10 pr-4 py-2.5 text-sm text-white font-mono"
                  required
                />
              </div>
            </div>

            <div className="flex items-center gap-2 mt-1">
              <input 
                type="checkbox" 
                id="rememberMe"
                checked={authRememberMe}
                onChange={(e) => setAuthRememberMe(e.target.checked)}
                className="w-4 h-4 rounded border-white/10 bg-slate-900 text-primary focus:ring-primary/50"
              />
              <label htmlFor="rememberMe" className="text-xs text-slate-400 cursor-pointer">
                Remember my login session
              </label>
            </div>

            <button
              type="submit"
              disabled={authLoading}
              className="w-full mt-2 bg-gradient-to-r from-primary to-accent hover:brightness-110 active:scale-98 disabled:opacity-50 text-white font-bold py-2.5 rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-primary/20 transition-all cursor-pointer text-sm"
            >
              {authLoading ? 'Authorizing...' : (authMode === 'login' ? 'Login' : 'Sign Up')}
            </button>
          </form>

          <div className="text-center pt-2">
            <button
              onClick={() => {
                setAuthMode(authMode === 'login' ? 'register' : 'login');
                setAuthError('');
              }}
              className="text-xs text-primary font-bold hover:underline bg-transparent border-0 cursor-pointer"
            >
              {authMode === 'login' 
                ? "New to AKSHAT? Create a local user account"
                : 'Already registered? Sign in to your dashboard'
              }
            </button>
          </div>
        </div>
      </div>
    );
  }

  // B. Render App Views if authenticated
  return (
    <div className={`relative min-h-screen text-slate-200 bg-slate-950 ${density === 'compact' ? 'text-sm' : 'text-base'}`}>
      <canvas ref={bgCanvasRef} className="fixed inset-0 pointer-events-none z-[1]" style={{ willChange: 'transform', transform: 'translateZ(0)' }} />
      
      {/* Top Navbar */}
      <nav className="fixed left-1/2 -translate-x-1/2 top-4 w-[calc(100%-32px)] max-w-7xl h-16 z-50 flex items-center justify-between px-6 border border-white/10 rounded-lg bg-slate-950/80 shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold">
              A
            </div>
            <div className="font-display font-semibold tracking-wider hidden sm:block">
              AKSHAT <span className="text-[9px] text-slate-400 font-mono block tracking-widest leading-none">COMMAND CENTER</span>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center gap-2 pl-4 border-l border-white/10">
            <button
              onClick={() => setCurrentPage('dashboard')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer ${
                currentPage === 'dashboard' ? 'bg-primary/20 text-primary border border-primary/30' : 'text-slate-400 hover:text-white'
              }`}
            >
              <LayoutDashboard size={14} />
              <span>Dashboard</span>
            </button>

            <button
              onClick={() => setCurrentPage('projects')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer ${
                currentPage === 'projects' ? 'bg-primary/20 text-primary border border-primary/30' : 'text-slate-400 hover:text-white'
              }`}
            >
              <FolderGit2 size={14} />
              <span>History</span>
            </button>

            <button
              onClick={() => {
                if (selectedProject) setCurrentPage('timeline');
              }}
              disabled={!selectedProject}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
                currentPage === 'timeline' ? 'bg-primary/20 text-primary border border-primary/30' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Layers size={14} />
              <span>Timeline</span>
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button 
            onClick={() => setViewMode('landing')}
            className="hidden md:flex items-center gap-1 px-3 py-1.5 border border-white/10 rounded-md text-xs font-semibold hover:bg-white/5 transition-colors text-slate-400 hover:text-white"
          >
            <Home size={14} /> Landing
          </button>

          <div className="hidden lg:flex items-center gap-3">
            <select 
              value={theme}
              onChange={(e) => setTheme(e.target.value as any)}
              className="bg-slate-900 border border-white/10 text-[11px] font-bold rounded px-2.5 py-1 outline-none text-slate-300 cursor-pointer"
            >
              <option value="cyan">Cyan</option>
              <option value="violet">Violet</option>
              <option value="emerald">Emerald</option>
            </select>

            <select 
              value={density}
              onChange={(e) => setDensity(e.target.value as any)}
              className="bg-slate-900 border border-white/10 text-[11px] font-bold rounded px-2.5 py-1 outline-none text-slate-300 cursor-pointer"
            >
              <option value="normal">Normal</option>
              <option value="compact">Compact</option>
            </select>
          </div>

          {/* Active indicator */}
          <div className="flex items-center gap-2 border border-green-500/20 bg-green-500/10 rounded-md px-3 py-1 text-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shrink-0" />
            <span className="font-mono text-green-400 font-semibold">{activeAgent}</span>
          </div>

          {/* Settings Button */}
          <button
            onClick={() => setSettingsOpen(true)}
            title="Configure LLM"
            className="p-2 border border-white/10 rounded-lg bg-slate-900/40 hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <Settings size={15} />
          </button>

          {/* Logout */}
          <button
            onClick={() => logout()}
            title={`Log out: ${email}`}
            className="p-2 border border-white/10 rounded-lg bg-slate-900/40 hover:bg-red-500/10 hover:border-red-500/30 text-slate-400 hover:text-red-400 transition-colors cursor-pointer"
          >
            <LogOut size={15} />
          </button>
        </div>
      </nav>

      {/* Main Grid View */}
      <main className="max-w-7xl mx-auto pt-24 pb-8 px-4 relative z-10">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'projects' && <Projects />}
        {currentPage === 'timeline' && <Timeline />}
      </main>

      {/* Modals */}
      <SettingsModal />
    </div>
  );
};

export default App;
