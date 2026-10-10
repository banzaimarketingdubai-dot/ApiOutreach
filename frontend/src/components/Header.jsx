import React, { useState, useEffect } from 'react';
import { Bot, Sparkles, Database, Layers, Wallet, CheckCircle2, GitMerge, Send, Target, BarChart2, Shield } from 'lucide-react';
import { fetchApifyBalance } from '../services/api';

export default function Header({ onOpenAIStrategist, activeTab, setActiveTab, campaigns = [], globalCampaignId, setGlobalCampaignId, user, onLogout }) {
  const [apifyData, setApifyData] = useState(null);

  useEffect(() => {
    fetchApifyBalance()
      .then((data) => setApifyData(data))
      .catch((err) => console.error('Apify balance fetch error:', err));
  }, []);

  return (
    <header className="border-b border-slate-800 bg-[#0c121e]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-[1400px] mx-auto px-3 sm:px-6 h-16 flex items-center justify-between gap-3">
        
        {/* Brand & Workspace Selector (Fixed Left) */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          <div className="flex items-center space-x-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20 ring-1 ring-white/20 flex-shrink-0">
              <Database className="w-4 h-4 text-white" />
            </div>
            <div className="hidden sm:flex flex-col justify-center">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent leading-none mb-0.5">
                REVO
              </span>
              <p className="text-[9px] text-slate-400 leading-none">AI Lead Gen</p>
            </div>
          </div>
          
          <div className="hidden md:block h-6 w-px bg-slate-800"></div>

          <select
            value={globalCampaignId}
            onChange={(e) => setGlobalCampaignId(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white font-semibold rounded-lg text-xs px-2 py-1.5 focus:ring focus:ring-blue-500/50 outline-none hover:bg-slate-800 transition-colors cursor-pointer w-32 md:w-40 truncate"
          >
            <option value="">Global</option>
            {campaigns.map(c => (
              <option key={c.id} value={c.id}>{c.campaign_name}</option>
            ))}
          </select>
        </div>

        {/* Center: Scrollable Nav Tabs */}
        <div className="flex-1 flex overflow-x-auto hide-scrollbar [scrollbar-width:none] px-1 mask-linear-fade">
          <nav className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800 flex-shrink-0 mx-auto space-x-1">
            <button
              onClick={() => setActiveTab('leads')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'leads'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Master Data</span>
            </button>

            <button
              onClick={() => setActiveTab('builder')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'builder'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Campaign Builder</span>
            </button>

            <button
              onClick={() => setActiveTab('merge')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'merge'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <GitMerge className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Merge</span>
            </button>

            <button
              onClick={() => setActiveTab('outreach')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'outreach'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Send className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Outreach</span>
            </button>

            <button
              onClick={() => setActiveTab('promotrack')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'promotrack'
                  ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Target className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Promo</span>
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'analytics'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Analytics</span>
            </button>

            <button
              onClick={() => setActiveTab('admin')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'admin'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Wallet className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Settings</span>
            </button>
            
            {user?.role === 'SUPER_ADMIN' && (
              <button
                onClick={() => setActiveTab('users')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === 'users'
                    ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30'
                    : 'text-violet-400 hover:text-violet-300 hover:bg-slate-800/50'
                }`}
              >
                <Shield className="w-3.5 h-3.5" />
                <span className="hidden lg:inline">Команда</span>
              </button>
            )}
          </nav>
        </div>

        {/* Right: Actions & Profile (Fixed Right) */}
        <div className="flex items-center space-x-3 flex-shrink-0">

          <button
            onClick={onOpenAIStrategist}
            className="group relative inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold text-white bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 shadow-md shadow-indigo-500/25 transition-all duration-200 transform hover:-translate-y-0.5"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
            <span className="hidden md:inline">AI Strategist</span>
            <span className="md:hidden">AI</span>
          </button>

          {user && (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
              <div className="hidden xl:flex flex-col text-right">
                <span className="text-[11px] font-semibold text-slate-200 truncate max-w-[100px]">{user.full_name || 'Admin'}</span>
                <span className="text-[9px] text-slate-400 truncate max-w-[100px]">{user.email}</span>
              </div>
              <button
                onClick={onLogout}
                title="Выйти"
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-rose-400 hover:border-rose-500/30 transition-colors cursor-pointer"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}
