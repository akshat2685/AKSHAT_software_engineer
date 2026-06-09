import React, { useEffect, useState, useRef } from 'react';
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
  Settings
} from 'lucide-react';

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

  // Auth local state
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authRememberMe, setAuthRememberMe] = useState(false);

  const bgCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // Connection status & details
  useEffect(() => {
    if (!isAuthenticated()) return;
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
  }, [token]);

  // Neural network background effect
  useEffect(() => {
    if (!bgCanvasRef.current) return;
    const canvas = bgCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let particles: Array<{ x: number; y: number; vx: number; vy: number; r: number }> = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      const count = Math.max(30, Math.min(80, Math.floor((canvas.width * canvas.height) / 25000)));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: 1 + Math.random() * 1.5,
      }));
    };

    resize();
    window.addEventListener('resize', resize);

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Connect nodes
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          if (dist < 150) {
            ctx.globalAlpha = (1 - dist / 150) * 0.15;
            ctx.strokeStyle = theme === 'violet' ? '#a78bfa' : theme === 'emerald' ? '#4cf2a1' : '#38d5ff';
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      ctx.globalAlpha = 0.5;
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        ctx.fillStyle = theme === 'violet' ? '#a78bfa' : theme === 'emerald' ? '#4cf2a1' : '#38d5ff';
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, [theme]);

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

  const activeAgent = systemState?.current_agent || 'Ready';

  // Render Login/Register View
  if (!isAuthenticated()) {
    return (
      <div className="relative min-h-screen text-gray-200 flex flex-col items-center justify-center p-4">
        <canvas ref={bgCanvasRef} className="fixed inset-0 pointer-events-none z-[-2]" />
        
        {/* Auth Box */}
        <div className="w-full max-w-md glass-panel p-8 shadow-2xl relative border border-line bg-slate-950/80 backdrop-blur-xl rounded-2xl">
          <div className="text-center mb-8">
            <div className="w-12 h-12 rounded-xl mx-auto flex items-center justify-center font-bold text-slate-950 bg-gradient-to-br from-cyan to-green mb-3 text-lg">
              AK
            </div>
            <h2 className="text-2xl font-display font-extrabold text-white">
              {authMode === 'login' ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="text-xs text-gray-400 mt-1 font-semibold">
              {authMode === 'login' 
                ? 'Sign in to access your autonomous engineering dashboard'
                : 'Get started with local-first software agents platform'
              }
            </p>
          </div>

          <form onSubmit={handleAuth} className="flex flex-col gap-4">
            {authError && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-3 text-xs font-semibold">
                {authError}
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Email</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"><Mail size={16} /></span>
                <input 
                  type="email" 
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  placeholder="dev@example.com"
                  className="w-full bg-slate-900 border border-line focus:border-cyan/50 focus:ring-1 focus:ring-cyan/20 outline-none rounded-lg pl-10 pr-4 py-2.5 text-sm text-white font-mono"
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Password</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"><Lock size={16} /></span>
                <input 
                  type="password" 
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-900 border border-line focus:border-cyan/50 focus:ring-1 focus:ring-cyan/20 outline-none rounded-lg pl-10 pr-4 py-2.5 text-sm text-white font-mono"
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
                className="w-4 h-4 rounded border-line bg-slate-900 text-cyan focus:ring-cyan/50"
              />
              <label htmlFor="rememberMe" className="text-xs text-gray-400 cursor-pointer">
                Remember me
              </label>
            </div>

            <button
              type="submit"
              disabled={authLoading}
              className="w-full mt-2 bg-gradient-to-br from-cyan to-green hover:brightness-105 active:scale-98 disabled:opacity-50 text-slate-950 font-bold py-2.5 rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-cyan/15 transition-all cursor-pointer text-sm"
            >
              {authMode === 'login' ? 'Login' : 'Sign Up'}
            </button>
          </form>

          <div className="mt-6 text-center border-t border-line/50 pt-5">
            <button
              onClick={() => {
                setAuthMode(authMode === 'login' ? 'register' : 'login');
                setAuthError('');
              }}
              className="text-xs text-cyan font-bold hover:underline bg-transparent border-0 cursor-pointer"
            >
              {authMode === 'login' 
                ? 'New to AKSHAT? Create an account'
                : 'Already have an account? Sign in'
              }
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render Dashboard/Timeline View
  return (
    <div className={`relative min-h-screen text-gray-200 ${density === 'compact' ? 'text-sm' : 'text-base'}`}>
      <canvas ref={bgCanvasRef} className="fixed inset-0 pointer-events-none z-[-2]" />
      
      {/* Top Navbar */}
      <nav className="fixed left-1/2 -translate-x-1/2 top-4 w-[calc(100%-32px)] max-w-7xl h-16 z-50 flex items-center justify-between px-6 border border-line rounded-lg bg-slate-950/80 shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-md flex items-center justify-center font-bold text-slate-950 bg-gradient-to-br from-cyan to-green">
              AK
            </div>
            <div className="font-display font-semibold tracking-wider hidden sm:block">
              AKSHAT <span className="text-[9px] text-gray-400 font-mono block tracking-widest leading-none">LOCAL OS v2</span>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center gap-2 pl-4 border-l border-line">
            <button
              onClick={() => setCurrentPage('dashboard')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer ${
                currentPage === 'dashboard' ? 'bg-cyan/15 text-cyan' : 'text-gray-400 hover:text-white'
              }`}
            >
              <LayoutDashboard size={14} />
              <span>Dashboard</span>
            </button>

            <button
              onClick={() => setCurrentPage('projects')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer ${
                currentPage === 'projects' ? 'bg-cyan/15 text-cyan' : 'text-gray-400 hover:text-white'
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
                currentPage === 'timeline' ? 'bg-cyan/15 text-cyan' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Layers size={14} />
              <span>Timeline</span>
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Settings / Controls */}
          <div className="hidden md:flex items-center gap-3">
            <select 
              value={theme}
              onChange={(e) => setTheme(e.target.value as any)}
              className="bg-slate-900 border border-line text-[11px] font-bold rounded px-2.5 py-1 outline-none text-gray-300 cursor-pointer"
            >
              <option value="cyan">Cyan</option>
              <option value="violet">Violet</option>
              <option value="emerald">Emerald</option>
            </select>

            <select 
              value={density}
              onChange={(e) => setDensity(e.target.value as any)}
              className="bg-slate-900 border border-line text-[11px] font-bold rounded px-2.5 py-1 outline-none text-gray-300 cursor-pointer"
            >
              <option value="normal">Normal</option>
              <option value="compact">Compact</option>
            </select>
          </div>

          {/* Active indicator */}
          <div className="flex items-center gap-2 border border-green/30 bg-green/10 rounded-md px-3 py-1 text-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-green status-pulse shrink-0" />
            <span className="font-mono text-green-300 font-semibold">{activeAgent}</span>
          </div>

          {/* Settings Button */}
          <button
            onClick={() => setSettingsOpen(true)}
            title="Configure LLM"
            className="p-2 border border-line rounded-lg bg-slate-900/40 hover:bg-white/10 hover:border-white/30 text-gray-400 hover:text-white transition-colors cursor-pointer"
          >
            <Settings size={15} />
          </button>

          {/* Logout */}
          <button
            onClick={() => logout()}
            title={`Log out: ${email}`}
            className="p-2 border border-line rounded-lg bg-slate-900/40 hover:bg-red-500/10 hover:border-red-500/30 text-gray-400 hover:text-red-400 transition-colors cursor-pointer"
          >
            <LogOut size={15} />
          </button>
        </div>
      </nav>

      {/* Main Grid View */}
      <main className="max-w-7xl mx-auto pt-24 pb-8 px-4">
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
