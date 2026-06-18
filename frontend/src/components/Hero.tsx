import React from 'react';
import { useStore } from '../stores/projectStore';

export const Hero: React.FC = () => {
  const { systemState } = useStore();

  const status = systemState?.status || 'idle';
  const agentName = systemState?.current_agent || 'Idle';
  const projectName = systemState?.project_name || 'AKSHAT Engineering OS';
  const currentAction = systemState?.current_action || 'Waiting for your prompt...';

  const statusColors: Record<string, { bg: string; dot: string; text: string }> = {
    idle:     { bg: 'bg-slate-500/10 border-slate-500/20', dot: 'bg-slate-500', text: 'text-slate-400' },
    thinking: { bg: 'bg-amber-500/10 border-amber-500/20', dot: 'bg-amber-400 animate-pulse', text: 'text-amber-400' },
    running:  { bg: 'bg-cyan-500/10 border-cyan-500/20',   dot: 'bg-cyan-400 animate-pulse',  text: 'text-cyan-400' },
    success:  { bg: 'bg-green-500/10 border-green-500/20', dot: 'bg-green-500',  text: 'text-green-400' },
    error:    { bg: 'bg-red-500/10 border-red-500/20',     dot: 'bg-red-500',    text: 'text-red-400' },
  };

  const sc = statusColors[status] || statusColors.idle;

  return (
    <div className="w-full px-0 pb-4 pt-0">
      {/* Banner strip */}
      <div className={`flex items-center gap-4 border rounded-xl px-5 py-3 ${sc.bg}`}>
        {/* Status dot */}
        <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${sc.dot}`} />

        {/* Project info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-bold text-white font-display truncate">
              {projectName}
            </span>
            <span className={`text-xs font-mono font-bold uppercase px-2 py-0.5 rounded-full border ${sc.bg} ${sc.text}`}>
              {status}
            </span>
            {agentName && agentName !== 'Idle' && (
              <span className="text-xs text-slate-400 font-mono">
                Agent: <span className="text-white font-semibold">{agentName}</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-0.5 truncate font-body">{currentAction}</p>
        </div>

        {/* Iteration count */}
        {systemState?.iteration_count !== undefined && systemState.iteration_count > 0 && (
          <div className="shrink-0 text-right">
            <div className="text-xs text-slate-500 font-mono">Iterations</div>
            <div className="text-sm font-bold text-white font-mono">{systemState.iteration_count}</div>
          </div>
        )}
      </div>
    </div>
  );
};
