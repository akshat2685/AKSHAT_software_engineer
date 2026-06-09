import React, { useEffect, useState } from 'react';
import { useStore } from '../stores/projectStore';
import { X } from 'lucide-react';

export const SettingsModal: React.FC = () => {
  const isSettingsOpen = useStore(state => state.isSettingsOpen);
  const setSettingsOpen = useStore(state => state.setSettingsOpen);
  const llmConfig = useStore(state => state.llmConfig);
  const fetchLLMSettings = useStore(state => state.fetchLLMSettings);
  const saveLLMSettings = useStore(state => state.saveLLMSettings);

  const [url, setUrl] = useState('');
  const [key, setKey] = useState('');
  const [model, setModel] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isSettingsOpen) {
      fetchLLMSettings();
    }
  }, [isSettingsOpen, fetchLLMSettings]);

  useEffect(() => {
    if (llmConfig) {
      setUrl(llmConfig.cloud_url || '');
      setKey(llmConfig.has_key ? llmConfig.masked_key : '');
      setModel(llmConfig.cloud_model || '');
    }
  }, [llmConfig]);

  if (!isSettingsOpen) return null;

  const handleSave = async () => {
    setSaving(true);
    await saveLLMSettings(url, key, model);
    setSaving(false);
    setSettingsOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-[#1C1C23] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
        <div className="p-5 border-b border-white/5 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white tracking-wide">LLM Configuration</h2>
          <button 
            onClick={() => setSettingsOpen(false)}
            className="p-1.5 rounded-lg text-white/50 hover:bg-white/5 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-5">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70 block">Cloud Provider URL</label>
            <input 
              type="text" 
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://api.openai.com/v1/chat/completions"
              className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan-500/50 transition-colors"
            />
            <p className="text-xs text-white/40">Leave empty to use default local Ollama if available.</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70 block">API Key</label>
            <input 
              type="password" 
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="sk-..."
              className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan-500/50 transition-colors font-mono"
            />
            {llmConfig?.has_key && <p className="text-xs text-emerald-400">An API key is currently configured.</p>}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70 block">Model Name</label>
            <input 
              type="text" 
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="gpt-4o / llama-3.3-70b-versatile"
              className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan-500/50 transition-colors font-mono"
            />
          </div>
        </div>

        <div className="p-5 border-t border-white/5 bg-white/[0.02] flex justify-end gap-3">
          <button 
            onClick={() => setSettingsOpen(false)}
            className="px-5 py-2 rounded-xl text-sm font-medium text-white/70 hover:text-white hover:bg-white/5 transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-cyan-500/80 to-blue-500/80 hover:from-cyan-500 hover:to-blue-500 shadow-lg shadow-cyan-500/20 transition-all active:scale-95 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
};
