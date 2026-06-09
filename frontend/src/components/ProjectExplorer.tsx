import React from 'react';
import { FolderOpen, FileCode, ShieldCheck } from 'lucide-react';
import { useStore } from '../stores/projectStore';

export const ProjectExplorer: React.FC = () => {
  const { systemState } = useStore();

  return (
    <div className="liquid-glass p-5 min-h-[300px]">
      <div className="text-xs tracking-wider uppercase text-gray-400 font-display mb-3 flex items-center gap-1.5 border-b border-line pb-2">
        <FolderOpen size={14} className="text-green" />
        <span>Workspace File Explorer</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg bg-slate-900/40 border border-line p-3 max-h-[160px] overflow-y-auto">
          <div className="text-xs font-semibold text-white mb-2 flex items-center gap-1.5">
            <FileCode size={13} className="text-cyan" />
            <span>Generated Project Files</span>
          </div>
          {systemState?.created_files && systemState.created_files.length > 0 ? (
            <ul className="text-xs font-mono text-gray-400 flex flex-col gap-1.5">
              {systemState.created_files.map((file, i) => (
                <li key={i} className="truncate hover:text-white transition-colors cursor-default">
                  {file}
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-xs text-gray-500 font-mono italic">No workspace files created yet.</div>
          )}
        </div>

        <div className="rounded-lg bg-slate-900/40 border border-line p-3 max-h-[160px] overflow-y-auto">
          <div className="text-xs font-semibold text-white mb-2 flex items-center gap-1.5">
            <ShieldCheck size={13} className="text-green" />
            <span>Agent Action Log Vitals</span>
          </div>
          {systemState?.active_tools && systemState.active_tools.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {systemState.active_tools.map((tool, i) => (
                <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950/80 border border-line/50 text-gray-300">
                  {tool}
                </span>
              ))}
            </div>
          ) : (
            <div className="text-xs text-gray-500 font-mono italic">No active tools logged.</div>
          )}
        </div>
      </div>
    </div>
  );
};
