import React, { useState, useEffect } from 'react';
import { getSuspectedDuplicates, mergeLeads } from '../services/api';
import { GitMerge, Loader2, CheckCircle, Trash2, ArrowRight } from 'lucide-react';

export default function MergeCenter() {
  const [duplicateGroups, setDuplicateGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [merging, setMerging] = useState(false);

  useEffect(() => {
    fetchDuplicates();
  }, []);

  const fetchDuplicates = async () => {
    setLoading(true);
    try {
      const data = await getSuspectedDuplicates();
      setDuplicateGroups(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleMerge = async (groupIdx, targetLeadId, sourceLeadId) => {
    if (!window.confirm('Are you sure you want to merge these leads? Source lead will be deleted.')) return;
    setMerging(true);
    try {
      await mergeLeads(sourceLeadId, targetLeadId);
      // Remove the merged lead from UI by re-fetching
      await fetchDuplicates();
    } catch (e) {
      alert(e.message);
    } finally {
      setMerging(false);
    }
  };

  if (loading) return <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-indigo-500" /></div>;

  if (duplicateGroups.length === 0) return (
    <div className="p-12 text-center text-slate-400">
      <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
      <h2 className="text-xl font-bold text-white mb-2">No duplicates found</h2>
      <p>The Master Data is perfectly clean!</p>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
            <GitMerge className="text-indigo-400" />
            <span>Smart Merge Center</span>
          </h2>
          <p className="text-slate-400 text-sm mt-1">Review suspected duplicates. Select a target to keep and a source to merge & delete.</p>
        </div>
        <div className="bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 px-4 py-2 rounded-lg font-bold">
          {duplicateGroups.length} Groups Found
        </div>
      </div>

      <div className="space-y-6">
        {duplicateGroups.map((group, gIdx) => (
          <div key={gIdx} className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
            <div className="bg-slate-800 px-4 py-2 border-b border-slate-700 text-sm font-semibold text-slate-300">
              Match Group {gIdx + 1}: "{group[0]?.company_name.split(' ')[0]}" in {group[0]?.city}
            </div>
            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              {group.map((lead, lIdx) => (
                <div key={lead.id} className="border border-slate-700 rounded-lg p-4 bg-slate-950 relative">
                  <h4 className="font-bold text-white mb-1">{lead.company_name}</h4>
                  <div className="text-xs text-slate-400 mb-4 space-y-1">
                    <p>🌐 {lead.website || 'No website'}</p>
                    <p>📞 {lead.phone || 'No phone'}</p>
                    <p>📍 {lead.address || 'No address'}</p>
                    <p>⭐ Score: {lead.revo_score}</p>
                  </div>
                  
                  {lIdx > 0 && (
                    <button 
                      onClick={() => handleMerge(gIdx, group[0].id, lead.id)}
                      disabled={merging}
                      className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-lg text-xs font-bold transition"
                    >
                      <span>Merge into Primary (Left)</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}
                  {lIdx === 0 && (
                    <div className="w-full text-center py-2 text-xs font-bold text-green-400 bg-green-500/10 border border-green-500/20 rounded-lg">
                      Primary Target
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
