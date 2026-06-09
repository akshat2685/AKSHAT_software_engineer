import React from 'react';
import { useStore } from '../stores/projectStore';
import { Shield, Zap, Search, Database, PenTool, Scale, CheckSquare, Wrench, Coins, UploadCloud, BrainCircuit, Activity, Eye, Layout, Hammer } from 'lucide-react';

const AGENT_CLUSTERS = [
  {
    name: "Strategy & Design",
    color: "text-cyan",
    bg: "bg-cyan/10",
    border: "border-cyan/30",
    agents: [
      { name: "ProjectManager", icon: <Layout size={14} /> },
      { name: "Research", icon: <Search size={14} /> },
      { name: "Architect", icon: <BrainCircuit size={14} /> },
      { name: "UXFrontend", icon: <PenTool size={14} /> }
    ]
  },
  {
    name: "Engineering Core",
    color: "text-amber",
    bg: "bg-amber/10",
    border: "border-amber/30",
    agents: [
      { name: "Developer", icon: <Hammer size={14} /> },
      { name: "DataEngineer", icon: <Database size={14} /> },
      { name: "Tester", icon: <CheckSquare size={14} /> },
      { name: "Improver", icon: <Wrench size={14} /> }
    ]
  },
  {
    name: "Protectors & Governance",
    color: "text-danger",
    bg: "bg-danger/10",
    border: "border-danger/30",
    agents: [
      { name: "Security", icon: <Shield size={14} /> },
      { name: "Performance", icon: <Zap size={14} /> },
      { name: "Compliance", icon: <Scale size={14} /> },
      { name: "Reviewer", icon: <Eye size={14} /> }
    ]
  },
  {
    name: "Infrastructure & Ops",
    color: "text-green",
    bg: "bg-green/10",
    border: "border-green/30",
    agents: [
      { name: "DevOps", icon: <UploadCloud size={14} /> },
      { name: "Cost", icon: <Coins size={14} /> },
      { name: "Memory", icon: <BrainCircuit size={14} /> },
      { name: "TechnicalWriter", icon: <PenTool size={14} /> }
    ]
  }
];

export const AgentRoster: React.FC = () => {
  const { systemState } = useStore();
  const isRunning = systemState?.status === 'running' || systemState?.status === 'thinking';

  return (
    <div className="liquid-glass p-5 flex flex-col h-full">
      <div className="text-xs tracking-wider uppercase text-gray-400 font-display mb-4 flex items-center justify-between border-b border-line pb-2 shrink-0">
        <div className="flex items-center gap-1.5">
          <Activity size={14} className={isRunning ? "text-cyan animate-pulse" : "text-gray-500"} />
          <span>Swarm Status</span>
        </div>
        <div className="text-[10px] bg-white/5 px-2 py-0.5 rounded-full font-mono">17 AGENTS ONLINE</div>
      </div>
      
      <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-4">
        {AGENT_CLUSTERS.map((cluster, idx) => (
          <div key={idx}>
            <div className={`text-[10px] uppercase font-bold tracking-wider mb-2 ${cluster.color} opacity-80`}>
              {cluster.name}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {cluster.agents.map((agent, i) => {
                // Mock active state based on system status
                const isActive = isRunning && Math.random() > 0.3; // Simulate dynamic swarm
                return (
                  <div 
                    key={i} 
                    className={`flex items-center gap-2 p-2 rounded-md border text-xs font-mono transition-all duration-300 ${
                      isActive 
                        ? `${cluster.bg} ${cluster.border} ${cluster.color} shadow-[0_0_10px_rgba(255,255,255,0.05)]` 
                        : "bg-white/5 border-white/5 text-gray-500"
                    }`}
                  >
                    <div className={isActive ? "animate-pulse" : ""}>{agent.icon}</div>
                    <span className="truncate">{agent.name}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
