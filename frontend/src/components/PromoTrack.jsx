import React, { useState, useEffect } from 'react';
import { Target, ShieldCheck, Zap, Mail, ChevronRight, Clock, Star, ExternalLink, Search } from 'lucide-react';
// import { apiCall } from '../services/api';

export default function PromoTrack({ onSelectLead }) {
  // Mock data for UI demonstration
  const [promoLeads] = useState([
    {
      id: 1,
      company_name: 'Manhattan Bakery & Cafe',
      business_type: 'Cafe & Bakery',
      website: 'https://manhattanbakery.com',
      status: 'TRIAL_ACTIVE',
      day: 3,
      rating: 4.9,
      reviews: 148,
      next_action: 'Send Profile Guard Hack (Day 3)'
    },
    {
      id: 2,
      company_name: 'Artisan Barbers',
      business_type: 'Barbershop',
      website: 'https://artisanbarbers.kyiv.ua',
      status: 'CODE_SENT',
      day: 0,
      rating: 4.2,
      reviews: 55,
      next_action: 'Wait for Signup Webhook'
    },
    {
      id: 3,
      company_name: 'Smile Dental Clinic',
      business_type: 'Dental Clinic',
      website: '',
      status: 'CONVERTED',
      day: 14,
      rating: 4.8,
      reviews: 320,
      next_action: 'None (Subscribed to Pro)'
    }
  ]);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Target className="w-32 h-32 text-amber-500" />
        </div>
        <div className="relative z-10 max-w-2xl">
          <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
            <Target className="w-6 h-6 text-amber-500" />
            Promo Track (Hot Leads)
          </h2>
          <p className="text-slate-400 text-sm">
            Monitor leads who replied and received the Welcome14 code. Track their 14-day onboarding journey across GBPilot features.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
            <Mail className="w-5 h-5 text-blue-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-200">24</div>
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Codes Sent</div>
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4 border-b-2 border-b-emerald-500">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
            <Clock className="w-5 h-5 text-emerald-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-200">12</div>
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Active Trials</div>
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4 border-b-2 border-b-amber-500">
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
            <Star className="w-5 h-5 text-amber-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-200">8</div>
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Converted</div>
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-200">4</div>
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Dropped (Free)</div>
          </div>
        </div>
      </div>

      {/* Main Tracker Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Zap className="w-4 h-4 text-emerald-500" />
            Live Trial Pipelines
          </h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900/50 border-b border-slate-800">
                <th className="px-6 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Company</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Trial Day</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Onboarding Funnel (Next Touch)</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {promoLeads.map((lead) => (
                <tr key={lead.id} className="hover:bg-slate-800/20 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="font-semibold text-slate-200 cursor-pointer hover:text-blue-400 transition-colors" onClick={() => onSelectLead(lead)}>
                      {lead.company_name}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{lead.business_type}</div>
                    <div className="text-xs text-slate-500 flex items-center gap-2 mt-1">
                      <Star className="w-3 h-3 text-amber-500" /> {lead.rating} ({lead.reviews} revs)
                      {lead.website && (
                        <>
                          <span className="w-1 h-1 bg-slate-700 rounded-full"></span>
                          <a href={lead.website} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-blue-400">
                            <ExternalLink className="w-3 h-3" /> Web
                          </a>
                        </>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {lead.status === 'TRIAL_ACTIVE' && <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>Active Trial</span>}
                    {lead.status === 'CODE_SENT' && <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20">Code Sent</span>}
                    {lead.status === 'CONVERTED' && <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20">Converted ($$)</span>}
                  </td>
                  <td className="px-6 py-4">
                    {lead.status === 'TRIAL_ACTIVE' ? (
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden w-24">
                          <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${(lead.day / 14) * 100}%` }}></div>
                        </div>
                        <span className="text-xs font-mono text-slate-400">Day {lead.day}/14</span>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-600">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-xs font-medium text-slate-300">{lead.next_action}</div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={() => onSelectLead(lead)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                      title="Inspect Full Profile"
                    >
                      <Search className="w-4 h-4" />
                    </button>
                    <button className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors ml-1">
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
