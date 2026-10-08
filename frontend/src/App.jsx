import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import StatsCards from './components/StatsCards';
import MasterDataGrid from './components/MasterDataGrid';
import TaskBuilder from './components/TaskBuilder';
import AIStrategistModal from './components/AIStrategistModal';
import LeadDrawer from './components/LeadDrawer';
import MergeCenter from './components/MergeCenter';
import AdminPanel from './components/AdminPanel';
import { fetchLeads, fetchCampaigns } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('leads'); // 'leads' or 'builder'
  const [isAIModalOpen, setIsAIModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);

  const [leads, setLeads] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [filters, setFilters] = useState({ city: '', min_score: '', search: '' });

  const loadLeads = async () => {
    try {
      const data = await fetchLeads(filters);
      setLeads(data.items || []);
    } catch (err) {
      console.error('Error fetching leads:', err);
    }
  };

  const loadCampaigns = async () => {
    try {
      const data = await fetchCampaigns();
      setCampaigns(data || []);
    } catch (err) {
      console.error('Error fetching campaigns:', err);
    }
  };

  useEffect(() => {
    loadLeads();
    loadCampaigns();
  }, [filters]);

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans flex flex-col">
      
      {/* Header Navigation */}
      <Header
        onOpenAIStrategist={() => setIsAIModalOpen(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">
        
        {/* KPI Cards */}
        <StatsCards leadsCount={leads.length} campaignsCount={campaigns.length} />

        {/* Tab Views */}
        {activeTab === 'leads' && (
          <MasterDataGrid
            leads={leads}
            onSelectLead={(lead) => setSelectedLead(lead)}
            filters={filters}
            setFilters={setFilters}
            onRefresh={loadLeads}
          />
        )}
        {activeTab === 'builder' && (
          <TaskBuilder
            onCampaignCreated={() => { loadCampaigns(); loadLeads(); }}
            onOpenAIStrategist={() => setIsAIModalOpen(true)}
            campaigns={campaigns}
          />
        )}
        {activeTab === 'merge' && (
          <MergeCenter />
        )}
        {activeTab === 'admin' && (
          <AdminPanel />
        )}

      </main>

      {/* AI Strategist Co-pilot Modal */}
      <AIStrategistModal
        isOpen={isAIModalOpen}
        onClose={() => setIsAIModalOpen(false)}
        onCampaignCreated={() => { loadCampaigns(); loadLeads(); }}
      />

      {/* Lead Detail Slide-out Drawer */}
      <LeadDrawer
        lead={selectedLead}
        onClose={() => setSelectedLead(null)}
      />

    </div>
  );
}
