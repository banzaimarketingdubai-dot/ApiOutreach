import React, { useState } from 'react';
import { Search, Download, Filter, Star, Globe, Phone, Mail, MessageSquare, MapPin, ExternalLink, Flame, Play, Cloud, Send, MessageCircle, XOctagon } from 'lucide-react';
import { getExportCsvUrl, checkMessengers, exportLeadRadar } from '../services/api';
import DryRunModal from './DryRunModal';
import CRMExportModal from './CRMExportModal';
import OmnichannelOutreachModal from './OmnichannelOutreachModal';

export default function MasterDataGrid({ leads = [], onSelectLead, filters, setFilters, onRefresh, pagination = { total: 0, total_pages: 1, page: 1 } }) {
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [selectAllGlobal, setSelectAllGlobal] = useState(false);
  const [dryRunModalOpen, setDryRunModalOpen] = useState(false);
  const [crmModalOpen, setCrmModalOpen] = useState(false);
  const [outreachLead, setOutreachLead] = useState(null);
  const [isCheckingMessengers, setIsCheckingMessengers] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSort = (column) => {
    if (filters.sort_by === column) {
      setFilters({ ...filters, sort_order: filters.sort_order === 'asc' ? 'desc' : 'asc' });
    } else {
      setFilters({ ...filters, sort_by: column, sort_order: 'desc' });
    }
  };

  const getSortIcon = (column) => {
    if (filters.sort_by !== column) return <span className="opacity-0 group-hover:opacity-30 ml-1">↕</span>;
    return <span className="text-blue-400 ml-1">{filters.sort_order === 'asc' ? '↑' : '↓'}</span>;
  };

  const handleExportCSV = () => {
    const url = getExportCsvUrl(filters);
    window.open(url, '_blank');
  };

  const toggleLeadSelection = (lead, e) => {
    e.stopPropagation();
    setSelectAllGlobal(false);
    if (selectedLeads.find(l => l.id === lead.id)) {
      setSelectedLeads(selectedLeads.filter(l => l.id !== lead.id));
    } else {
      setSelectedLeads([...selectedLeads, lead]);
    }
  };

  const toggleSelectAll = (e) => {
    if (e.target.checked) {
      const newSelected = [...selectedLeads];
      leads.forEach(lead => {
        if (!newSelected.find(l => l.id === lead.id)) {
          newSelected.push(lead);
        }
      });
      setSelectedLeads(newSelected);
    } else {
      const visibleIds = new Set(leads.map(l => l.id));
      setSelectedLeads(selectedLeads.filter(l => !visibleIds.has(l.id)));
      setSelectAllGlobal(false);
    }
  };

  const selectedCount = selectAllGlobal ? pagination.total : selectedLeads.length;

  const handleCheckMessengers = async () => {
    if (selectedCount === 0) return;
    setIsCheckingMessengers(true);
    try {
      const payload = selectAllGlobal 
        ? { select_all: true, filters } 
        : { lead_ids: selectedLeads.map(l => l.id) };
      await checkMessengers(payload);
      onRefresh(); // Refresh table
      setSelectedLeads([]);
      setSelectAllGlobal(false);
    } catch (err) {
      console.error(err);
      alert('Failed to check messengers');
    } finally {
      setIsCheckingMessengers(false);
    }
  };

  const handleOutreachSync = async () => {
    if (selectedCount === 0) return;
    setIsSyncing(true);
    try {
      const payload = selectAllGlobal 
        ? { select_all: true, filters } 
        : { lead_ids: selectedLeads.map(l => l.id) };
      const res = await exportLeadRadar(payload);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `lead_radar_sync_${new Date().getTime()}.json`;
      a.click();
    } catch (err) {
      console.error(err);
      alert('Failed to sync to Lead Radar');
    } finally {
      setIsSyncing(false);
    }
  };

  const allVisibleSelected = leads.length > 0 && leads.every(lead => selectedLeads.find(l => l.id === lead.id));

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 backdrop-blur-md space-y-4">
      
      {/* Filters & Export Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search leads by name, city, website..."
            value={filters.search || ''}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {selectedLeads.length > 0 && (
            <>
              <button
                onClick={() => setDryRunModalOpen(true)}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 text-xs font-semibold border border-emerald-500/30 transition-all"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Dry Run AI ({selectedLeads.length})</span>
              </button>
              
              <button
                onClick={async () => {
                  try {
                    const API_BASE = window.location.hostname.includes('vercel.app') 
                      ? 'https://web-production-c4d98.up.railway.app/api/v1' 
                      : '/api/v1';
                      
                    const payload = selectAllGlobal 
                      ? { select_all: true, filters } 
                      : { lead_ids: selectedLeads.map(l => l.id) };

                    const res = await fetch(`${API_BASE}/leads/tools/enrich`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload)
                    });
                    if (res.ok) {
                      setSelectedLeads([]);
                      if (onRefresh) onRefresh();
                    } else {
                      alert('Failed to start enrichment');
                    }
                  } catch (e) {
                    alert('Error triggering enrichment');
                  }
                }}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-400 text-xs font-semibold border border-purple-500/30 transition-all mr-2"
              >
                <Flame className="w-3.5 h-3.5" />
                <span>Deep AI Enrich ({selectedCount})</span>
              </button>

              <button
                onClick={async () => {
                  if (!window.confirm('Cancel enrichment for selected leads?')) return;
                  try {
                    const API_BASE = window.location.hostname.includes('vercel.app') 
                      ? 'https://web-production-c4d98.up.railway.app/api/v1' 
                      : '/api/v1';
                      
                    const payload = selectAllGlobal 
                      ? { select_all: true, filters } 
                      : { lead_ids: selectedLeads.map(l => l.id) };
                      
                    const res = await fetch(`${API_BASE}/leads/tools/reset_enrichment`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload)
                    });
                    if (res.ok) {
                      setSelectedLeads([]);
                      if (onRefresh) onRefresh();
                    } else {
                      alert('Failed to reset enrichment');
                    }
                  } catch (e) {
                    alert('Error cancelling enrichment');
                  }
                }}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 text-xs font-semibold border border-rose-500/30 transition-all mr-2"
              >
                <XOctagon className="w-3.5 h-3.5" />
                <span>Cancel Enrich</span>
              </button>
            </>
          )}

          <select
            value={filters.city || ''}
            onChange={(e) => setFilters({ ...filters, city: e.target.value, page: 1, page_size: e.target.value ? 500 : 50 })}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All GEOs</option>
            <option value="Dubai">Dubai {filters.city === 'Dubai' ? `(${pagination.total})` : ''}</option>
            <option value="Kyiv">Kyiv {filters.city === 'Kyiv' ? `(${pagination.total})` : ''}</option>
            <option value="Almaty">Almaty {filters.city === 'Almaty' ? `(${pagination.total})` : ''}</option>
          </select>

          <select
            value={filters.min_score || ''}
            onChange={(e) => setFilters({ ...filters, min_score: e.target.value, page: 1, page_size: e.target.value ? 500 : 50 })}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">Any Revo Score</option>
            <option value="80">80+ (High Potential) {filters.min_score === '80' ? `(${pagination.total})` : ''}</option>
            <option value="50">50+ (Medium Potential) {filters.min_score === '50' ? `(${pagination.total})` : ''}</option>
          </select>

          <select
            value={filters.enrichment_status || ''}
            onChange={(e) => setFilters({ ...filters, enrichment_status: e.target.value, page: 1, page_size: e.target.value ? 500 : 50 })}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">Any AI Status</option>
            <option value="none">Not Enriched Yet {filters.enrichment_status === 'none' ? `(${pagination.total})` : ''}</option>
            <option value="in_progress">AI Enriching... {filters.enrichment_status === 'in_progress' ? `(${pagination.total})` : ''}</option>
            <option value="completed">AI Done {filters.enrichment_status === 'completed' ? `(${pagination.total})` : ''}</option>
            <option value="failed">AI Failed {filters.enrichment_status === 'failed' ? `(${pagination.total})` : ''}</option>
          </select>

          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl px-2 py-1 text-xs text-slate-300">
            <Star className="w-3.5 h-3.5 text-amber-500 mr-2" />
            <input 
              type="number" 
              step="0.1" 
              min="0" 
              max="5"
              placeholder="Min" 
              value={filters.min_rating || ''} 
              onChange={(e) => setFilters({ ...filters, min_rating: e.target.value })}
              className="bg-transparent border-none w-12 focus:outline-none text-center"
            />
            <span className="text-slate-600 mx-1">-</span>
            <input 
              type="number" 
              step="0.1" 
              min="0" 
              max="5"
              placeholder="Max" 
              value={filters.max_rating || ''} 
              onChange={(e) => setFilters({ ...filters, max_rating: e.target.value })}
              className="bg-transparent border-none w-12 focus:outline-none text-center"
            />
          </div>

          <button
            onClick={handleOutreachSync}
            disabled={isSyncing || selectedCount === 0}
            className={`flex items-center px-4 py-2 text-xs font-semibold rounded-xl border transition-all ml-auto ${
              isSyncing || selectedCount === 0
                ? 'bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-emerald-600/20 border-emerald-500/50 text-emerald-400 hover:bg-emerald-500 hover:text-white shadow-[0_0_15px_-3px_rgba(16,185,129,0.3)] hover:shadow-[0_0_20px_-3px_rgba(16,185,129,0.6)]'
            }`}
          >
            <Send className={`w-4 h-4 mr-1.5 ${isSyncing ? 'animate-pulse' : ''}`} />
            <span>{isSyncing ? 'Syncing...' : 'Outreach Sync'}</span>
          </button>

          <button
            onClick={handleCheckMessengers}
            disabled={isCheckingMessengers || selectedCount === 0}
            className={`flex items-center px-4 py-2 text-xs font-semibold rounded-xl border transition-all ml-auto ${
              isCheckingMessengers || selectedCount === 0
                ? 'bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-indigo-600/20 border-indigo-500/50 text-indigo-400 hover:bg-indigo-500 hover:text-white shadow-[0_0_15px_-3px_rgba(99,102,241,0.3)] hover:shadow-[0_0_20px_-3px_rgba(99,102,241,0.6)]'
            }`}
          >
            <MessageCircle className={`w-4 h-4 mr-1.5 ${isCheckingMessengers ? 'animate-pulse' : ''}`} />
            <span>{isCheckingMessengers ? 'Checking...' : 'Check Messengers'}</span>
          </button>

          <button
            onClick={() => setCrmModalOpen(true)}
            disabled={leads.length === 0}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold border border-blue-500 transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50"
          >
            <Cloud className="w-3.5 h-3.5" />
            <span>CRM Sync</span>
          </button>

          <button
            onClick={handleExportCSV}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Smart Selection Banner */}
      {selectedLeads.length > 0 && selectedLeads.length === leads.length && pagination.total > leads.length && (
        <div className="bg-blue-900/40 border border-blue-500/30 rounded-xl p-3 text-sm text-center flex items-center justify-center space-x-2">
          {!selectAllGlobal ? (
            <>
              <span className="text-blue-200">Все <strong>{selectedLeads.length}</strong> загруженных лидов на странице выделены.</span>
              <button 
                onClick={() => setSelectAllGlobal(true)}
                className="text-blue-400 font-bold hover:underline"
              >
                Выделить все {pagination.total} лидов, подходящих под фильтр
              </button>
            </>
          ) : (
            <>
              <span className="text-blue-200">Все <strong>{pagination.total}</strong> лидов по этому фильтру выделены.</span>
              <button 
                onClick={() => {
                  setSelectAllGlobal(false);
                  setSelectedLeads([]);
                }}
                className="text-blue-400 font-bold hover:underline"
              >
                Снять выделение
              </button>
            </>
          )}
        </div>
      )}

      {/* Data Table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-4 w-10">
                <input 
                  type="checkbox" 
                  checked={allVisibleSelected}
                  onChange={toggleSelectAll}
                  className="rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-950"
                  title="Select/Deselect All Visible Leads"
                />
              </th>
              <th className="py-3 px-4 cursor-pointer hover:bg-slate-800/50 group transition-colors select-none" onClick={() => handleSort('company_name')}>
                Company Name {getSortIcon('company_name')}
              </th>
              <th className="py-3 px-4 cursor-pointer hover:bg-slate-800/50 group transition-colors select-none" onClick={() => handleSort('business_type')}>
                Type / Niche {getSortIcon('business_type')}
              </th>
              <th className="py-3 px-4 cursor-pointer hover:bg-slate-800/50 group transition-colors select-none" onClick={() => handleSort('city')}>
                GEO / Address {getSortIcon('city')}
              </th>
              <th className="py-3 px-4 cursor-pointer hover:bg-slate-800/50 group transition-colors select-none" onClick={() => handleSort('rating')}>
                Rating {getSortIcon('rating')}
              </th>
              <th className="py-3 px-4 cursor-pointer hover:bg-slate-800/50 group transition-colors select-none" onClick={() => handleSort('revo_score')}>
                Revo Score {getSortIcon('revo_score')}
              </th>
              <th className="py-3 px-4">Contacts Found</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
            {leads.length === 0 ? (
              <tr>
                <td colSpan="8" className="py-12 text-center text-slate-500">
                  No Master Data leads match current filters.
                </td>
              </tr>
            ) : (
              leads.map((lead) => {
                const hasWeb = !!lead.website;
                const phones = (lead.contacts || []).filter(c => c.contact_type === 'phone');
                const emails = (lead.contacts || []).filter(c => c.contact_type === 'email');
                const whatsapp = (lead.contacts || []).filter(c => c.contact_type === 'whatsapp');
                const isSelected = !!selectedLeads.find(l => l.id === lead.id);

                return (
                  <tr
                    key={lead.id}
                    onClick={() => onSelectLead(lead)}
                    className={`hover:bg-slate-800/60 cursor-pointer transition-colors group ${isSelected ? 'bg-slate-800/40' : ''}`}
                  >
                    <td className="py-3.5 px-4" onClick={(e) => e.stopPropagation()}>
                      <input 
                        type="checkbox" 
                        checked={isSelected}
                        onChange={(e) => toggleLeadSelection(lead, e)}
                        className="rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-900"
                      />
                    </td>
                    <td className="py-3.5 px-4 font-bold group-hover:text-blue-400">
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(lead.company_name + ' ' + (lead.city || ''))}`}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-white hover:text-blue-400 flex items-center space-x-1.5"
                        title="View on Google Maps"
                      >
                        <span className="truncate max-w-[150px] md:max-w-[250px] lg:max-w-[300px]" title={lead.company_name}>{lead.company_name}</span>
                        <MapPin className="w-3.5 h-3.5 text-blue-500/70 flex-shrink-0" />
                      </a>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <span className="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-[11px]">
                        {lead.business_type || 'N/A'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 truncate max-w-[120px] md:max-w-[180px]" title={lead.city}>
                      {lead.city || 'N/A'}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-1 text-amber-400">
                        <Star className="w-3.5 h-3.5 fill-amber-400" />
                        <span className="font-semibold text-white">{lead.rating || 'N/A'}</span>
                        <span className="text-slate-500 text-[10px]">({lead.reviews_count})</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-1.5">
                        <Flame className={`w-3.5 h-3.5 ${lead.revo_score >= 80 ? 'text-amber-400' : 'text-slate-500'}`} />
                        <span className={`font-extrabold px-2 py-0.5 rounded-lg text-[11px] ${
                          lead.revo_score >= 80 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                          lead.revo_score >= 50 ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                          'bg-slate-800 text-slate-400'
                        }`}>
                          {lead.revo_score}/100
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                        <div className="flex items-center space-x-2">
                          {phones.length > 0 && (
                            <a href={`tel:${phones[0].contact_value}`} onClick={(e) => e.stopPropagation()} className="hover:scale-110 transition-transform">
                              <Phone className="w-4 h-4 text-emerald-400 hover:text-emerald-300" title={`Phone: ${phones[0].contact_value}`} />
                            </a>
                          )}
                          {emails.length > 0 && (
                            <a href={`mailto:${emails[0].contact_value}`} onClick={(e) => e.stopPropagation()} className="hover:scale-110 transition-transform">
                              <Mail className="w-4 h-4 text-blue-400 hover:text-blue-300" title={`Email: ${emails[0].contact_value}`} />
                            </a>
                          )}
                          {lead.custom_data?.whatsapp_available && phones.length > 0 && (
                            <a href={`https://wa.me/${phones[0].contact_value.replace(/[^0-9]/g, '')}`} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} className="hover:scale-110 transition-transform">
                              <MessageCircle className="w-4 h-4 text-green-500 hover:text-green-400" title="Open in WhatsApp" />
                            </a>
                          )}
                          {lead.custom_data?.telegram_available && (
                            <button onClick={(e) => { e.stopPropagation(); alert('Telegram link stored in custom_data'); }} className="hover:scale-110 transition-transform">
                              <Send className="w-4 h-4 text-sky-400 hover:text-sky-300" title="Telegram available" />
                            </button>
                          )}
                          {hasWeb && (
                            <a href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} className="hover:scale-110 transition-transform">
                              <Globe className="w-4 h-4 text-purple-400 hover:text-purple-300" title="Visit Website" />
                            </a>
                          )}
                        </div>
                        
                        {lead.custom_data?.enrichment_status === 'in_progress' && (() => {
                          let logs = lead.custom_data.ai_logs || [];
                          if (!Array.isArray(logs)) logs = [logs];
                          const lastLog = typeof logs[logs.length - 1] === 'string' ? logs[logs.length - 1] : '';
                          let stepStr = 'Enriching...';
                          if (lastLog.includes('visiting')) stepStr = 'Scraping site...';
                          else if (lastLog.includes('analyzed')) stepStr = 'AI analyzing...';
                          else if (lastLog.includes('Checking messengers')) stepStr = 'Checking msgs...';
                          
                          return (
                            <span title={lastLog} className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse whitespace-nowrap">
                              {stepStr}
                            </span>
                          );
                        })()}
                        {lead.custom_data?.enrichment_status === 'completed' && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 whitespace-nowrap">AI Done</span>
                        )}
                        {lead.custom_data?.enrichment_status === 'failed' && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-500/20 text-red-400 border border-red-500/30 whitespace-nowrap">AI Failed</span>
                        )}
                        {lead.custom_data?.enrichment_status === 'no_website' && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-500/20 text-slate-400 border border-slate-500/30 whitespace-nowrap">No WWW</span>
                        )}
                        {lead.custom_data?.enrichment_status === 'social_only' && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-pink-500/20 text-pink-400 border border-pink-500/30 whitespace-nowrap">Social Only</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-3">
                        <button 
                          onClick={(e) => { e.stopPropagation(); setOutreachLead(lead); }}
                          className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 border border-blue-500/30 rounded-lg transition-colors group-hover:border-blue-500/60"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span className="text-[10px] font-bold">Draft Email</span>
                        </button>
                        <span className="text-slate-400 text-[11px] group-hover:text-white">
                          Inspect →
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between bg-slate-900/40 border border-slate-800 rounded-xl p-4 mt-4">
        <div className="flex items-center space-x-4">
          <div className="text-xs text-slate-400">
            Showing {leads.length > 0 ? (filters.page - 1) * filters.page_size + 1 : 0} to {Math.min(filters.page * filters.page_size, pagination.total)} of {pagination.total} leads
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500">Rows per page:</span>
            <select
              value={filters.page_size || 50}
              onChange={(e) => setFilters({ ...filters, page_size: parseInt(e.target.value), page: 1 })}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-300 focus:outline-none"
            >
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={500}>500</option>
            </select>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFilters({ ...filters, page: Math.max(1, filters.page - 1) })}
            disabled={filters.page <= 1}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-semibold text-white transition-colors"
          >
            Previous
          </button>
          <span className="text-xs text-slate-300 font-medium px-2">
            Page {filters.page} of {pagination.total_pages}
          </span>
          <button
            onClick={() => setFilters({ ...filters, page: Math.min(pagination.total_pages, filters.page + 1) })}
            disabled={filters.page >= pagination.total_pages}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-semibold text-white transition-colors"
          >
            Next
          </button>
        </div>
      </div>

      {dryRunModalOpen && (
        <DryRunModal 
          selectedLeads={selectedLeads} 
          onClose={() => setDryRunModalOpen(false)} 
        />
      )}

      {crmModalOpen && (
        <CRMExportModal 
          leads={leads}
          onClose={() => setCrmModalOpen(false)}
        />
      )}

      {outreachLead && (
        <OmnichannelOutreachModal 
          lead={outreachLead}
          onClose={() => setOutreachLead(null)}
        />
      )}

    </div>
  );
}
