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
  Shield, 
  Chrome, 
  Cpu, 
  RefreshCw, 
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

  // Determine initial view based on hostname
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const [viewMode, setViewMode] = useState<'landing' | 'app'>(isLocalhost ? 'app' : 'landing');

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
      <div className="relative min-h-screen bg-[#020617] text-slate-100 font-sans selection:bg-blue-500/30 selection:text-white pb-16">
        {/* Soft Ambient Background Glows */}
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none z-0"></div>
        <div className="absolute top-1/3 right-1/4 w-[600px] h-[600px] bg-violet-500/10 rounded-full blur-[140px] pointer-events-none z-0"></div>
        <div className="absolute bottom-10 left-10 w-[400px] h-[400px] bg-emerald-500/5 rounded-full blur-[100px] pointer-events-none z-0"></div>

        {/* Outer content container */}
        <div className="relative z-10 max-w-6xl mx-auto px-6 flex flex-col">
          
          {/* Elegant Navbar */}
          <header className="flex items-center justify-between py-6 border-b border-slate-800/80 mb-12">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-white font-extrabold shadow-[0_0_20px_rgba(59,130,246,0.4)]">
                A
              </div>
              <span className="font-semibold text-lg tracking-tight text-white font-display">
                AKSHAT <span className="text-slate-500 font-normal">/ AGENT</span>
              </span>
              <span className="bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] font-bold px-2 py-0.5 rounded-full">
                v1.2.0
              </span>
            </div>
            
            <nav className="flex items-center gap-6 text-sm">
              <a href="#features" className="text-slate-400 hover:text-white transition-colors">Features</a>
              <a href="#setup" className="text-slate-400 hover:text-white transition-colors">Setup Guide</a>
              <button 
                onClick={() => isLocalhost ? setViewMode('app') : (window.location.href = 'http://127.0.0.1:3000')}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-violet-600 text-white font-semibold text-xs hover:brightness-110 active:scale-95 transition-all shadow-[0_0_15px_rgba(59,130,246,0.3)]"
              >
                Launch Dashboard
              </button>
            </nav>
          </header>

          {/* Hero & Intro Section */}
          <section className="text-center max-w-3xl mx-auto mb-16">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/5 px-3.5 py-1 text-xs font-semibold text-blue-400 mb-6 backdrop-blur-md">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
              Local-First AI Software Engineer
            </div>
            
            <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-white mb-6 leading-tight font-display">
              The Agent That Lives <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-violet-400 to-indigo-400">
                Inside Your Workspace.
              </span>
            </h1>
            
            <p className="text-base sm:text-lg text-slate-400 leading-relaxed mb-8 max-w-2xl mx-auto">
              AKSHAT is an autonomous workspace daemon that runs locally on your machine, monitors your git repositories, executes builds, runs unit tests, and integrates summaries directly to your developer profiles.
            </p>

            <div className="flex justify-center gap-4">
              <button 
                onClick={() => isLocalhost ? setViewMode('app') : (window.location.href = 'http://127.0.0.1:3000')}
                className="px-6 py-3 rounded-lg bg-gradient-to-r from-blue-500 to-violet-600 text-white font-bold text-sm hover:scale-105 active:scale-95 transition-all shadow-lg shadow-blue-500/25 flex items-center gap-2"
              >
                <Cpu size={16} />
                Open Dashboard
              </button>
              <a 
                href="#setup"
                className="px-6 py-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-semibold text-sm hover:bg-slate-800 hover:text-white active:scale-95 transition-all flex items-center gap-2"
              >
                Get Started
              </a>
            </div>
          </section>

          {/* Quick Start Installation Block */}
          <section id="setup" className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-24 items-start">
            {/* Left side: Guide description and installation tab */}
            <div className="lg:col-span-5 flex flex-col justify-center">
              <h2 className="text-2xl font-bold text-white mb-4">Quick Start Setup</h2>
              <p className="text-slate-400 text-sm leading-relaxed mb-6">
                AKSHAT runs directly in your local terminal. Run the daemon on your PC, and connect it with the live client dashboard to watch tasks execute.
              </p>

              <div className="bg-[#0f172a]/60 border border-slate-800/80 rounded-xl p-5 backdrop-blur-md">
                <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Installation commands</span>
                  <div className="flex bg-slate-900/80 rounded-lg p-0.5 border border-slate-800">
                    <button 
                      onClick={() => setOsTab('unix')}
                      className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-all ${osTab === 'unix' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}
                    >
                      macOS / Linux
                    </button>
                    <button 
                      onClick={() => setOsTab('windows')}
                      className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-all ${osTab === 'windows' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}
                    >
                      Windows
                    </button>
                  </div>
                </div>

                {/* Step 1 */}
                <div className="mb-4">
                  <div className="flex justify-between items-center text-xs text-slate-400 mb-1.5">
                    <span>1. Clone Repository</span>
                    <button onClick={() => handleCopy(installCmd, 1)} className="text-slate-500 hover:text-blue-400 transition-colors">
                      {copiedStep === 1 ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                    </button>
                  </div>
                  <div className="bg-slate-950 border border-slate-800/60 rounded-lg p-3 overflow-x-auto font-mono text-xs text-slate-300">
                    <code>{installCmd}</code>
                  </div>
                </div>

                {/* Step 2 */}
                <div>
                  <div className="flex justify-between items-center text-xs text-slate-400 mb-1.5">
                    <span>2. Start Workspace Daemon</span>
                    <button onClick={() => handleCopy(configureCmd, 2)} className="text-slate-500 hover:text-blue-400 transition-colors">
                      {copiedStep === 2 ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                    </button>
                  </div>
                  <div className="bg-slate-950 border border-slate-800/60 rounded-lg p-3 overflow-x-auto font-mono text-xs text-slate-300">
                    <code>{configureCmd}</code>
                  </div>
                </div>
              </div>
            </div>

            {/* Right side: Mock terminal preview */}
            <div className="lg:col-span-7">
              <div className="bg-[#0b0f19] border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col h-[380px]">
                {/* Header */}
                <div className="bg-[#070b13] px-4 py-3 flex items-center justify-between border-b border-slate-900">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded-full bg-rose-500/80"></span>
                    <span className="w-3 h-3 rounded-full bg-amber-500/80"></span>
                    <span className="w-3 h-3 rounded-full bg-emerald-500/80"></span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-500">akshat@workspace:~</span>
                  <div className="w-12"></div>
                </div>
                
                {/* Simulated Logs */}
                <div className="flex-1 p-5 font-mono text-xs leading-relaxed overflow-y-auto text-slate-400 bg-[#040810]/50 space-y-1.5 select-none">
                  <div className="text-blue-400 font-semibold">akshat@local:~ $ akshat run --continuous</div>
                  <div className="text-cyan-500">[SYSTEM] Initializing AKSHAT Software Engineer Daemon...</div>
                  <div className="text-cyan-500">[SYSTEM] Loading Gemini 3.5 Flash Reasoning Engine...</div>
                  <div className="text-slate-500">[MONITOR] File watcher active on directory: C:/Users/workspace</div>
                  <div className="text-slate-400">[MONITOR] Detected 3 modified files in branch "feat-ui-redesign"</div>
                  <div className="text-slate-300">[PLANNER] Flow: [Build Front] → [Run Tests] → [Commit & Push]</div>
                  <div className="text-emerald-400">[DEVELOPER] Running build & unit-tests locally...</div>
                  <div className="text-emerald-400">[TESTER] 6 tests executed. Results: 100% SUCCESS.</div>
                  <div className="text-indigo-400">[INTEGRATOR] Auto-commited "fix: solve scroll issues on UI container"</div>
                  <div className="text-indigo-400">[INTEGRATOR] Successfully pushed changes to GitHub origin/master.</div>
                  <div className="text-cyan-500">[SYSTEM] Task completed. Entering background watch mode...</div>
                  <div className="text-slate-600 animate-pulse font-bold">akshat@local:~ $ monitoring workspace... █</div>
                </div>
              </div>
            </div>
          </section>

          {/* Features Grid */}
          <section id="features" className="py-12 border-t border-slate-800/80">
            <div className="text-center mb-16">
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">Core Features</h2>
              <p className="text-slate-400 text-sm max-w-xl mx-auto">Fully local engineering daemon built with complete security and autonomy.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-900/40 border border-slate-800/60 rounded-xl p-6 hover:border-blue-500/30 transition-all duration-300 hover:-translate-y-1">
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center mb-4">
                  <Shield className="text-blue-400" size={20} />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Local-First Security</h3>
                <p className="text-slate-400 text-xs leading-relaxed">
                  Your code base, API keys, credentials, and databases remain strictly on your machine. Zero code telemetry or secret uploading to external servers.
                </p>
              </div>

              <div className="bg-slate-900/40 border border-slate-800/60 rounded-xl p-6 hover:border-violet-500/30 transition-all duration-300 hover:-translate-y-1">
                <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center mb-4">
                  <RefreshCw className="text-violet-400" size={20} />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Continuous Repository Monitor</h3>
                <p className="text-slate-400 text-xs leading-relaxed">
                  A local daemon watches repository edits, summarizes developments, runs test suites, builds production assets, and synchronizes status updates.
                </p>
              </div>

              <div className="bg-slate-900/40 border border-slate-800/60 rounded-xl p-6 hover:border-emerald-500/30 transition-all duration-300 hover:-translate-y-1">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-4">
                  <Chrome className="text-emerald-400" size={20} />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Platform Profile Syncer</h3>
                <p className="text-slate-400 text-xs leading-relaxed">
                  Utilizes local cookie storage and Playwright automation to securely synchronize engineering status logs to your professional LinkedIn updates.
                </p>
              </div>
            </div>
          </section>

          {/* Simple Footer */}
          <footer className="mt-20 pt-8 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
            <p>© 2026 AKSHAT Agent. Released under the MIT License.</p>
            <a 
              href="https://github.com/akshat2685/AKSHAT_software_engineer" 
              target="_blank" 
              rel="noopener noreferrer"
              className="hover:text-white transition-colors flex items-center gap-1.5"
            >
              GitHub Repository <ExternalLink size={12} />
            </a>
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
