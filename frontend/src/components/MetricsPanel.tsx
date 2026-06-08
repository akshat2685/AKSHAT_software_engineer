import React from 'react';
import { Activity } from 'lucide-react';
import { useStore } from '../stores/projectStore';

export const MetricsPanel: React.FC = () => {
  const { systemState } = useStore();

  const statusStr = systemState?.status || 'idle';

  return (
    <div className="glass-panel p-5 flex flex-col gap-4">
      <div className="text-xs tracking-wider uppercase text-gray-400 font-display flex items-center justify-between">
        <span>System Vitals</span>
        <Activity size={14} className="text-cyan animate-pulse" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-lg bg-slate-900/60 border border-line p-3 text-center">
          <div className="text-xs text-gray-400 font-display">Quality</div>
          <div className="text-2xl font-display font-bold text-white mt-1">
            {systemState?.quality_score ?? 0}%
          </div>
        </div>
        <div className="rounded-lg bg-slate-900/60 border border-line p-3 text-center">
          <div className="text-xs text-gray-400 font-display">Security</div>
          <div className="text-2xl font-display font-bold text-white mt-1">
            {systemState?.security_score ?? 0}%
          </div>
        </div>
        <div className="rounded-lg bg-slate-900/60 border border-line p-3 text-center">
          <div className="text-xs text-gray-400 font-display">Iterations</div>
          <div className="text-2xl font-display font-bold text-white mt-1">
            {systemState?.iteration_count ?? 0}
          </div>
        </div>
        <div className="rounded-lg bg-slate-900/60 border border-line p-3 text-center">
          <div className="text-xs text-gray-400 font-display">Status</div>
          <div className="text-sm font-display font-bold text-white mt-2 capitalize">
            {statusStr}
          </div>
        </div>
      </div>
    </div>
  );
};
