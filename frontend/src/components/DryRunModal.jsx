import React, { useState } from 'react';
import { Play, Loader2, X } from 'lucide-react';
import { dryRunAI } from '../services/api';

export default function DryRunModal({ selectedLeads, onClose }) {
  const [prompt, setPrompt] = useState('Hi {{company_name}}, I see you are located in {{city}}. We would love to help you.');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);

  const handleRun = async () => {
    if (selectedLeads.length === 0) return alert('No leads selected');
    setLoading(true);
    try {
      const leadIds = selectedLeads.map(l => l.id);
      const data = await dryRunAI(prompt, leadIds);
      setResults(data.results || []);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-[600px] max-h-[80vh] overflow-hidden shadow-2xl flex flex-col">
        <div className="px-5 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
          <h3 className="font-bold text-white flex items-center space-x-2">
            <Play className="w-4 h-4 text-emerald-400" />
            <span>AI Dry Run Sandbox</span>
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded text-slate-400"><X className="w-4 h-4" /></button>
        </div>
        
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          <div className="text-sm text-slate-300">
            Testing on {selectedLeads.length} selected leads.
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1">Prompt Template</label>
            <textarea 
              rows={4}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-sm"
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
            />
            <p className="text-[10px] text-slate-500 mt-1">Available variables: {'{{company_name}}, {{city}}, {{address}}, {{business_type}}'}, plus any custom variables.</p>
          </div>
          
          {loading && <div className="flex justify-center p-4"><Loader2 className="w-6 h-6 animate-spin text-emerald-500" /></div>}
          
          {results.length > 0 && (
            <div className="space-y-4 mt-4">
              <h4 className="text-sm font-bold text-white">Generated Previews:</h4>
              {results.map((res, i) => (
                <div key={i} className="bg-slate-950 border border-slate-800 rounded-lg p-3">
                  <div className="text-xs font-bold text-emerald-400 mb-2">{res.lead_name}</div>
                  <div className="text-sm text-slate-300 whitespace-pre-wrap">{res.generated_text}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="px-5 py-4 border-t border-slate-800 bg-slate-950 flex justify-end space-x-3">
          <button onClick={onClose} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">Close</button>
          <button 
            onClick={handleRun} 
            disabled={loading || selectedLeads.length === 0}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg flex items-center space-x-2 shadow-lg shadow-emerald-500/20"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>Run Sandbox</span>
          </button>
        </div>
      </div>
    </div>
  );
}
