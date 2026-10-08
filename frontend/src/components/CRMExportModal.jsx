import React, { useState } from 'react';
import { Cloud, Loader2, X, Check, Server } from 'lucide-react';

export default function CRMExportModal({ leads = [], onClose }) {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Take only first 10 for validation
  const validationSet = leads.slice(0, 10);

  const handlePush = () => {
    setLoading(true);
    // Mock API call to CRM
    setTimeout(() => {
      setLoading(false);
      setSuccess(true);
    }, 2000);
  };

  if (success) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div className="bg-slate-900 border border-slate-700 rounded-2xl w-[400px] p-8 text-center shadow-2xl">
          <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-green-500/30">
            <Check className="w-8 h-8 text-green-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Export Successful</h2>
          <p className="text-slate-400 text-sm mb-6">Successfully pushed {leads.length} leads to HubSpot CRM.</p>
          <button 
            onClick={onClose}
            className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-bold transition"
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-[700px] max-h-[85vh] overflow-hidden shadow-2xl flex flex-col">
        <div className="px-5 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
          <h3 className="font-bold text-white flex items-center space-x-2">
            <Cloud className="w-4 h-4 text-blue-400" />
            <span>CRM Export Validation</span>
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded text-slate-400"><X className="w-4 h-4" /></button>
        </div>
        
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          <div className="flex items-center justify-between bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl">
            <div>
              <h4 className="text-blue-400 font-bold mb-1">Pushing {leads.length} leads to HubSpot</h4>
              <p className="text-xs text-blue-300/70">Review the first 10 leads before triggering the bulk API sync.</p>
            </div>
            <Server className="w-8 h-8 text-blue-400/50" />
          </div>

          <div className="space-y-3">
            {validationSet.map((l, i) => (
              <div key={i} className="flex flex-col bg-slate-950 border border-slate-800 rounded-lg p-3">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-bold text-sm text-white">{l.company_name}</span>
                  <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">Revo Score: {l.revo_score}</span>
                </div>
                <div className="text-xs text-slate-400 grid grid-cols-2 gap-2">
                  <div><span className="font-semibold text-slate-500">GEO:</span> {l.city || 'N/A'}</div>
                  <div><span className="font-semibold text-slate-500">Website:</span> {l.website || 'N/A'}</div>
                  <div><span className="font-semibold text-slate-500">Phone:</span> {l.phone || (l.contacts?.find(c => c.contact_type === 'phone')?.contact_value) || 'N/A'}</div>
                  <div><span className="font-semibold text-slate-500">Business:</span> {l.business_type || 'N/A'}</div>
                </div>
              </div>
            ))}
          </div>
          {leads.length > 10 && (
            <div className="text-center text-xs font-semibold text-slate-500 py-2">
              ... and {leads.length - 10} more leads.
            </div>
          )}
        </div>

        <div className="px-5 py-4 border-t border-slate-800 bg-slate-950 flex justify-end space-x-3">
          <button onClick={onClose} className="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white">Cancel</button>
          <button 
            onClick={handlePush} 
            disabled={loading || leads.length === 0}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg flex items-center space-x-2 shadow-lg shadow-blue-500/20"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Cloud className="w-3.5 h-3.5" />}
            <span>{loading ? 'Syncing via API...' : 'Confirm & Sync'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
