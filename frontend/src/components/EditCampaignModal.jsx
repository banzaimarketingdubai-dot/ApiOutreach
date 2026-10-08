import React, { useState } from 'react';
import { Settings, Save, X } from 'lucide-react';
import { updateCampaign } from '../services/api';

export default function EditCampaignModal({ campaignId, onClose, initialData }) {
  const [geo, setGeo] = useState(initialData?.target_geo || '');
  const [query, setQuery] = useState(initialData?.ai_config?.search_queries?.[0] || '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateCampaign(campaignId, {
        target_geo: geo,
        ai_config: { search_queries: [query] }
      });
      alert('Campaign settings updated on the fly!');
      onClose();
    } catch (e) {
      alert('Failed to update: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-[400px] overflow-hidden shadow-2xl">
        <div className="px-5 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
          <h3 className="font-bold text-white flex items-center space-x-2">
            <Settings className="w-4 h-4 text-blue-400" />
            <span>Hot-Swap Settings</span>
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded text-slate-400"><X className="w-4 h-4" /></button>
        </div>
        
        <div className="p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1">Target GEO</label>
            <input 
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-sm"
              value={geo}
              onChange={e => setGeo(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1">Search Query</label>
            <input 
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-sm"
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
          </div>
          <div className="text-[10px] text-amber-400/80 bg-amber-500/10 p-2 rounded border border-amber-500/20">
            Changes will be applied to the next processing batch without stopping the Celery worker.
          </div>
        </div>

        <div className="px-5 py-4 border-t border-slate-800 bg-slate-950 flex justify-end space-x-3">
          <button onClick={onClose} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">Cancel</button>
          <button 
            onClick={handleSave} 
            disabled={saving}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg flex items-center space-x-2 shadow-lg shadow-blue-500/20"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{saving ? 'Saving...' : 'Apply on the fly'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
