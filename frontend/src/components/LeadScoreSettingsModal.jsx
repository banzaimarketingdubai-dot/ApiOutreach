import React, { useState } from 'react';
import { Target, Save, X, RefreshCw } from 'lucide-react';
import { recalculateScore } from '../services/api';

export default function LeadScoreSettingsModal({ campaignId, onClose, initialRules }) {
  const [rules, setRules] = useState(initialRules || {
    "website_weight": 2.0,
    "phone_weight": 2.0,
    "rating_threshold": 4.0
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await recalculateScore(campaignId, rules);
      alert(`Scores recalculated successfully for ${res.updated_leads} leads!`);
      onClose();
    } catch (e) {
      alert('Failed to recalculate: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  const updateRule = (key, val) => setRules({...rules, [key]: parseFloat(val) || 0});

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-[400px] overflow-hidden shadow-2xl">
        <div className="px-5 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
          <h3 className="font-bold text-white flex items-center space-x-2">
            <Target className="w-4 h-4 text-purple-400" />
            <span>Revo Score Engine</span>
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded text-slate-400"><X className="w-4 h-4" /></button>
        </div>
        
        <div className="p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1">Website Weight</label>
            <input 
              type="number"
              step="0.1"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-sm"
              value={rules.website_weight}
              onChange={e => updateRule("website_weight", e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1">Phone Weight</label>
            <input 
              type="number"
              step="0.1"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-sm"
              value={rules.phone_weight}
              onChange={e => updateRule("phone_weight", e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1">Minimum Rating Threshold</label>
            <input 
              type="number"
              step="0.1"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-sm"
              value={rules.rating_threshold}
              onChange={e => updateRule("rating_threshold", e.target.value)}
            />
          </div>
          
          <div className="text-[10px] text-purple-400/80 bg-purple-500/10 p-2 rounded border border-purple-500/20">
            Applying this will mass-recalculate the Revo Score for all extracted leads in this campaign based on the new weights.
          </div>
        </div>

        <div className="px-5 py-4 border-t border-slate-800 bg-slate-950 flex justify-end space-x-3">
          <button onClick={onClose} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">Cancel</button>
          <button 
            onClick={handleSave} 
            disabled={saving}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-lg flex items-center space-x-2 shadow-lg shadow-purple-500/20"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${saving ? 'animate-spin' : ''}`} />
            <span>{saving ? 'Recalculating...' : 'Recalculate Batch'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
