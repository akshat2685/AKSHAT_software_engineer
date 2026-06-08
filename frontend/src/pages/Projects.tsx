import React, { useEffect, useState } from 'react';
import { useStore } from '../stores/projectStore';
import { RefreshCw, Search, Calendar, Play } from 'lucide-react';

export const Projects: React.FC = () => {
  const { projects, fetchProjects, setSelectedProject, fetchReplayEvents, setCurrentPage } = useStore();
  const [filter, setFilter] = useState('');

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleInspect = async (project: any) => {
    setSelectedProject(project);
    await fetchReplayEvents(project.id);
    setCurrentPage('timeline');
  };

  const filteredProjects = projects.filter(p => 
    p.name.toLowerCase().includes(filter.toLowerCase()) ||
    p.id.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="glass-panel p-6 w-full max-w-7xl mx-auto">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-line pb-6 mb-6">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">Project History</h1>
          <p className="text-sm text-gray-400 mt-1">
            Browse and replay all autonomous runs registered to your account.
          </p>
        </div>
        <button
          onClick={() => fetchProjects()}
          className="flex items-center justify-center gap-2 px-4 py-2 border border-line rounded-lg text-sm bg-slate-900/40 hover:bg-slate-900/80 transition-colors text-white cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw size={15} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter and search bar */}
      <div className="relative mb-6">
        <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
          <Search size={16} />
        </span>
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Search projects by prompt text or run ID..."
          className="w-full bg-slate-950/60 border border-line focus:border-cyan/50 focus:ring-1 focus:ring-cyan/20 outline-none rounded-lg pl-10 pr-4 py-2.5 text-sm text-white font-mono"
        />
      </div>

      {/* Projects list */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => {
            const isCompleted = project.status === 'success' || project.status === 'completed';
            const isError = project.status === 'error' || project.status === 'failed';
            return (
              <div 
                key={project.id}
                className="rounded-xl border border-line bg-slate-950/40 hover:border-cyan/30 hover:bg-slate-950/70 transition-all p-5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <span className="text-[10px] font-mono text-gray-500 bg-slate-900 px-2 py-0.5 rounded border border-line max-w-[150px] truncate">
                      {project.id}
                    </span>
                    <span className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded font-bold ${
                      isCompleted 
                        ? 'bg-green/10 text-green border border-green/30' 
                        : isError 
                          ? 'bg-red-500/10 text-red-400 border border-red-500/30' 
                          : 'bg-amber/10 text-amber border border-amber/30'
                    }`}>
                      {project.status}
                    </span>
                  </div>

                  <h3 className="text-white font-semibold text-sm line-clamp-3 mb-4 leading-relaxed font-body">
                    {project.name}
                  </h3>
                </div>

                <div className="border-t border-line/40 pt-4 mt-2 flex items-center justify-between text-xs text-gray-400">
                  <div className="flex items-center gap-1.5 font-mono">
                    <Calendar size={13} />
                    <span>{new Date(project.created_at).toLocaleDateString()}</span>
                  </div>
                  <button
                    onClick={() => handleInspect(project)}
                    className="flex items-center gap-1 font-bold text-cyan hover:underline cursor-pointer bg-transparent border-0 p-0"
                  >
                    <span>Inspect Replay</span>
                    <Play size={10} fill="currentColor" className="ml-0.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12 rounded-xl border border-dashed border-line bg-slate-950/20">
          <div className="text-gray-500 text-sm font-mono italic">
            {filter ? 'No projects found matching that query.' : 'No projects launched yet. Submit a task on the dashboard.'}
          </div>
        </div>
      )}
    </div>
  );
};
