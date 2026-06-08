import React, { useState } from 'react';
import { Play, Cpu, CheckCircle, ExternalLink, Layers } from 'lucide-react';
import { useStore } from '../stores/projectStore';
import { AvatarPanel } from '../components/AvatarPanel';
import { MetricsPanel } from '../components/MetricsPanel';
import { AgentFeed } from '../components/AgentFeed';
import { ProjectExplorer } from '../components/ProjectExplorer';

export const Dashboard: React.FC = () => {
  const { systemState, submitTask } = useStore();
  const [prompt, setPrompt] = useState('');
  const [activeTab, setActiveTab] = useState<'activity' | 'chat'>('activity');

  const handleRun = () => {
    if (!prompt.trim()) return;
    submitTask(prompt);
    setPrompt('');
  };

  const statusStr = systemState?.status || 'idle';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Column (Avatar & System Vitals) */}
      <section className="lg:col-span-4 flex flex-col gap-6">
        <AvatarPanel />
        <MetricsPanel />
      </section>

      {/* Right Column (Workspace Console, Activity logs, Timeline, Explorer) */}
      <section className="lg:col-span-8 flex flex-col gap-6">
        {/* Project Console (Workspace Intake) */}
        <div className="glass-panel p-6">
          <div className="text-xs tracking-wider uppercase text-gray-400 font-display mb-3 flex items-center gap-2">
            <Cpu size={14} className="text-cyan" />
            <span>Autonomy Intake Workspace</span>
          </div>

          <h1 className="text-3xl lg:text-4xl font-display font-bold tracking-tight text-white mb-2">
            Plan, build, test, review.
          </h1>
          <p className="text-sm text-gray-400 mb-6 max-w-xl font-medium">
            Describe your software project prompt below. AKSHAT routes the instructions autonomously through PM, Architect, Developer, Tester, Reviewer, and Memory agents.
          </p>

          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. build a notes management app and run validation"
              onKeyDown={(e) => e.key === 'Enter' && handleRun()}
              className="flex-1 bg-slate-950/80 border border-line focus:border-cyan/50 focus:ring-1 focus:ring-cyan/20 outline-none rounded-lg px-4 py-3 text-white font-body"
            />
            <button
              onClick={handleRun}
              disabled={statusStr === 'thinking' || statusStr === 'running'}
              className="bg-gradient-to-br from-cyan to-green hover:brightness-105 active:scale-98 disabled:opacity-50 text-slate-950 font-bold px-6 py-3 rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-cyan/15 transition-all cursor-pointer"
            >
              <Play size={16} fill="currentColor" />
              <span>Run</span>
            </button>
          </div>

          {/* Final Deliverable Box */}
          {systemState?.deployment_url && (
            <div className="mt-5 border border-green/30 bg-green/5 rounded-lg p-4 flex items-start gap-3">
              <CheckCircle className="text-green mt-0.5 shrink-0" size={18} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-white">Project Published Successfully</div>
                <div className="text-xs text-gray-400 mt-1 truncate font-mono">
                  {systemState.deployment_url}
                </div>
                <a
                  href={systemState.deployment_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-green font-semibold mt-2 hover:underline"
                >
                  <span>Open Visual Deploy</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Execution Log & Tasks */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <AgentFeed activeTab={activeTab} setActiveTab={setActiveTab} />

          {/* Real-time Project Tasks */}
          <div className="glass-panel p-5 flex flex-col h-[340px]">
            <div className="text-xs tracking-wider uppercase text-gray-400 font-display mb-3 flex items-center gap-1.5 border-b border-line pb-2 shrink-0">
              <Layers size={14} className="text-amber" />
              <span>Active Project Tasks</span>
            </div>
            <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2">
              {systemState?.todo_list && systemState.todo_list.length > 0 ? (
                systemState.todo_list.map((todo, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs bg-slate-900/30 border border-line/30 rounded p-2.5">
                    <div
                      className={`w-4 h-4 rounded-full shrink-0 flex items-center justify-center font-bold font-mono text-[9px] ${
                        todo.startsWith('[x]')
                          ? 'bg-green/20 border border-green text-green'
                          : 'bg-amber/10 border border-amber/50 text-amber'
                      }`}
                    >
                      {todo.startsWith('[x]') ? '✓' : '▶'}
                    </div>
                    <span className="font-mono text-gray-300 truncate">
                      {todo.replace('[x]', '').replace('[ ]', '').trim()}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-gray-500 font-mono italic my-auto text-center">
                  Tasks not initialized. Submit a prompt to start.
                </div>
              )}
            </div>
          </div>
        </div>

        <ProjectExplorer />
      </section>
    </div>
  );
};
