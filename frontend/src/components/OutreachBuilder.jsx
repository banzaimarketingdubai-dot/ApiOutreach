import React, { useState, useEffect } from 'react';
import { Send, Target, CheckCircle, AlertCircle, Wand2, Mail } from 'lucide-react';
import { apiCall } from '../services/api';

export default function OutreachBuilder({ globalCampaignId }) {
  const [campaigns, setCampaigns] = useState([]);
  const [newCampaign, setNewCampaign] = useState({ name: '', prompt_template: '' });
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const defaultPrompt = `You have a great service, but you're losing clients to competitors. I ran a GBP analysis for you: [Link]. Here are 2 things you must fix today.
Google Maps isn't set-and-forget. It requires continuous updates to stay on top.
Click [Here] to try our AI Copilot. Or, reply to this email and I'll send you a Welcome14 promo code for 14 days of free Autopilot.`;

  useEffect(() => {
    fetchCampaigns();
    setNewCampaign(prev => ({ ...prev, prompt_template: defaultPrompt }));
  }, []);

  const fetchCampaigns = async () => {
    try {
      const data = await apiCall('/api/v1/outreach/campaigns');
      setCampaigns(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreate = async () => {
    if (!newCampaign.name) return;
    setLoading(true);
    try {
      await apiCall('/api/v1/outreach/campaigns', {
        method: 'POST',
        body: JSON.stringify({
          name: newCampaign.name,
          prompt_template: newCampaign.prompt_template,
          filters: { campaign_id: globalCampaignId }
        })
      });
      setNewCampaign({ name: '', prompt_template: defaultPrompt });
      fetchCampaigns();
      setSuccessMsg('Outreach Campaign Created!');
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Send className="w-32 h-32 text-blue-500" />
        </div>
        <div className="relative z-10 max-w-2xl">
          <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
            <Send className="w-6 h-6 text-blue-500" />
            Outreach Campaign Builder
          </h2>
          <p className="text-slate-400 text-sm">
            Configure automated 5-touch email drip campaigns to convert scraped leads into GBPilot SaaS trials.
          </p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Create New */}
        <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col h-[600px]">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Wand2 className="w-5 h-5 text-purple-500" />
            New Funnel
          </h3>
          
          <div className="space-y-4 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Campaign Name</label>
              <input
                type="text"
                value={newCampaign.name}
                onChange={e => setNewCampaign({ ...newCampaign, name: e.target.value })}
                placeholder="e.g. Hidden Gems - Kyiv"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">StoryBrand Base Prompt (Touch 1)</label>
              <textarea
                value={newCampaign.prompt_template}
                onChange={e => setNewCampaign({ ...newCampaign, prompt_template: e.target.value })}
                className="w-full h-64 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors resize-none font-mono"
              />
            </div>

            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
              <p className="text-xs text-blue-400">
                <strong>Targeting:</strong> All leads from the currently selected Global Project ({globalCampaignId || 'None selected'}).
              </p>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-slate-800">
            {successMsg && (
              <div className="mb-3 p-2 bg-emerald-500/10 border border-emerald-500/20 rounded text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4" /> {successMsg}
              </div>
            )}
            <button
              onClick={handleCreate}
              disabled={loading || !newCampaign.name}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading ? <span className="animate-pulse">Saving...</span> : <><Send className="w-4 h-4" /> Create Funnel</>}
            </button>
          </div>
        </div>

        {/* Right Column: Existing Campaigns */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col h-[600px]">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Mail className="w-5 h-5 text-indigo-500" />
            Active Funnels
          </h3>
          
          {campaigns.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 space-y-3 border-2 border-dashed border-slate-800 rounded-xl">
              <AlertCircle className="w-8 h-8 opacity-50" />
              <p className="text-sm">No outreach funnels created yet.</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
              {campaigns.map(camp => (
                <div key={camp.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 hover:border-slate-700 transition-colors group">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-slate-200">{camp.name}</h4>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      camp.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                      'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>
                      {camp.status}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <div className="bg-slate-900 rounded p-2 text-center">
                      <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Queued</div>
                      <div className="font-mono text-sm text-slate-300">0</div>
                    </div>
                    <div className="bg-slate-900 rounded p-2 text-center">
                      <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Sent</div>
                      <div className="font-mono text-sm text-blue-400">0</div>
                    </div>
                    <div className="bg-slate-900 rounded p-2 text-center">
                      <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Opened</div>
                      <div className="font-mono text-sm text-purple-400">0</div>
                    </div>
                    <div className="bg-slate-900 rounded p-2 text-center border border-emerald-500/20">
                      <div className="text-[10px] text-emerald-500/70 uppercase tracking-wider mb-1">Replied</div>
                      <div className="font-mono text-sm text-emerald-400 font-bold">0</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button className="flex-1 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 text-xs font-semibold py-1.5 rounded border border-indigo-500/20 transition-colors">
                      Generate Drafts
                    </button>
                    <button className="flex-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-semibold py-1.5 rounded border border-emerald-500/20 transition-colors">
                      Start Sending
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
