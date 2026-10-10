import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import StatsCards from './components/StatsCards';
import MasterDataGrid from './components/MasterDataGrid';
import TaskBuilder from './components/TaskBuilder';
import AIStrategistModal from './components/AIStrategistModal';
import LeadDrawer from './components/LeadDrawer';
import MergeCenter from './components/MergeCenter';
import AdminPanel from './components/AdminPanel';
import OutreachBuilder from './components/OutreachBuilder';
import PromoTrack from './components/PromoTrack';
import AdminLoginModal from './components/AdminLoginModal';
import { fetchLeads, fetchCampaigns, fetchStats } from './services/api';

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch (e) {
      return null;
    }
  });
  const [activeTab, setActiveTab] = useState('leads'); // 'leads' or 'builder'
  const [isAIModalOpen, setIsAIModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);

  const [globalCampaignId, setGlobalCampaignId] = useState('');

  const [leads, setLeads] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [stats, setStats] = useState({ total: 0, whatsapp: 0, telegram: 0, viber: 0, email: 0, phone: 0 });
  const [filters, setFilters] = useState({ city: '', min_score: '', min_rating: '', max_rating: '', search: '', sort_by: 'created_at', sort_order: 'desc', page_size: 50, page: 1, has_whatsapp: '', has_telegram: '', has_viber: '', has_email: '', has_phone: '' });
  const [pagination, setPagination] = useState({ total: 0, total_pages: 1 });

  const handleApiError = (err) => {
    console.error('API call error:', err);
    if (err?.message?.includes('401') || err?.message?.includes('Unauthorized') || err?.message?.includes('Invalid token')) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
    }
  };

  const loadLeads = async () => {
    if (!user) return;
    try {
      const fetchFilters = { ...filters };
      if (globalCampaignId) fetchFilters.campaign_id = globalCampaignId;
      const data = await fetchLeads(fetchFilters);
      setLeads(data.items || []);
      setPagination({ total: data.total || 0, total_pages: data.total_pages || 1 });
    } catch (err) {
      handleApiError(err);
    }
  };

  const loadCampaigns = async () => {
    if (!user) return;
    try {
      const data = await fetchCampaigns();
      setCampaigns(data || []);
    } catch (err) {
      handleApiError(err);
    }
  };

  const loadStats = async () => {
    if (!user) return;
    try {
      const data = await fetchStats();
      setStats(data || { total: 0, whatsapp: 0, telegram: 0, viber: 0, email: 0, phone: 0 });
    } catch (err) {
      handleApiError(err);
    }
  };


  useEffect(() => {
    loadLeads();

    // Auto-refresh (polling) for real-time AI Queue updates
    const intervalId = setInterval(() => {
      loadLeads();
      loadStats();
    }, 5000);

    return () => clearInterval(intervalId);
  }, [filters, globalCampaignId]);

  useEffect(() => {
    loadCampaigns();
    loadStats();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans flex items-center justify-center">
        <AdminLoginModal onLoginSuccess={(loggedInUser) => setUser(loggedInUser)} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans flex flex-col">
      
      {/* Header Navigation */}
      <Header
        onOpenAIStrategist={() => setIsAIModalOpen(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        campaigns={campaigns}
        globalCampaignId={globalCampaignId}
        setGlobalCampaignId={setGlobalCampaignId}
        user={user}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">
        
        {/* KPI Cards */}
        <StatsCards 
          stats={stats}
          campaignsCount={campaigns.length}
          filters={filters}
          setFilters={setFilters}
        />

        {/* Tab Views */}
        {activeTab === 'leads' && (
          <MasterDataGrid
            leads={leads}
            onSelectLead={(lead) => setSelectedLead(lead)}
            filters={filters}
            setFilters={setFilters}
            onRefresh={() => { loadLeads(); loadStats(); }}
            pagination={pagination}
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
          <MergeCenter globalCampaignId={globalCampaignId} />
        )}
        {activeTab === 'admin' && (
          <AdminPanel />
        )}
        {activeTab === 'outreach' && (
          <OutreachBuilder 
            globalCampaignId={globalCampaignId} 
          />
        )}
        {activeTab === 'promotrack' && (
          <PromoTrack 
            onSelectLead={(lead) => setSelectedLead(lead)} 
          />
        )}
        {activeTab === 'analytics' && (
          <AnalyticsDashboard globalCampaignId={globalCampaignId} />
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
