import React, { useState } from 'react';
import { Beaker, Loader2, Send, Zap, Anchor, Ghost, ChevronRight, MessageCircle } from 'lucide-react';
import { generateSandboxFunnel } from '../services/api';

export default function SandboxModal({ isOpen, onClose, lead }) {
  const [funnelType, setFunnelType] = useState('HIDDEN_GEMS');
  const [isGenerating, setIsGenerating] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen || !lead) return null;

  const funnels = [
    { id: 'HIDDEN_GEMS', name: 'Hidden Gems', icon: <Zap className="w-4 h-4 text-amber-400" /> },
    { id: 'SINKING_GIANTS', name: 'Sinking Giants', icon: <Anchor className="w-4 h-4 text-rose-400" /> },
    { id: 'GHOSTS', name: 'The Ghosts', icon: <Ghost className="w-4 h-4 text-slate-400" /> }
  ];

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setResults(null);
    try {
      const res = await generateSandboxFunnel(lead.id, funnelType);
      setResults(res.touches);
    } catch (err) {
      setError(err.message || 'Failed to generate sandbox funnel');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="bg-slate-900 border border-slate-700/50 rounded-2xl w-full max-w-4xl shadow-2xl flex flex-col overflow-hidden max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-500/20 rounded-lg border border-purple-500/30">
              <Beaker className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Funnel Sandbox Laboratory</h2>
              <p className="text-xs text-slate-400">Instantly generate all 5 touches for {lead.company_name}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors p-2">
            ✕
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-64 border-r border-slate-800 bg-slate-900/50 p-4 flex flex-col shrink-0">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Select Persona</h3>
            <div className="space-y-2 flex-1">
              {funnels.map(f => (
                <button
                  key={f.id}
                  onClick={() => setFunnelType(f.id)}
                  className={`w-full flex items-center space-x-3 p-3 rounded-xl border text-left transition-all ${
                    funnelType === f.id 
                      ? 'bg-purple-500/10 border-purple-500/30 ring-1 ring-purple-500/50 shadow-inner' 
                      : 'bg-slate-950 border-slate-800 hover:bg-slate-800'
                  }`}
                >
                  {f.icon}
                  <span className={`text-sm font-semibold ${funnelType === f.id ? 'text-white' : 'text-slate-400'}`}>
                    {f.name}
                  </span>
                </button>
              ))}
            </div>

            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full flex items-center justify-center space-x-2 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-bold transition-colors mt-4"
            >
              {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              <span>Generate 5 Touches</span>
            </button>
          </div>

          {/* Main Area */}
          <div className="flex-1 overflow-y-auto p-6 bg-slate-950/50">
            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm mb-6">
                {error}
              </div>
            )}

            {!results && !isGenerating && !error && (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
                <Beaker className="w-12 h-12 opacity-20" />
                <p>Select a persona and click Generate to see the AI magic.</p>
              </div>
            )}

            {isGenerating && (
              <div className="h-full flex flex-col items-center justify-center space-y-4 text-purple-400">
                <Loader2 className="w-10 h-10 animate-spin" />
                <p className="animate-pulse font-medium">Groq 120b is writing 5 emails...</p>
              </div>
            )}

            {results && !isGenerating && (
              <div className="space-y-8">
                {results.map((touch, idx) => (
                  <div key={idx} className="relative">
                    {/* Connection Line */}
                    {idx !== results.length - 1 && (
                      <div className="absolute left-6 top-14 bottom-[-32px] w-0.5 bg-slate-800"></div>
                    )}
                    
                    <div className="flex items-start space-x-4 relative z-10">
                      <div className="w-12 h-12 rounded-full bg-slate-900 border-2 border-purple-500/50 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
                        <span className="text-purple-400 font-bold text-lg">{touch.touch_level}</span>
                      </div>
                      
                      <div className="flex-1 bg-slate-900 border border-slate-700/50 rounded-xl overflow-hidden shadow-lg">
                        <div className="px-4 py-3 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-slate-500 font-semibold">Subject:</span>
                            <span className="text-sm font-bold text-white">{touch.subject}</span>
                          </div>
                        </div>
                        <div 
                          className="p-4 text-sm text-slate-300 prose prose-invert max-w-none prose-p:my-1 prose-a:text-blue-400"
                          dangerouslySetInnerHTML={{ __html: touch.body }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
