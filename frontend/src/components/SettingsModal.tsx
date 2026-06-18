import React, { useEffect, useState } from 'react';
import { useStore } from '../stores/projectStore';
import { X, Zap, Key, Globe, Cpu } from 'lucide-react';

export const SettingsModal: React.FC = () => {
  const isSettingsOpen = useStore(state => state.isSettingsOpen);
  const setSettingsOpen = useStore(state => state.setSettingsOpen);
  const llmConfig = useStore(state => state.llmConfig);
  const fetchLLMSettings = useStore(state => state.fetchLLMSettings);
  const saveLLMSettings = useStore(state => state.saveLLMSettings);

  const [activeTab, setActiveTab] = useState<'gemini' | 'cloud'>('gemini');
  const [geminiKey, setGeminiKey] = useState('');
  const [geminiModel, setGeminiModel] = useState('gemini-1.5-flash');
  const [url, setUrl] = useState('');
  const [key, setKey] = useState('');
  const [model, setModel] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (isSettingsOpen) fetchLLMSettings();
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
    if (activeTab === 'gemini') {
      // Save via the /api/settings endpoint with a special Gemini URL pattern
      await saveLLMSettings(
        'gemini://' + geminiModel,
        geminiKey,
        geminiModel
      );
    } else {
      await saveLLMSettings(url, key, model);
    }
    setSaving(false);
    setSaved(true);
    setTimeout(() => { setSaved(false); setSettingsOpen(false); }, 1200);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-[#0f1629] border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-white/8 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-2">
            <Cpu size={18} className="text-cyan" />
            <h2 className="text-lg font-bold text-white tracking-wide">LLM Configuration</h2>
          </div>
          <button 
            onClick={() => setSettingsOpen(false)}
            className="p-1.5 rounded-lg text-white/50 hover:bg-white/5 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-white/8 bg-slate-950/40">
          <button
            onClick={() => setActiveTab('gemini')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-semibold transition-all ${
              activeTab === 'gemini'
                ? 'text-cyan border-b-2 border-cyan bg-cyan/5'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Zap size={14} />
            Google Gemini
            <span className="text-[10px] font-bold bg-cyan/20 text-cyan px-1.5 py-0.5 rounded-full">Recommended</span>
          </button>
          <button
            onClick={() => setActiveTab('cloud')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-semibold transition-all ${
              activeTab === 'cloud'
                ? 'text-violet border-b-2 border-violet bg-violet/5'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Globe size={14} />
            Custom Cloud API
          </button>
        </div>

        <div className="p-6 space-y-5">
          {activeTab === 'gemini' ? (
            <>
              <div className="p-3 bg-cyan/5 border border-cyan/20 rounded-xl text-xs text-cyan/80 leading-relaxed">
                <strong className="text-cyan">Powers all 8 AKSHAT agents.</strong> Get a free API key from{' '}
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-white"
                >
                  Google AI Studio
                </a>{' '}
                — no billing required for Gemini 1.5 Flash.
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-white/70 flex items-center gap-1.5">
                  <Key size={13} /> Gemini API Key
                </label>
                <input
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="AIza..."
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white/90 placeholder-white/30 focus:outline-none focus:border-cyan/50 transition-colors font-mono text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-white/70">Model</label>
                <select
                  value={geminiModel}
                  onChange={(e) => setGeminiModel(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white/90 focus:outline-none focus:border-cyan/50 transition-colors text-sm"
                >
                  <option value="gemini-1.5-flash">gemini-1.5-flash (Recommended — fast &amp; free)</option>
                  <option value="gemini-1.5-pro">gemini-1.5-pro (Smarter, slower)</option>
                  <option value="gemini-2.0-flash">gemini-2.0-flash (Latest)</option>
                  <option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite (Fastest)</option>
                </select>
              </div>
            </>
          ) : (
            <>
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-white/70 block">Cloud Provider URL</label>
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://api.openai.com/v1/chat/completions"
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white/90 placeholder-white/30 focus:outline-none focus:border-violet/50 transition-colors text-sm"
                />
                <p className="text-xs text-white/40">OpenAI-compatible endpoint (Groq, OpenRouter, etc.)</p>
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-white/70 block">API Key</label>
                <input
                  type="password"
                  value={key}
                  onChange={(e) => setKey(e.target.value)}
                  placeholder="sk-... or gsk_..."
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white/90 placeholder-white/30 focus:outline-none focus:border-violet/50 transition-colors font-mono text-sm"
                />
                {llmConfig?.has_key && <p className="text-xs text-green font-semibold">An API key is currently configured.</p>}
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-white/70 block">Model Name</label>
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="gpt-4o / llama-3.3-70b-versatile"
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white/90 placeholder-white/30 focus:outline-none focus:border-violet/50 transition-colors font-mono text-sm"
                />
              </div>
            </>
          )}
        </div>

        <div className="p-5 border-t border-white/8 bg-white/[0.02] flex justify-end gap-3">
          <button
            onClick={() => setSettingsOpen(false)}
            className="px-5 py-2 rounded-xl text-sm font-semibold text-white/60 hover:text-white hover:bg-white/5 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className={`px-6 py-2 rounded-xl text-sm font-bold transition-all active:scale-95 disabled:opacity-50 shadow-lg ${
              activeTab === 'gemini'
                ? 'bg-gradient-to-r from-cyan/80 to-blue-500/80 hover:from-cyan hover:to-blue-500 shadow-cyan/20 text-slate-950'
                : 'bg-gradient-to-r from-violet/80 to-purple-600/80 hover:from-violet hover:to-purple-600 shadow-violet/20 text-white'
            }`}
          >
            {saving ? 'Saving...' : saved ? 'Saved!' : 'Save & Apply'}
          </button>
        </div>
      </div>
    </div>
  );
};
