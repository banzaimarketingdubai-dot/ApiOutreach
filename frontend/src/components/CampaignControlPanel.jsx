import React, { useState, useEffect } from 'react';
import { getCampaignStatus, retryFailed } from '../services/api';
import { Play, Pause, Square, Activity, Database, Settings, X, ChevronRight, Target, RefreshCw } from 'lucide-react';
import EditCampaignModal from './EditCampaignModal';
import LeadScoreSettingsModal from './LeadScoreSettingsModal';

export default function CampaignControlPanel({ campaignId, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [scoreModalOpen, setScoreModalOpen] = useState(false);

  useEffect(() => {
    if (!campaignId) return;
    
    const fetchStatus = async () => {
      try {
        const res = await getCampaignStatus(campaignId);
        setData(res);
      } catch (err) {
        console.error("Failed to fetch campaign status", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, [campaignId]);

  if (loading || !data) {
    return (
      <div className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 flex items-center justify-center h-full min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const { status, stats, logs } = data;

  const getStatusColor = (s) => {
    switch(s) {
      case 'RUNNING': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      case 'PAUSED': return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'COMPLETED': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'FAILED': return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-700 rounded-3xl flex flex-col h-full min-h-[500px] overflow-hidden shadow-2xl relative">
      
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
        <div className="flex items-center space-x-3">
          <Activity className="w-5 h-5 text-blue-400" />
          <h3 className="font-bold text-white">Live Execution Center</h3>
          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${getStatusColor(status)} ${status === 'RUNNING' ? 'animate-pulse' : ''}`}>
            {status}
          </span>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-full transition-colors">
          <X className="w-5 h-5 text-slate-400" />
        </button>
      </div>

      {/* Visual Pipeline */}
      <div className="px-6 py-5 border-b border-slate-800/60 bg-slate-900/50">
        <div className="flex items-center justify-between relative">
          <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-800 -z-10 -translate-y-1/2"></div>
          
          {['Scrape', 'Resolution', 'Enrich', 'AI Extract', 'Scoring'].map((step, idx) => (
            <div key={step} className="flex flex-col items-center bg-slate-900 px-2 z-10">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 
                ${status === 'RUNNING' && idx === 0 ? 'border-blue-500 bg-blue-500/20 text-blue-400' : 'border-slate-700 bg-slate-800 text-slate-500'}
              `}>
                <Database className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-semibold text-slate-400 mt-2">{step}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Stats Counters */}
      <div className="grid grid-cols-4 divide-x divide-slate-800 border-b border-slate-800/60 bg-slate-950/30">
        <div className="p-4 text-center">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Found</div>
          <div className="text-2xl font-bold text-white">{stats.total_scraped || 0}</div>
        </div>
        <div className="p-4 text-center">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Enriched</div>
          <div className="text-2xl font-bold text-blue-400">{stats.new_leads_created || 0}</div>
        </div>
        <div className="p-4 text-center">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Merged</div>
          <div className="text-2xl font-bold text-purple-400">{stats.merged_leads || 0}</div>
        </div>
        <div className="p-4 text-center">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Errors</div>
          <div className="text-2xl font-bold text-rose-400">{stats.errors || 0}</div>
        </div>
      </div>

      {/* Live Terminal Log */}
      <div className="flex-1 bg-black p-4 overflow-y-auto font-mono text-[11px] leading-relaxed">
        {logs.length === 0 ? (
          <div className="text-slate-600 italic">Waiting for pipeline events...</div>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="mb-1 flex space-x-2">
              <span className="text-slate-600">[{log.timestamp || new Date().toISOString().split('T')[1].slice(0,8)}]</span>
              <span className={`
                ${log.level === 'error' ? 'text-rose-400' : log.level === 'warning' ? 'text-amber-400' : 'text-emerald-400'}
              `}>[{log.level?.toUpperCase() || 'INFO'}]</span>
              <span className="text-slate-300">{log.message}</span>
            </div>
          ))
        )}
      </div>

      {/* Action Bar */}
      <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/50 flex justify-between items-center">
        <div className="flex space-x-2">
           <button 
             onClick={() => setEditModalOpen(true)}
             className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-all"
           >
             <Settings className="w-3 h-3" /> <span>Edit</span>
           </button>
           <button 
             onClick={() => setScoreModalOpen(true)}
             className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-all"
           >
             <Target className="w-3 h-3 text-purple-400" /> <span>Score Settings</span>
           </button>
           <button 
             onClick={async () => {
               try {
                 await retryFailed(campaignId);
                 alert('Retry job sent to Celery successfully!');
               } catch(e) {
                 alert(e.message);
               }
             }}
             className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-all"
           >
             <RefreshCw className="w-3 h-3 text-blue-400" /> <span>Retry Failed Enrichment</span>
           </button>
        </div>
        <div className="flex space-x-2">
           {status === 'RUNNING' && (
             <button 
               onClick={async () => { await import('../services/api').then(m => m.pauseCampaign(campaignId)); setData({...data, status: 'PAUSED'}) }}
               className="px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/30 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-all"
             >
               <Pause className="w-3 h-3" /> <span>Pause</span>
             </button>
           )}
           {status === 'PAUSED' && (
             <button 
               onClick={async () => { await import('../services/api').then(m => m.resumeCampaign(campaignId)); setData({...data, status: 'RUNNING'}) }}
               className="px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 border border-blue-500/30 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-all"
             >
               <Play className="w-3 h-3" /> <span>Resume</span>
             </button>
           )}
           {['RUNNING', 'PAUSED', 'PENDING'].includes(status) && (
             <button 
               onClick={async () => { await import('../services/api').then(m => m.stopCampaign(campaignId)); setData({...data, status: 'CANCELLED'}) }}
               className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-all"
             >
               <Square className="w-3 h-3" /> <span>Stop</span>
             </button>
           )}
        </div>
      </div>

      {editModalOpen && (
        <EditCampaignModal 
          campaignId={campaignId}
          initialData={data}
          onClose={() => setEditModalOpen(false)}
        />
      )}

      {scoreModalOpen && (
        <LeadScoreSettingsModal 
          campaignId={campaignId}
          initialRules={data?.ai_config?.scoring_rules}
          onClose={() => setScoreModalOpen(false)}
        />
      )}
    </div>
  );
}
