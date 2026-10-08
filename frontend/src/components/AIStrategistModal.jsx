import React, { useState } from 'react';
import { Sparkles, X, Check, RefreshCw, Send, Plus, Trash2, ArrowRight } from 'lucide-react';
import { generateAIStrategy, createCampaign } from '../services/api';

export default function AIStrategistModal({ isOpen, onClose, onCampaignCreated }) {
  const [goal, setGoal] = useState('');
  const [geo, setGeo] = useState('');
  const [notes, setNotes] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState(null);
  const [editingConfig, setEditingConfig] = useState(null);
  const [launching, setLaunching] = useState(false);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    if (!goal.trim()) {
      alert("Please enter your Outreach Goal before generating a strategy.");
      return;
    }
    setLoading(true);
    try {
      const res = await generateAIStrategy(goal, geo || "Worldwide", notes);
      setStrategy(res);
      setEditingConfig(res.recommendation);
    } catch (err) {
      alert('Failed to generate strategy: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomVarChange = (idx, field, value) => {
    const updatedVars = [...editingConfig.custom_variables];
    updatedVars[idx][field] = value;
    setEditingConfig({ ...editingConfig, custom_variables: updatedVars });
  };

  const handleAddCustomVar = () => {
    const updatedVars = [
      ...editingConfig.custom_variables,
      { key: 'new_variable', description: 'Description for LLM', variable_type: 'boolean' }
    ];
    setEditingConfig({ ...editingConfig, custom_variables: updatedVars });
  };

  const handleRemoveCustomVar = (idx) => {
    const updatedVars = editingConfig.custom_variables.filter((_, i) => i !== idx);
    setEditingConfig({ ...editingConfig, custom_variables: updatedVars });
  };

  const handleApproveAndLaunch = async () => {
    setLaunching(true);
    try {
      const payload = {
        campaign_name: editingConfig.campaign_name,
        target_geo: editingConfig.target_geo,
        target_niches: editingConfig.target_niches,
        ai_config: editingConfig
      };
      await createCampaign(payload);
      alert('🚀 Campaign approved and launched successfully!');
      if (onCampaignCreated) onCampaignCreated();
      onClose();
    } catch (err) {
      alert('Error launching campaign: ' + err.message);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md">
              <Sparkles className="w-5 h-5 animate-spin-slow" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">AI Campaign Strategist & Co-pilot</h2>
              <p className="text-xs text-slate-400">Describe your outreach goal; Gemini 3.8 auto-builds queries & variables</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          
          {/* Input Box */}
          <div className="space-y-3 bg-slate-950/60 p-4 rounded-2xl border border-slate-800">
            <label className="font-semibold text-slate-300 block">1. Define Outreach Goal & Target GEO</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <input
                  type="text"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="E.g., High-end dental clinics in Dubai needing CRM booking..."
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <input
                  type="text"
                  value={geo}
                  onChange={(e) => setGeo(e.target.value)}
                  placeholder="Target GEO (e.g. Dubai)"
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold px-4 py-2 rounded-xl hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 transition-all shadow-md"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Analyzing Strategy with Gemini 3.8...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Generate AI Campaign Proposal</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* AI Output / Editor */}
          {editingConfig && (
            <div className="space-y-4 border-t border-slate-800 pt-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-amber-400 flex items-center space-x-2">
                  <Check className="w-4 h-4 text-emerald-400" />
                  <span>AI Recommended Strategy & Custom Variables</span>
                </h3>
                <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-1 rounded-md">Editable before approval</span>
              </div>

              {/* Campaign Title & Queries */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-900/80 p-4 rounded-2xl border border-slate-800">
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Campaign Title</label>
                  <input
                    type="text"
                    value={editingConfig.campaign_name}
                    onChange={(e) => setEditingConfig({ ...editingConfig, campaign_name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white"
                  />
                </div>
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Target Search Queries</label>
                  <input
                    type="text"
                    value={editingConfig.search_queries.join(', ')}
                    onChange={(e) => setEditingConfig({ ...editingConfig, search_queries: e.target.value.split(',').map(s => s.trim()) })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white"
                  />
                </div>
              </div>

              {/* Custom Variables Section */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-300">Custom LLM Variables (Website Extraction)</span>
                  <button
                    onClick={handleAddCustomVar}
                    className="flex items-center space-x-1 text-blue-400 hover:text-blue-300 font-medium text-[11px]"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Variable</span>
                  </button>
                </div>

                <div className="space-y-2">
                  {editingConfig.custom_variables.map((item, idx) => (
                    <div key={idx} className="flex items-center space-x-2 bg-slate-950/80 p-2.5 rounded-xl border border-slate-800">
                      <input
                        type="text"
                        value={item.key}
                        onChange={(e) => handleCustomVarChange(idx, 'key', e.target.value)}
                        className="w-1/3 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-amber-300 font-mono"
                        placeholder="key_name"
                      />
                      <input
                        type="text"
                        value={item.description}
                        onChange={(e) => handleCustomVarChange(idx, 'description', e.target.value)}
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-300"
                        placeholder="Extraction instructions..."
                      />
                      <button
                        onClick={() => handleRemoveCustomVar(idx)}
                        className="text-slate-500 hover:text-red-400 p-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommended Outreach Pitch */}
              {editingConfig.recommended_outreach_angle && (
                <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/20 text-indigo-300">
                  <span className="font-semibold block mb-0.5">Recommended Pitch Angle:</span>
                  {editingConfig.recommended_outreach_angle}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-800 flex items-center justify-between bg-slate-900/90">
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-slate-400 hover:text-white font-medium">
            Cancel
          </button>
          
          {editingConfig && (
            <button
              onClick={handleApproveAndLaunch}
              disabled={launching}
              className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/30 transition-all"
            >
              {launching ? (
                <span>Launching Celery Pipeline...</span>
              ) : (
                <>
                  <span>Approve & Launch Pipeline</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
