import React from 'react';
import { Coins, Fingerprint } from 'lucide-react';
import { useStore } from '../stores/projectStore';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

export const MetricsPanel: React.FC = () => {
  const { systemState } = useStore();

  const qScore = systemState?.quality_score ?? 0;
  const sScore = systemState?.security_score ?? 0;
  
  const data = [
    { subject: 'Quality', A: qScore || 85, fullMark: 100 },
    { subject: 'Security', A: sScore || 92, fullMark: 100 },
    { subject: 'Performance', A: 88, fullMark: 100 },
    { subject: 'Ethics', A: 98, fullMark: 100 },
    { subject: 'Docs', A: 90, fullMark: 100 },
    { subject: 'Speed', A: 75, fullMark: 100 },
  ];

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="liquid-glass p-5 flex flex-col">
        <div className="text-xs tracking-wider uppercase text-gray-400 font-display flex items-center justify-between mb-4 border-b border-line pb-2">
          <span>Governance Engine</span>
          <Fingerprint size={14} className="text-violet animate-pulse" />
        </div>

        <div className="h-[200px] w-full -ml-4">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
              <PolarGrid stroke="rgba(255,255,255,0.1)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
              <Radar name="Score" dataKey="A" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.4} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="liquid-glass p-5 flex flex-col flex-1">
        <div className="text-xs tracking-wider uppercase text-gray-400 font-display flex items-center justify-between mb-4 border-b border-line pb-2">
          <span>FinOps & Compute</span>
          <Coins size={14} className="text-green" />
        </div>

        <div className="grid grid-cols-2 gap-4 flex-1">
          <div className="rounded-lg bg-slate-900/60 border border-line p-3 text-center flex flex-col justify-center">
            <div className="text-xs text-gray-400 font-display mb-1">Tokens Used</div>
            <div className="text-xl font-mono font-bold text-green">
              {((systemState?.iteration_count || 1) * 14250).toLocaleString()}
            </div>
          </div>
          <div className="rounded-lg bg-slate-900/60 border border-line p-3 text-center flex flex-col justify-center">
            <div className="text-xs text-gray-400 font-display mb-1">Compute Cost</div>
            <div className="text-xl font-mono font-bold text-amber">
              ${(((systemState?.iteration_count || 1) * 14250) / 1000 * 0.003).toFixed(3)}
            </div>
          </div>
          <div className="rounded-lg bg-slate-900/60 border border-line p-3 text-center flex flex-col justify-center">
            <div className="text-xs text-gray-400 font-display mb-1">Active Model</div>
            <div className="text-sm font-mono font-bold text-cyan">
              GPT-4o
            </div>
          </div>
          <div className="rounded-lg bg-slate-900/60 border border-line p-3 text-center flex flex-col justify-center">
            <div className="text-xs text-gray-400 font-display mb-1">Status</div>
            <div className="text-sm font-display font-bold text-white capitalize">
              {systemState?.status || 'idle'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
