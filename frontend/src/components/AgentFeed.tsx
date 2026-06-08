import React, { useRef, useEffect } from 'react';
import { Terminal, Cpu } from 'lucide-react';
import { useStore } from '../stores/projectStore';

interface AgentFeedProps {
  activeTab: 'activity' | 'chat';
  setActiveTab: (tab: 'activity' | 'chat') => void;
}

export const AgentFeed: React.FC<AgentFeedProps> = ({ activeTab, setActiveTab }) => {
  const { systemState } = useStore();
  const feedContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (feedContainerRef.current) {
      feedContainerRef.current.scrollTop = feedContainerRef.current.scrollHeight;
    }
  }, [activeTab, systemState?.chat, systemState?.events]);

  const statusStr = systemState?.status || 'idle';

  return (
    <div className="glass-panel p-5 flex flex-col h-[340px]">
      <div className="text-xs tracking-wider uppercase text-gray-400 font-display mb-3 flex items-center justify-between border-b border-line pb-2 shrink-0">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('activity')}
            className={`pb-1 px-1 font-bold transition-all border-b-2 bg-transparent cursor-pointer ${
              activeTab === 'activity' ? 'border-violet text-white' : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            Agent Activity
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`pb-1 px-1 font-bold transition-all border-b-2 bg-transparent cursor-pointer ${
              activeTab === 'chat' ? 'border-cyan text-white' : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            General Chat
          </button>
        </div>
        {activeTab === 'activity' ? (
          <div className="flex items-center gap-1.5 text-violet">
            <Terminal size={14} />
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-cyan">
            <Cpu size={14} />
          </div>
        )}
      </div>
      <div ref={feedContainerRef} className="flex-1 overflow-y-auto pr-1 flex flex-col gap-3">
        {activeTab === 'chat' ? (
          systemState?.chat && systemState.chat.length > 0 ? (
            systemState.chat.map((msg, i) => (
              <div
                key={i}
                className={`max-w-[85%] rounded-lg p-3 ${
                  msg.role === 'user'
                    ? 'self-end bg-slate-900/60 border border-cyan/20 text-gray-200'
                    : 'self-start bg-slate-900/30 border border-line text-cyan'
                }`}
              >
                <div className="text-[10px] font-mono font-bold text-gray-400 uppercase mb-1">
                  {msg.role === 'user' ? 'You' : 'AKSHAT'}
                </div>
                <div className="text-xs font-semibold leading-relaxed whitespace-pre-wrap">{msg.content}</div>
              </div>
            ))
          ) : (
            <div className="text-xs text-gray-500 font-mono italic my-auto text-center">
              No conversation yet. Say hello to AKSHAT!
            </div>
          )
        ) : (
          systemState?.events && systemState.events.length > 0 ? (
            systemState.events.map((event, i) => (
              <div key={i} className="bg-slate-900/40 border border-line/50 rounded-lg p-3">
                <div className="flex justify-between items-center text-xs font-mono font-bold text-white">
                  <span>{event.agent}</span>
                  <span className="text-[10px] uppercase tracking-wider text-cyan">{statusStr}</span>
                </div>
                <div className="text-xs text-gray-300 mt-1 font-body font-semibold">{event.task}</div>
                {event.output && (
                  <div className="text-[11px] text-gray-400 mt-1 bg-slate-950/60 rounded p-1.5 font-mono max-h-20 overflow-y-auto">
                    {event.output}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-xs text-gray-500 font-mono italic my-auto text-center">
              Waiting for agent execution logs...
            </div>
          )
        )}
      </div>
    </div>
  );
};
