import React from 'react';
import { Database, MessageSquare, Mail, Phone } from 'lucide-react';

export default function StatsCards({ stats = { total: 0, whatsapp: 0, email: 0, phone: 0 }, filters, setFilters }) {
  
  const toggleFilter = (key) => {
    // If it's already true, clear it, otherwise set it to true (and clear the other contact filters to avoid conflicting empty sets, though they could be ANDed)
    const isActive = filters[key] === true;
    
    // We clear page to 1 when changing filters
    setFilters({
      ...filters,
      has_whatsapp: key === 'has_whatsapp' ? !isActive : '',
      has_email: key === 'has_email' ? !isActive : '',
      has_phone: key === 'has_phone' ? !isActive : '',
      page: 1
    });
  };

  const cards = [
    {
      title: 'Total Master Data Leads',
      value: stats.total || 0,
      change: 'Global Database Size',
      icon: Database,
      color: 'from-blue-500/20 to-blue-600/5 text-blue-400 border-blue-500/20',
      activeColor: 'border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)] bg-blue-900/20',
      filterKey: 'all',
      onClick: () => setFilters({...filters, has_whatsapp: '', has_email: '', has_phone: '', page: 1}),
      isActive: !filters.has_whatsapp && !filters.has_email && !filters.has_phone
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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((item, index) => {
        const Icon = item.icon;
        return (
          <div
            key={index}
            onClick={item.onClick}
            className={`p-4 rounded-2xl cursor-pointer bg-slate-900/60 border ${item.isActive ? item.activeColor : item.color} backdrop-blur-md relative overflow-hidden group hover:border-slate-500 transition-all`}
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
