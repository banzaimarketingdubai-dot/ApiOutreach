import React, { useState, useEffect } from 'react';
import { Bot, Sparkles, Database, Layers, Wallet, CheckCircle2, GitMerge, Send, Target, BarChart2 } from 'lucide-react';
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between overflow-x-auto gap-4 hide-scrollbar snap-x [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        
        {/* Brand & Workspace Selector */}
        <div className="flex items-center space-x-4 lg:space-x-6 flex-shrink-0 snap-center">
          <div className="flex items-center space-x-3 whitespace-nowrap">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20 ring-1 ring-white/20 flex-shrink-0">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col justify-center">
              <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent leading-none mb-1">
                REVO <span className="text-blue-500 font-light">MASTER DATA</span>
              </span>
              <p className="text-[10px] text-slate-400 leading-none">AI-Driven Lead Gen</p>
            </div>
          </div>
          
          <div className="hidden md:block h-6 w-px bg-slate-800"></div>

          <select
            value={globalCampaignId}
            onChange={(e) => setGlobalCampaignId(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white font-semibold rounded-lg text-sm px-3 py-1.5 focus:ring focus:ring-blue-500/50 outline-none hover:bg-slate-800 transition-colors cursor-pointer w-40 lg:w-48 truncate"
          >
            <option value="">Global (All Projects)</option>
            {campaigns.map(c => (
              <option key={c.id} value={c.id}>{c.campaign_name}</option>
            ))}
          </select>
        </div>

        {/* Center/Right: Apify Status Badge + Nav Tabs + Actions */}
        <div className="flex items-center space-x-4 flex-shrink-0 snap-center">

          {/* Apify Balance Widget */}
          {apifyData && apifyData.connected && (
            <div className="hidden lg:flex items-center space-x-2.5 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-emerald-500/30 text-xs shadow-inner">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <div className="text-left">
                <span className="text-slate-300 font-medium block text-[11px]">
                  Apify ({apifyData.plan_name}): <span className="text-emerald-400 font-bold">${apifyData.remaining_usd}</span> / ${apifyData.monthly_limit_usd}
                </span>
              </div>
            </div>
          )}

          <nav className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('leads')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'leads'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>Master Data</span>
            </button>

            <button
              onClick={() => setActiveTab('builder')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'builder'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Campaign Builder</span>
            </button>

            <button
              onClick={() => setActiveTab('merge')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'merge'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <GitMerge className="w-3.5 h-3.5" />
              <span>Merge Center</span>
            </button>

            <button
              onClick={() => setActiveTab('outreach')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'outreach'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Send className="w-3.5 h-3.5" />
              <span>Outreach</span>
            </button>

            <button
              onClick={() => setActiveTab('promotrack')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'promotrack'
                  ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Target className="w-3.5 h-3.5" />
              <span>Promo Track</span>
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'analytics'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              <span>Analytics</span>
            </button>

            <button
              onClick={() => setActiveTab('admin')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'admin'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Wallet className="w-3.5 h-3.5" />
              <span>Settings & Templates</span>
            </button>
          </nav>

          <button
            onClick={onOpenAIStrategist}
            className="group relative inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 shadow-lg shadow-indigo-500/25 transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0"
          >
            <Sparkles className="w-4 h-4 text-amber-300 animate-pulse" />
            <span>AI Strategist Co-pilot</span>
          </button>

          {/* User Profile Badge & Logout */}
          {user && (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-semibold text-slate-200 truncate max-w-[120px]">{user.full_name || 'Admin'}</span>
                <span className="text-[10px] text-slate-400 truncate max-w-[120px]">{user.email}</span>
              </div>
              <button
                onClick={onLogout}
                title="Выйти из аккаунта"
                className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-rose-400 hover:border-rose-500/30 transition-colors cursor-pointer"
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
