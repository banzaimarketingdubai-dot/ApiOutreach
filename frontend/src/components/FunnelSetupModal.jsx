import React, { useState } from 'react';
import { Play, Send, Zap, Ghost, Anchor, AlertCircle, Search, Mail, Loader2 } from 'lucide-react';
import { startFunnel } from '../services/api';

export default function FunnelSetupModal({ isOpen, onClose, selectedCount, selectedLeadIds, onSuccess }) {
  const [funnelType, setFunnelType] = useState('HIDDEN_GEMS');
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const funnels = [
    {
      id: 'HIDDEN_GEMS',
      name: 'Hidden Gems',
      icon: <Zap className="w-5 h-5 text-amber-400" />,
      desc: 'Для компаний с высоким Revo Score, но плохим откликом. Теплый тон, упор на упущенную выгоду.',
      color: 'bg-amber-500/10 border-amber-500/30'
    },
    {
      id: 'SINKING_GIANTS',
      name: 'Sinking Giants',
      icon: <Anchor className="w-5 h-5 text-rose-400" />,
      desc: 'Для компаний с низким рейтингом и кучей плохих отзывов. Решаем проблему репутации.',
      color: 'bg-rose-500/10 border-rose-500/30'
    },
    {
      id: 'GHOSTS',
      name: 'The Ghosts',
      icon: <Ghost className="w-5 h-5 text-slate-400" />,
      desc: 'Для компаний без отзывов или с пустым профилем. Открываем им глаза на SEO локального поиска.',
      color: 'bg-slate-500/10 border-slate-500/30'
    }
  ];

  const handleStart = async () => {
    setIsStarting(true);
    setError(null);
    try {
      await startFunnel(selectedLeadIds, funnelType);
      onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to start funnel');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="bg-slate-900 border border-slate-700/50 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-500/20 rounded-lg">
              <Send className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Start Drip Funnel</h2>
              <p className="text-xs text-slate-400">Launch automated 5-touch email sequences.</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <AlertCircle className="w-5 h-5 rotate-45" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[70vh] flex flex-col space-y-6">
          
          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-start space-x-3">
            <Mail className="w-5 h-5 text-blue-400 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-blue-100">Ready to Launch</h3>
              <p className="text-xs text-blue-300/70 mt-1">
                You have selected <strong>{selectedCount}</strong> leads. They will be placed into the selected funnel, starting at Touch 1 immediately.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Select Funnel Type
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {funnels.map(f => (
                <div 
                  key={f.id}
                  onClick={() => setFunnelType(f.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    funnelType === f.id 
                      ? `${f.color} ring-2 ring-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.15)]` 
                      : 'bg-slate-950 border-slate-800 hover:border-slate-700 hover:bg-slate-900/50 opacity-70'
                  }`}
                >
                  <div className="mb-2">{f.icon}</div>
                  <h4 className="text-sm font-bold text-white mb-1">{f.name}</h4>
                  <p className="text-[10px] text-slate-400 leading-relaxed">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 text-center">
              {error}
            </div>
          )}

        </div>

        <div className="p-5 border-t border-slate-800 bg-slate-950 flex justify-end space-x-3">
          <button 
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleStart}
            disabled={isStarting}
            className="flex items-center space-x-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium shadow-[0_0_15px_rgba(79,70,229,0.3)] transition-all"
          >
            {isStarting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            <span>Launch {selectedCount} Leads</span>
          </button>
        </div>
      </div>
    </div>
  );
}
