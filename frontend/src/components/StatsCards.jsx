import React from 'react';
import { Database, MessageSquare, Mail, Phone, Globe, Sparkles, Send, PhoneCall } from 'lucide-react';

export default function StatsCards({ stats = { total: 0, whatsapp: 0, telegram: 0, viber: 0, email: 0, phone: 0, website: 0, enrichment_in_progress: 0, enrichment_completed: 0, enrichment_failed: 0 }, filters, setFilters }) {
  
  const toggleFilter = (key) => {
    // If it's already true, clear it, otherwise set it to true (and clear the other contact filters to avoid conflicting empty sets, though they could be ANDed)
    const isActive = filters[key] === true;
    const isEnrich = filters.enrichment_status === key;
    
    // We clear page to 1 when changing filters
    setFilters({
      ...filters,
      has_whatsapp: key === 'has_whatsapp' ? !isActive : '',
      has_telegram: key === 'has_telegram' ? !isActive : '',
      has_viber: key === 'has_viber' ? !isActive : '',
      has_email: key === 'has_email' ? !isActive : '',
      has_phone: key === 'has_phone' ? !isActive : '',
      has_website: key === 'has_website' ? !isActive : '',
      enrichment_status: (key === 'in_progress' || key === 'completed' || key === 'failed') ? (isEnrich ? '' : key) : '',
      page: 1
    });
  };

  const inProg = stats.enrichment_in_progress || 0;
  const comp = stats.enrichment_completed || 0;
  const fail = stats.enrichment_failed || 0;

  const cards = [
    {
      title: 'Total Master Data Leads',
      value: stats.total || 0,
      change: 'Global Database Size',
      icon: Database,
      color: 'from-blue-500/20 to-blue-600/5 text-blue-400 border-blue-500/20',
      activeColor: 'border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)] bg-blue-900/20',
      filterKey: 'all',
      onClick: () => setFilters({...filters, has_whatsapp: '', has_telegram: '', has_viber: '', has_email: '', has_phone: '', has_website: '', enrichment_status: '', page: 1}),
      isActive: !filters.has_whatsapp && !filters.has_telegram && !filters.has_viber && !filters.has_email && !filters.has_phone && !filters.has_website && !filters.enrichment_status
    },
    {
      title: 'AI Enrichment Queue',
      value: `${inProg} / ${comp}`,
      change: `${fail} failed`,
      icon: Sparkles,
      color: 'from-fuchsia-500/20 to-fuchsia-600/5 text-fuchsia-400 border-fuchsia-500/20',
      activeColor: 'border-fuchsia-500 shadow-[0_0_15px_rgba(217,70,239,0.3)] bg-fuchsia-900/20',
      filterKey: 'in_progress',
      onClick: () => toggleFilter('in_progress'),
      isActive: filters.enrichment_status === 'in_progress' || filters.enrichment_status === 'completed'
    },
    {
      title: 'Websites Collected',
      value: stats.website || 0,
      change: 'Domains ready for AI enrichment',
      icon: Globe,
      color: 'from-cyan-500/20 to-cyan-600/5 text-cyan-400 border-cyan-500/20',
      activeColor: 'border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.3)] bg-cyan-900/20',
      filterKey: 'has_website',
      onClick: () => toggleFilter('has_website'),
      isActive: filters.has_website === true
    },
    {
      title: 'Email Verified',
      value: stats.email || 0,
      change: 'Cold email sequencing ready',
      icon: Mail,
      color: 'from-amber-500/20 to-amber-600/5 text-amber-400 border-amber-500/20',
      activeColor: 'border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.3)] bg-amber-900/20',
      filterKey: 'has_email',
      onClick: () => toggleFilter('has_email'),
      isActive: filters.has_email === true
    },
    {
      title: 'Telegram Verified',
      value: stats.telegram || 0,
      change: 'Direct messenger outreach',
      icon: Send,
      color: 'from-blue-500/20 to-blue-600/5 text-blue-400 border-blue-500/20',
      activeColor: 'border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)] bg-blue-900/20',
      filterKey: 'has_telegram',
      onClick: () => toggleFilter('has_telegram'),
      isActive: filters.has_telegram === true
    },
    {
      title: 'Viber Verified',
      value: stats.viber || 0,
      change: 'Direct messenger outreach',
      icon: PhoneCall,
      color: 'from-indigo-500/20 to-indigo-600/5 text-indigo-400 border-indigo-500/20',
      activeColor: 'border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.3)] bg-indigo-900/20',
      filterKey: 'has_viber',
      onClick: () => toggleFilter('has_viber'),
      isActive: filters.has_viber === true
    },
    {
      title: 'WhatsApp Verified',
      value: stats.whatsapp || 0,
      change: 'Direct messenger outreach ready',
      icon: MessageSquare,
      color: 'from-emerald-500/20 to-emerald-600/5 text-emerald-400 border-emerald-500/20',
      activeColor: 'border-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.3)] bg-emerald-900/20',
      filterKey: 'has_whatsapp',
      onClick: () => toggleFilter('has_whatsapp'),
      isActive: filters.has_whatsapp === true
    },
    {
      title: 'Phone Numbers',
      value: stats.phone || 0,
      change: 'Cold calling / SMS ready',
      icon: Phone,
      color: 'from-purple-500/20 to-purple-600/5 text-purple-400 border-purple-500/20',
      activeColor: 'border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.3)] bg-purple-900/20',
      filterKey: 'has_phone',
      onClick: () => toggleFilter('has_phone'),
      isActive: filters.has_phone === true
    },
  ];

  return (
    <div className="flex overflow-x-auto pb-4 snap-x snap-mandatory gap-4 mb-2 md:grid md:grid-cols-2 lg:grid-cols-4 md:overflow-visible md:pb-0 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
      {cards.map((item, index) => {
        const Icon = item.icon;
        return (
          <div
            key={index}
            onClick={item.onClick}
            className={`flex-none w-[280px] md:w-auto snap-center p-4 rounded-2xl cursor-pointer bg-slate-900/60 border ${item.isActive ? item.activeColor : item.color} backdrop-blur-md relative overflow-hidden group hover:border-slate-500 transition-all`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-400">{item.title}</p>
                <h3 className="text-2xl font-bold text-white mt-1 tracking-tight">{item.value}</h3>
              </div>
              <div className={`p-3 rounded-xl bg-slate-800/80 border border-slate-700/50`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
            <p className="text-[11px] text-slate-400 mt-2 flex items-center">
              <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${item.isActive ? 'bg-white' : 'bg-slate-600'}`}></span>
              {item.change}
            </p>
          </div>
        );
      })}
    </div>
  );
}
