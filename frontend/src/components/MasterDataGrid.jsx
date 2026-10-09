import React, { useState } from 'react';
import { Search, Download, Filter, Star, Globe, Phone, Mail, MessageSquare, ExternalLink, Flame, Play, Cloud } from 'lucide-react';
import { getExportCsvUrl } from '../services/api';
import DryRunModal from './DryRunModal';
import CRMExportModal from './CRMExportModal';

export default function MasterDataGrid({ leads = [], onSelectLead, filters, setFilters, onRefresh, pagination = { total: 0, total_pages: 1, page: 1 } }) {
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [dryRunModalOpen, setDryRunModalOpen] = useState(false);
  const [crmModalOpen, setCrmModalOpen] = useState(false);

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
    if (selectedLeads.find(l => l.id === lead.id)) {
      setSelectedLeads(selectedLeads.filter(l => l.id !== lead.id));
    } else {
      setSelectedLeads([...selectedLeads, lead]);
    }
  };

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
            <button
              onClick={() => setDryRunModalOpen(true)}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 text-xs font-semibold border border-emerald-500/30 transition-all mr-2"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Dry Run AI ({selectedLeads.length})</span>
            </button>
          )}

          <select
            value={filters.city || ''}
            onChange={(e) => setFilters({ ...filters, city: e.target.value })}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All GEOs</option>
            <option value="Dubai">Dubai</option>
            <option value="Kyiv">Kyiv</option>
            <option value="Almaty">Almaty</option>
          </select>

          <select
            value={filters.min_score || ''}
            onChange={(e) => setFilters({ ...filters, min_score: e.target.value })}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">Any Revo Score</option>
            <option value="80">80+ (High Potential)</option>
            <option value="50">50+ (Medium Potential)</option>
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
            onClick={() => setCrmModalOpen(true)}
            disabled={leads.length === 0}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold border border-blue-500 transition-all ml-auto shadow-lg shadow-blue-500/20 disabled:opacity-50"
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

      {/* Data Table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-4 w-10"></th>
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
                    <td className="py-3.5 px-4 font-bold text-white group-hover:text-blue-400">
                      {lead.company_name}
                      {hasWeb && (
                        <a
                          href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-block ml-2 text-slate-500 hover:text-blue-400"
                        >
                          <ExternalLink className="w-3 h-3 inline" />
                        </a>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <span className="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-[11px]">
                        {lead.business_type || 'N/A'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 truncate max-w-xs">
                      {lead.city || ''} {lead.address ? `• ${lead.address}` : ''}
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
                      <div className="flex items-center space-x-2">
                        {phones.length > 0 && <Phone className="w-3.5 h-3.5 text-emerald-400" title="Phone available" />}
                        {emails.length > 0 && <Mail className="w-3.5 h-3.5 text-blue-400" title="Email available" />}
                        {whatsapp.length > 0 && <MessageSquare className="w-3.5 h-3.5 text-teal-400" title="WhatsApp available" />}
                        {hasWeb && <Globe className="w-3.5 h-3.5 text-purple-400" title="Website available" />}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-400 text-[11px] group-hover:text-white">
                      Inspect →
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
        <div className="text-xs text-slate-400">
          Showing {leads.length > 0 ? (pagination.page - 1) * filters.page_size + 1 : 0} to {Math.min(pagination.page * filters.page_size, pagination.total)} of {pagination.total} leads
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFilters({ ...filters, page: Math.max(1, pagination.page - 1) })}
            disabled={pagination.page <= 1}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-semibold text-white transition-colors"
          >
            Previous
          </button>
          <span className="text-xs text-slate-300 font-medium px-2">
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <button
            onClick={() => setFilters({ ...filters, page: Math.min(pagination.total_pages, pagination.page + 1) })}
            disabled={pagination.page >= pagination.total_pages}
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

    </div>
  );
}
