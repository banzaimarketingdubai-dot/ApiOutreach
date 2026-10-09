import React, { useState, useEffect } from 'react';
import { getVaultStatus, setVaultKey, getTemplates, createTemplate, deleteTemplate } from '../services/api';
import { Shield, Key, FileText, Plus, Trash2, Loader2, Save } from 'lucide-react';

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('vault'); // vault or templates
  const [vaultKeys, setVaultKeys] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form states
  const [provider, setProvider] = useState('apify');
  const [apiKey, setApiKey] = useState('');
  
  const [tplName, setTplName] = useState('');
  const [tplNiche, setTplNiche] = useState('');
  const [tplText, setTplText] = useState('');

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'vault') {
        const data = await getVaultStatus();
        setVaultKeys(data);
      } else {
        const data = await getTemplates();
        setTemplates(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveKey = async (e) => {
    e.preventDefault();
    try {
      await setVaultKey(provider, apiKey);
      alert('Key saved successfully!');
      setApiKey('');
      fetchData();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleSaveTemplate = async (e) => {
    e.preventDefault();
    try {
      await createTemplate({ name: tplName, niche: tplNiche, template_text: tplText });
      setTplName(''); setTplNiche(''); setTplText('');
      fetchData();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleDeleteTemplate = async (id) => {
    if (!window.confirm('Delete this template?')) return;
    try {
      await deleteTemplate(id);
      fetchData();
    } catch(e) {
      alert(e.message);
    }
  }

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 backdrop-blur-md min-h-[500px]">
      <div className="flex space-x-6 border-b border-slate-800 mb-6 pb-2">
        <button
          onClick={() => setActiveTab('vault')}
          className={`flex items-center space-x-2 font-bold transition ${activeTab === 'vault' ? 'text-blue-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          <Shield className="w-5 h-5" />
          <span>Security & Vault</span>
        </button>
        <button
          onClick={() => setActiveTab('templates')}
          className={`flex items-center space-x-2 font-bold transition ${activeTab === 'templates' ? 'text-purple-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          <FileText className="w-5 h-5" />
          <span>Prompt Templates</span>
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-slate-500" /></div>
      ) : activeTab === 'vault' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-white font-bold text-lg mb-4 flex items-center space-x-2"><Key className="w-4 h-4 text-blue-400"/> <span>Add / Update API Key</span></h3>
            <form onSubmit={handleSaveKey} className="space-y-4 bg-slate-950 p-5 rounded-xl border border-slate-800">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Provider</label>
                <select 
                  value={provider} onChange={(e) => setProvider(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm"
                >
                  <option value="apify">Apify</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="hubspot">HubSpot CRM</option>
                  <option value="resend">Resend (Outreach)</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">API Key</label>
                <input 
                  type="password" required value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm"
                  placeholder="Paste your secure token here"
                />
              </div>
              <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 rounded-lg text-sm flex items-center justify-center space-x-2">
                <Save className="w-4 h-4" /> <span>Save to Vault</span>
              </button>
            </form>
          </div>
          <div>
            <h3 className="text-white font-bold text-lg mb-4">Configured Integrations</h3>
            <div className="space-y-2">
              {vaultKeys.length === 0 ? <p className="text-slate-500 text-sm">No keys configured in DB or .env.</p> : vaultKeys.map(k => (
                <div key={k.provider} className="flex justify-between items-center bg-slate-950 border border-slate-800 px-4 py-3 rounded-lg">
                  <div className="flex flex-col space-y-1">
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]" />
                      <span className="text-slate-200 font-bold capitalize">{k.provider}</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded uppercase tracking-wider ${k.source === 'Vault' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'bg-slate-700/50 text-slate-400 border border-slate-700'}`}>{k.source}</span>
                    </div>
                    {k.masked && <span className="text-slate-500 font-mono text-[10px] pl-5">{k.masked}</span>}
                  </div>
                  <span className="text-[10px] bg-green-500/10 text-green-400 px-2 py-0.5 rounded border border-green-500/20 uppercase tracking-wider">Active</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <h3 className="text-white font-bold text-lg mb-4 flex items-center space-x-2"><Plus className="w-4 h-4 text-purple-400"/> <span>New Template</span></h3>
            <form onSubmit={handleSaveTemplate} className="space-y-4 bg-slate-950 p-5 rounded-xl border border-slate-800">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Name</label>
                <input required value={tplName} onChange={e=>setTplName(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" placeholder="e.g. Dubai Real Estate Pitch" />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Niche (Optional)</label>
                <input value={tplNiche} onChange={e=>setTplNiche(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" placeholder="e.g. Real Estate" />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Template Content</label>
                <textarea required value={tplText} onChange={e=>setTplText(e.target.value)} rows={5} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" placeholder="Hi {{company_name}}..." />
              </div>
              <button type="submit" className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-2 rounded-lg text-sm flex items-center justify-center space-x-2">
                <Save className="w-4 h-4" /> <span>Create Template</span>
              </button>
            </form>
          </div>
          <div className="lg:col-span-2">
            <h3 className="text-white font-bold text-lg mb-4">Saved Templates</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.length === 0 ? <p className="text-slate-500 text-sm">No templates saved yet.</p> : templates.map(t => (
                <div key={t.id} className="bg-slate-950 border border-slate-800 p-4 rounded-xl relative group">
                  <h4 className="font-bold text-white mb-1">{t.name}</h4>
                  <p className="text-xs text-purple-400 mb-3">{t.niche || 'General'}</p>
                  <p className="text-xs text-slate-400 line-clamp-3 mb-4">{t.template_text}</p>
                  <button onClick={() => handleDeleteTemplate(t.id)} className="absolute top-3 right-3 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
