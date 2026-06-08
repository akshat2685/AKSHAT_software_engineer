import React, { useState, useEffect } from 'react';
import { useStore } from '../stores/projectStore';
import { Play, Pause, ChevronLeft, ChevronRight, ArrowLeft, Layers, Code, CheckCircle, Eye } from 'lucide-react';

export const Timeline: React.FC = () => {
  const { selectedProject, activeProjectEvents, setCurrentPage } = useStore();
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= activeProjectEvents.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, activeProjectEvents]);

  if (!selectedProject) {
    return (
      <div className="glass-panel p-8 text-center max-w-lg mx-auto mt-12">
        <div className="text-sm text-gray-400 font-mono mb-4">No project selected for replay.</div>
        <button
          onClick={() => setCurrentPage('projects')}
          className="px-4 py-2 bg-cyan text-slate-950 rounded-lg font-bold hover:brightness-105 transition-all cursor-pointer"
        >
          Go to History
        </button>
      </div>
    );
  }

  const eventsCount = activeProjectEvents.length;
  const activeEvent = activeProjectEvents[currentStep] || null;

  return (
    <div className="w-full max-w-7xl mx-auto flex flex-col gap-6">
      {/* Top navigation */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setCurrentPage('projects')}
          className="p-2 border border-line rounded-lg bg-slate-900/40 hover:bg-slate-900/80 transition-colors text-white cursor-pointer"
        >
          <ArrowLeft size={16} />
        </button>
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            <span>Project Replay Timeline</span>
          </h1>
          <p className="text-xs text-gray-400 font-mono mt-0.5 truncate max-w-2xl">
            {selectedProject.name}
          </p>
        </div>
      </div>

      {/* Main playback control panel */}
      <div className="glass-panel p-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-line pb-5 mb-5">
          {/* Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setIsPlaying(false);
                setCurrentStep((prev) => Math.max(0, prev - 1));
              }}
              disabled={currentStep === 0}
              className="p-2.5 border border-line rounded-lg bg-slate-900/40 disabled:opacity-30 hover:bg-slate-900/80 transition-colors cursor-pointer text-white"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-5 py-2.5 bg-gradient-to-br from-cyan to-green hover:brightness-105 active:scale-98 text-slate-950 font-bold rounded-lg flex items-center gap-2 shadow-lg shadow-cyan/15 transition-all cursor-pointer"
            >
              {isPlaying ? <Pause size={15} fill="currentColor" /> : <Play size={15} fill="currentColor" />}
              <span>{isPlaying ? 'Pause' : 'Play Replay'}</span>
            </button>
            <button
              onClick={() => {
                setIsPlaying(false);
                setCurrentStep((prev) => Math.min(eventsCount - 1, prev + 1));
              }}
              disabled={currentStep >= eventsCount - 1}
              className="p-2.5 border border-line rounded-lg bg-slate-900/40 disabled:opacity-30 hover:bg-slate-900/80 transition-colors cursor-pointer text-white"
            >
              <ChevronRight size={16} />
            </button>
          </div>

          {/* Progress label */}
          <div className="text-xs font-mono text-gray-300 bg-slate-900/60 border border-line px-3.5 py-2 rounded-lg">
            Step <span className="text-cyan font-bold">{eventsCount > 0 ? currentStep + 1 : 0}</span> / {eventsCount}
          </div>
        </div>

        {/* Replay track timeline bar */}
        {eventsCount > 1 && (
          <div className="relative w-full h-2.5 bg-slate-950/80 border border-line rounded-full mb-6">
            <div
              className="absolute left-0 top-0 h-full bg-gradient-to-r from-cyan to-green rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / (eventsCount - 1)) * 100}%` }}
            />
            <input
              type="range"
              min={0}
              max={eventsCount - 1}
              value={currentStep}
              onChange={(e) => {
                setIsPlaying(false);
                setCurrentStep(Number(e.target.value));
              }}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
          </div>
        )}

        {/* Step Events sidebar list */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Timeline rail list */}
          <div className="lg:col-span-4 max-h-[380px] overflow-y-auto pr-2 flex flex-col gap-2 border-r border-line/40">
            {activeProjectEvents.map((event, idx) => {
              const isActive = idx === currentStep;
              return (
                <button
                  key={event.id}
                  onClick={() => {
                    setIsPlaying(false);
                    setCurrentStep(idx);
                  }}
                  className={`w-full text-left p-3 rounded-lg border text-xs font-mono flex items-center gap-2.5 transition-all cursor-pointer ${
                    isActive
                      ? 'border-cyan bg-cyan/10 text-white font-bold'
                      : 'border-line/40 bg-slate-900/20 text-gray-400 hover:bg-slate-900/40'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full shrink-0 ${
                    isActive ? 'bg-cyan animate-pulse' : 'bg-gray-600'
                  }`} />
                  <span className="truncate flex-1">{event.event_type}</span>
                  <span className="text-[10px] text-gray-500">
                    {new Date(event.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Details screen */}
          <div className="lg:col-span-8 flex flex-col gap-4">
            {activeEvent ? (
              <div className="rounded-lg bg-slate-900/20 border border-line p-5">
                <div className="flex items-center justify-between border-b border-line pb-3 mb-4">
                  <div className="flex items-center gap-2">
                    <Layers size={15} className="text-cyan" />
                    <span className="font-mono text-xs font-bold text-gray-400">Event Type:</span>
                    <h2 className="font-mono text-sm font-extrabold text-white uppercase tracking-wider">
                      {activeEvent.event_type}
                    </h2>
                  </div>
                  <span className="text-[10px] font-mono text-gray-500">
                    {new Date(activeEvent.created_at).toLocaleString()}
                  </span>
                </div>

                {/* Event payload text display */}
                <div className="flex flex-col gap-3">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-cyan uppercase block mb-1">Message</span>
                    <p className="text-sm font-semibold text-gray-200 leading-relaxed font-body">
                      {activeEvent.payload?.message || 'No action summary recorded.'}
                    </p>
                  </div>

                  {activeEvent.payload?.created_files && activeEvent.payload.created_files.length > 0 && (
                    <div className="mt-3 border border-line bg-slate-950/40 rounded-lg p-3">
                      <div className="text-xs font-semibold text-white mb-2 flex items-center gap-1.5">
                        <Code size={13} className="text-green" />
                        <span>Generated Files</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {activeEvent.payload.created_files.map((file: string, fIdx: number) => (
                          <span key={fIdx} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-line/50 text-gray-300">
                            {file}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {activeEvent.payload?.deployment_url && (
                    <div className="mt-4 border border-green/30 bg-green/5 rounded-lg p-4 flex items-start gap-3">
                      <CheckCircle className="text-green mt-0.5 shrink-0" size={18} />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold text-white">Project visual deploy available</div>
                        <div className="text-xs text-gray-400 mt-1 truncate font-mono">
                          {activeEvent.payload.deployment_url}
                        </div>
                        <a
                          href={activeEvent.payload.deployment_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-xs text-green font-semibold mt-2 hover:underline"
                        >
                          <span>Open Visual Deploy</span>
                          <Eye size={12} />
                        </a>
                      </div>
                    </div>
                  )}

                  {activeEvent.payload?.events && activeEvent.payload.events.length > 0 && (
                    <div className="mt-3">
                      <span className="text-[10px] font-mono font-bold text-violet uppercase block mb-1">Agent Action Trace Logs</span>
                      <div className="flex flex-col gap-2 max-h-48 overflow-y-auto">
                        {activeEvent.payload.events.map((ev: any, idx: number) => (
                          <div key={idx} className="bg-slate-950/60 border border-line rounded p-2.5">
                            <div className="flex justify-between items-center text-[11px] font-mono font-bold text-white">
                              <span>{ev.agent}</span>
                              <span className="text-[9px] uppercase tracking-wider text-cyan">{ev.task}</span>
                            </div>
                            {ev.output && (
                              <pre className="text-[10px] text-gray-400 mt-1 rounded bg-slate-900/50 p-1.5 font-mono overflow-x-auto whitespace-pre-wrap leading-normal">
                                {ev.output}
                              </pre>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-xs text-gray-500 font-mono italic text-center py-12">
                Select an event to view trace logs.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
