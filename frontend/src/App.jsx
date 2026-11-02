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
import AnalyticsDashboard from './components/AnalyticsDashboard';
import UserManagementDashboard from './components/UserManagementDashboard';
import AudiencesHub from './components/AudiencesHub';
import ProductsHub from './components/ProductsHub';
import FunnelStudio from './components/FunnelStudio';
import CreateProjectModal from './components/CreateProjectModal';
import ReviewQueue from './components/ReviewQueue';
import InboxHub from './components/InboxHub';
import CampaignLaunchModal from './components/CampaignLaunchModal';
import { fetchLeads, fetchCampaigns, fetchStats, fetchProjects, deleteProject } from './services/api';

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch (e) {
      return null;
    }
  });

  // Projects state
  const [projects, setProjects] = useState([]);
  const [currentProjectId, setCurrentProjectId] = useState(() => {
    return localStorage.getItem('current_project_id') || '';
  });
  const [isCreateProjectModalOpen, setIsCreateProjectModalOpen] = useState(false);
  const [isLaunchModalOpen, setIsLaunchModalOpen] = useState(false);
  const [launchModalPreset, setLaunchModalPreset] = useState(null);
  const [selectedAudienceId, setSelectedAudienceId] = useState('');
  const [activeProductIdForFunnel, setActiveProductIdForFunnel] = useState(null);

  const [activeTab, setActiveTab] = useState('audiences'); // default to 'audiences' hub in multi-project flow
  const [isAIModalOpen, setIsAIModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);

  const [globalCampaignId, setGlobalCampaignId] = useState('');

  const [leads, setLeads] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [stats, setStats] = useState({ total: 0, whatsapp: 0, telegram: 0, viber: 0, email: 0, phone: 0 });
  const [filters, setFilters] = useState({ 
    city: '', min_score: '', min_rating: '', max_rating: '', search: '', 
    sort_by: 'created_at', sort_order: 'desc', page_size: 50, page: 1, 
    has_whatsapp: '', has_telegram: '', has_viber: '', has_email: '', has_phone: '' 
  });
  const [pagination, setPagination] = useState({ total: 0, total_pages: 1 });

  const handleApiError = (err) => {
    console.warn('Background data fetch notice:', err);
    if (err?.message?.includes('Signature has expired') || err?.message?.includes('Could not validate credentials')) {
      console.warn('Expired auth token detected. Clearing expired session.');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
    }
  };

  useEffect(() => {
    const onAuthExpired = () => {
      console.warn('auth:expired event triggered. Resetting session.');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
    };
    window.addEventListener('auth:expired', onAuthExpired);
    return () => window.removeEventListener('auth:expired', onAuthExpired);
  }, []);

  const loadProjects = async () => {
    if (!user) return;
    try {
      const projs = await fetchProjects();
      const list = projs || [];
      setProjects(list);
      if (list.length > 0) {
        const currentSaved = localStorage.getItem('current_project_id');
        const exists = list.find(p => p.id === currentSaved || p.id === currentProjectId);
        const targetId = exists ? exists.id : ((list.find(p => p.is_default) || list[0]).id);
        setCurrentProjectId(targetId);
        localStorage.setItem('current_project_id', targetId);
      }
    } catch (err) {
      handleApiError(err);
    }
  };

  // Ensure currentProjectId is synchronized with available projects
  useEffect(() => {
    if (projects.length > 0) {
      const exists = projects.find(p => p.id === currentProjectId);
      if (!exists) {
        const defaultProj = projects.find(p => p.is_default) || projects[0];
        setCurrentProjectId(defaultProj.id);
        localStorage.setItem('current_project_id', defaultProj.id);
      }
    }
  }, [projects, currentProjectId]);

  const handleProjectChange = (newProjId) => {
    setCurrentProjectId(newProjId);
    setSelectedAudienceId('');
    localStorage.setItem('current_project_id', newProjId);
  };

  const handleDeleteProject = async (projectId) => {
    try {
      await deleteProject(projectId);
      const updated = projects.filter(p => p.id !== projectId);
      setProjects(updated);
      if (currentProjectId === projectId) {
        const nextProj = updated.find(p => p.is_default) || updated[0];
        if (nextProj) {
          handleProjectChange(nextProj.id);
        }
      }
      return true;
    } catch (err) {
      handleApiError(err);
      throw err;
    }
  };

  const loadLeads = async () => {
    if (!user) return;
    try {
      const fetchFilters = { ...filters };
      if (globalCampaignId) fetchFilters.campaign_id = globalCampaignId;
      if (currentProjectId) fetchFilters.project_id = currentProjectId;
      if (selectedAudienceId) fetchFilters.audience_id = selectedAudienceId;

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

  const [isGlobalScope, setIsGlobalScope] = useState(false);

  const loadStats = async (globalOverride) => {
    if (!user) return;
    try {
      const targetGlobal = globalOverride !== undefined ? globalOverride : isGlobalScope;
      const targetProjId = targetGlobal ? null : (currentProjectId || null);
      const targetAudId = targetGlobal ? null : (selectedAudienceId || null);
      const data = await fetchStats(targetProjId, targetAudId);
      setStats(data || { total: 0, whatsapp: 0, telegram: 0, viber: 0, email: 0, phone: 0 });
    } catch (err) {
      handleApiError(err);
    }
  };

  useEffect(() => {
    loadProjects();
    loadCampaigns();
    loadStats();
  }, [user]);

  useEffect(() => {
    loadLeads();
    loadStats();

    // Auto-refresh (polling) for real-time updates
    const intervalId = setInterval(() => {
      loadLeads();
      loadStats();
      if (projects.length === 0) {
        loadProjects();
      }
    }, 6000);

    return () => clearInterval(intervalId);
  }, [filters, globalCampaignId, currentProjectId, selectedAudienceId, projects.length, isGlobalScope]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('current_project_id');
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
      
      {/* Header Navigation with Project Switcher */}
      <Header
        onOpenAIStrategist={() => setIsAIModalOpen(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        campaigns={campaigns}
        globalCampaignId={globalCampaignId}
        setGlobalCampaignId={setGlobalCampaignId}
        user={user}
        onLogout={handleLogout}
        projects={projects}
        currentProjectId={currentProjectId}
        setCurrentProjectId={handleProjectChange}
        onOpenCreateProject={() => setIsCreateProjectModalOpen(true)}
        onDeleteProject={handleDeleteProject}
      />

      {/* Main Content Area */}
      <main className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">
        
        {/* KPI Cards */}
        <StatsCards 
          stats={stats}
          campaignsCount={campaigns.length}
          filters={filters}
          setFilters={setFilters}
          currentProject={projects.find(p => p.id === currentProjectId) || projects[0]}
          isGlobalScope={isGlobalScope}
          setIsGlobalScope={(val) => {
            setIsGlobalScope(val);
            loadStats(val);
          }}
        />

        {/* Tab Views */}
        {activeTab === 'audiences' && (
          <AudiencesHub
            currentProjectId={currentProjectId}
            projects={projects}
            onViewLeadsInTable={(audId) => {
              setSelectedAudienceId(audId);
              setActiveTab('leads');
            }}
            onOpenScraper={() => setActiveTab('builder')}
          />
        )}

        {activeTab === 'products' && (
          <ProductsHub
            currentProjectId={currentProjectId}
            projects={projects}
            onLaunchFunnelStudio={(prodId) => {
              setActiveProductIdForFunnel(prodId);
              setActiveTab('funnel');
            }}
          />
        )}

        {activeTab === 'funnel' && (
          <FunnelStudio
            currentProjectId={currentProjectId}
            initialProductId={activeProductIdForFunnel}
            onLaunchCampaignWithFunnel={(funnelData) => {
              setLaunchModalPreset(funnelData);
              setIsLaunchModalOpen(true);
            }}
          />
        )}

        {activeTab === 'review' && (
          <ReviewQueue currentProjectId={currentProjectId} />
        )}

        {activeTab === 'inbox' && (
          <InboxHub currentProjectId={currentProjectId} />
        )}

        {activeTab === 'leads' && (
          <div className="space-y-4">
            {selectedAudienceId && (
              <div className="flex items-center justify-between p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-xs text-indigo-300">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold">Фильтр по аудитории активен</span>
                </div>
                <button
                  onClick={() => setSelectedAudienceId('')}
                  className="px-2.5 py-1 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 font-medium transition-colors text-white text-[11px]"
                >
                  Сбросить фильтр аудитории
                </button>
              </div>
            )}
            <MasterDataGrid
              leads={leads}
              onSelectLead={(lead) => setSelectedLead(lead)}
              filters={filters}
              setFilters={setFilters}
              onRefresh={() => { loadLeads(); loadStats(); }}
              pagination={pagination}
            />
          </div>
        )}

        {activeTab === 'builder' && (
          <TaskBuilder
            onCampaignCreated={() => { loadCampaigns(); loadLeads(); }}
            onOpenAIStrategist={() => setIsAIModalOpen(true)}
            campaigns={campaigns}
            currentProjectId={currentProjectId}
            selectedAudienceId={selectedAudienceId}
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
          <AnalyticsDashboard 
            currentProjectId={currentProjectId} 
            projects={projects}
            globalCampaignId={globalCampaignId} 
          />
        )}
        {activeTab === 'users' && user?.role === 'SUPER_ADMIN' && (
          <UserManagementDashboard />
        )}

      </main>

      {/* Modals */}
      <CreateProjectModal
        isOpen={isCreateProjectModalOpen}
        onClose={() => setIsCreateProjectModalOpen(false)}
        onProjectCreated={(newProj) => {
          setProjects(prev => [newProj, ...prev]);
          handleProjectChange(newProj.id);
        }}
      />

      <CampaignLaunchModal
        isOpen={isLaunchModalOpen}
        onClose={() => setIsLaunchModalOpen(false)}
        currentProjectId={currentProjectId}
        presetData={launchModalPreset}
        onCampaignLaunched={(campaign) => {
          setIsLaunchModalOpen(false);
          if (campaign?.is_manual_review_required) {
            setActiveTab('review');
          } else {
            setActiveTab('outreach');
          }
        }}
      />

      {/* AI Strategist Co-pilot Modal */}
      <AIStrategistModal
        isOpen={isAIModalOpen}
        onClose={() => setIsAIModalOpen(false)}
        onCampaignCreated={() => { loadCampaigns(); loadLeads(); }}
        currentProjectId={currentProjectId}
        selectedAudienceId={selectedAudienceId}
      />

      {/* Lead Detail Slide-out Drawer */}
      <LeadDrawer
        lead={selectedLead}
        onClose={() => setSelectedLead(null)}
      />

    </div>
  );
}
