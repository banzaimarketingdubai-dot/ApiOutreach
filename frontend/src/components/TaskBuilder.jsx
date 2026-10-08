import React, { useState } from 'react';
import { Play, Sparkles, Server, CheckCircle2, Clock } from 'lucide-react';
import { createCampaign } from '../services/api';

export default function TaskBuilder({ onCampaignCreated, onOpenAIStrategist, campaigns = [] }) {
  const [campaignName, setCampaignName] = useState('Manual Dental Clinic Scraping');
  const [geo, setGeo] = useState('Dubai');
  const [niche, setNiche] = useState('Dental Clinics');
  const [query, setQuery] = useState('Dental Clinic in Dubai');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        campaign_name: campaignName,
        target_geo: geo,
        target_niches: [niche],
        ai_config: {
          campaign_name: campaignName,
          target_geo: geo,
          target_niches: [niche],
          search_queries: [query],
          sources: ['gmaps'],
          custom_variables: [
            { key: 'has_online_booking', description: 'Check if site has online booking', variable_type: 'boolean' }
          ],
          scoring_rules: {
            missing_website_penalty: 10,
            low_rating_penalty: 15,
            low_reviews_penalty: 20
          }
        }
      };
      await createCampaign(payload);
      alert('Pipeline task submitted!');
      if (onCampaignCreated) onCampaignCreated();
    } catch (err) {
      alert('Error creating campaign: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8 text-xs">
      
      {/* Left: Manual Task Launch Card */}
      <div className="lg:col-span-1 bg-slate-900/70 border border-slate-800 rounded-3xl p-6 backdrop-blur-md flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-base text-white flex items-center space-x-2">
              <Server className="w-4 h-4 text-blue-400" />
              <span>Quick Task Builder</span>
            </h3>
            <span className="text-[10px] text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/20">
              Direct Celery
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-slate-400 font-semibold mb-1 block">Campaign Name</label>
              <input
                type="text"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 font-semibold mb-1 block">Target GEO</label>
                <input
                  type="text"
                  value={geo}
                  onChange={(e) => setGeo(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                />
              </div>
              <div>
                <label className="text-slate-400 font-semibold mb-1 block">Niche</label>
                <input
                  type="text"
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                />
              </div>
            </div>

            <div>
              <label className="text-slate-400 font-semibold mb-1 block">Search Query</label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold flex items-center justify-center space-x-2 transition-all shadow-lg shadow-blue-600/20"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>{submitting ? 'Dispatching Task...' : 'Launch Direct Task'}</span>
            </button>
          </form>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-800 text-center">
          <button
            onClick={onOpenAIStrategist}
            className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center space-x-1 text-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Need AI Recommendations? Open Co-pilot</span>
          </button>
        </div>
      </div>

      {/* Right: Active Campaigns & Task Logs Table */}
      <div className="lg:col-span-2 bg-slate-900/70 border border-slate-800 rounded-3xl p-6 backdrop-blur-md">
        <h3 className="font-bold text-base text-white mb-4 flex items-center space-x-2">
          <Clock className="w-4 h-4 text-purple-400" />
          <span>Active Pipeline Runs & Celery History</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                <th className="py-2.5 px-3">Campaign Name</th>
                <th className="py-2.5 px-3">GEO / Niche</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Stats</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {campaigns.length === 0 ? (
                <tr>
                  <td colSpan="4" className="py-8 text-center text-slate-500">
                    No active campaign runs yet. Use Quick Task Builder or AI Strategist to start.
                  </td>
                </tr>
              ) : (
                campaigns.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40">
                    <td className="py-3 px-3 font-semibold text-white">{c.campaign_name}</td>
                    <td className="py-3 px-3 text-slate-300">{c.target_geo} / {c.target_niches?.join(', ')}</td>
                    <td className="py-3 px-3">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                        c.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                        c.status === 'RUNNING' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse' :
                        'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                      {c.stats ? `Scraped: ${c.stats.total_scraped || 0} | New: ${c.stats.new_leads_created || 0}` : 'In Queue'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
