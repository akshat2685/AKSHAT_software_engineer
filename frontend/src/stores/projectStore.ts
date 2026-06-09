import { create } from 'zustand';

export interface WorkflowEvent {
  agent: string;
  task: string;
  output: string;
}

export interface SystemState {
  project_id: string;
  project_name: string;
  status: string;
  avatar_state: string;
  current_agent: string;
  current_action: string;
  task_type: string;
  requirements: string[];
  architecture: string[];
  tasks: string[];
  todo_list: string[];
  steps_done: string[];
  events: WorkflowEvent[];
  quality_score: number;
  security_score: number;
  iteration_count: number;
  created_files: string[];
  deployment_url: string;
  deployment_status: string;
  final_deliverable: string;
  final_result: string;
  active_tools: string[];
  chat: Array<{ role: string; content: string }>;
}

export interface DBProject {
  id: string;
  name: string;
  status: string;
  created_at: string;
}

export interface ReplayEvent {
  id: number;
  event_type: string;
  payload: any;
  created_at: string;
}

export interface LLMConfig {
  cloud_url: string;
  cloud_model: string;
  has_key: boolean;
  masked_key: string;
}

interface StoreState {
  // Auth
  token: string | null;
  email: string | null;
  userId: number | null;
  isAuthenticated: () => boolean;
  login: (token: string, email: string, userId: number, rememberMe: boolean) => void;
  registerUser: (token: string, email: string, userId: number, rememberMe: boolean) => void;
  logout: () => void;

  // Pages
  currentPage: 'dashboard' | 'projects' | 'timeline';
  setCurrentPage: (page: 'dashboard' | 'projects' | 'timeline') => void;

  // Projects
  projects: DBProject[];
  activeProjectEvents: ReplayEvent[];
  selectedProject: DBProject | null;
  fetchProjects: () => Promise<void>;
  fetchReplayEvents: (projectId: string) => Promise<void>;
  setSelectedProject: (project: DBProject | null) => void;

  // Real-time Active system state
  systemState: SystemState | null;
  theme: 'cyan' | 'violet' | 'emerald';
  density: 'normal' | 'compact';
  isConnecting: boolean;
  setSystemState: (state: SystemState | null) => void;
  setTheme: (theme: 'cyan' | 'violet' | 'emerald') => void;
  setDensity: (density: 'normal' | 'compact') => void;
  setConnecting: (isConnecting: boolean) => void;
  fetchStatus: () => Promise<void>;
  submitTask: (prompt: string, workflowPattern?: string) => Promise<void>;

  // Settings
  isSettingsOpen: boolean;
  llmConfig: LLMConfig | null;
  setSettingsOpen: (isOpen: boolean) => void;
  fetchLLMSettings: () => Promise<void>;
  saveLLMSettings: (url: string, key: string, model: string) => Promise<boolean>;
}

export const useStore = create<StoreState>((set, get) => ({
  // Auth initial state
  token: localStorage.getItem('akshat_token') || sessionStorage.getItem('akshat_token'),
  email: localStorage.getItem('akshat_email') || sessionStorage.getItem('akshat_email'),
  userId: localStorage.getItem('akshat_user_id') 
    ? Number(localStorage.getItem('akshat_user_id')) 
    : (sessionStorage.getItem('akshat_user_id') ? Number(sessionStorage.getItem('akshat_user_id')) : null),
  isAuthenticated: () => !!get().token,

  login: (token, email, userId, rememberMe) => {
    const storage = rememberMe ? localStorage : sessionStorage;
    storage.setItem('akshat_token', token);
    storage.setItem('akshat_email', email);
    storage.setItem('akshat_user_id', String(userId));
    set({ token, email, userId });
  },

  registerUser: (token, email, userId, rememberMe) => {
    const storage = rememberMe ? localStorage : sessionStorage;
    storage.setItem('akshat_token', token);
    storage.setItem('akshat_email', email);
    storage.setItem('akshat_user_id', String(userId));
    set({ token, email, userId });
  },

  logout: () => {
    localStorage.removeItem('akshat_token');
    localStorage.removeItem('akshat_email');
    localStorage.removeItem('akshat_user_id');
    sessionStorage.removeItem('akshat_token');
    sessionStorage.removeItem('akshat_email');
    sessionStorage.removeItem('akshat_user_id');
    set({ token: null, email: null, userId: null, currentPage: 'dashboard', systemState: null });
  },

  // Pages
  currentPage: 'dashboard',
  setCurrentPage: (currentPage) => set({ currentPage }),

  // Projects & Timeline
  projects: [],
  activeProjectEvents: [],
  selectedProject: null,
  setSelectedProject: (selectedProject) => set({ selectedProject }),

  fetchProjects: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch('/api/projects', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        set({ projects: data });
      }
    } catch (err) {
      console.error('Failed to fetch user projects:', err);
    }
  },

  fetchReplayEvents: async (projectId) => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch(`/api/projects/${projectId}/replay`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        set({ activeProjectEvents: data });
      }
    } catch (err) {
      console.error(`Failed to fetch replay events for project ${projectId}:`, err);
    }
  },

  // Real-time states
  systemState: null,
  theme: 'cyan',
  density: 'normal',
  isConnecting: false,

  setSystemState: (systemState) => set({ systemState }),
  setTheme: (theme) => set({ theme }),
  setDensity: (density) => set({ density }),
  setConnecting: (isConnecting) => set({ isConnecting }),

  fetchStatus: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch('/api/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const workflow = data.workflow || {};
        const systemState: SystemState = {
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
        };
        set({ systemState });
      }
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  },

  submitTask: async (prompt: string, workflowPattern?: string) => {
    const { token } = get();
    if (!token) return;
    try {
      await fetch('/api/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: prompt, workflow_pattern: workflowPattern || "Auto" }),
      });
      await get().fetchStatus();
    } catch (err) {
      console.error('Failed to submit task:', err);
    }
  },

  // Settings
  isSettingsOpen: false,
  llmConfig: null,
  
  setSettingsOpen: (isSettingsOpen) => set({ isSettingsOpen }),
  
  fetchLLMSettings: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch('/api/settings', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        set({ llmConfig: data });
      }
    } catch (err) {
      console.error('Failed to fetch settings:', err);
    }
  },

  saveLLMSettings: async (cloud_url: string, cloud_key: string, cloud_model: string) => {
    const { token } = get();
    if (!token) return false;
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ cloud_url, cloud_key, cloud_model }),
      });
      if (res.ok) {
        await get().fetchLLMSettings();
        return true;
      }
    } catch (err) {
      console.error('Failed to save settings:', err);
    }
    return false;
  },
}));
