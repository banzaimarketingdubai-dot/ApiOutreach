import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, Sparkles, Database, Layers, Wallet, CheckCircle2, GitMerge, 
  Send, Target, BarChart2, Shield, Users, Briefcase, Plus,
  Package, ShieldCheck, Inbox, ChevronDown, Check, Loader2,
  Trash2, AlertTriangle
} from 'lucide-react';
import { fetchApifyBalance } from '../services/api';

export default function Header({ 
  onOpenAIStrategist, 
  activeTab, 
  setActiveTab, 
  campaigns = [], 
  globalCampaignId, 
  setGlobalCampaignId, 
  user, 
  onLogout,
  projects = [],
  currentProjectId,
  setCurrentProjectId,
  onOpenCreateProject,
  onDeleteProject
}) {
  const [apifyData, setApifyData] = useState(null);
  const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  const dropdownRef = useRef(null);

  const handleConfirmDelete = async () => {
    if (!projectToDelete || !onDeleteProject) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await onDeleteProject(projectToDelete.id);
      setProjectToDelete(null);
      setIsProjectDropdownOpen(false);
    } catch (err) {
      setDeleteError(err.message || 'Ошибка удаления проекта');
    } finally {
      setIsDeleting(false);
    }
  };

  useEffect(() => {
    fetchApifyBalance()
      .then((data) => setApifyData(data))
      .catch((err) => console.error('Apify balance fetch error:', err));
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsProjectDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const currentProject = projects.find(p => p.id === currentProjectId) || projects[0];

  return (
    <header className="border-b border-slate-800 bg-[#0c121e]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-[1440px] mx-auto px-3 sm:px-6 h-16 flex items-center justify-between gap-3">
        
        {/* Brand & Project Workspace Selector */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          <div className="flex items-center space-x-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20 ring-1 ring-white/20 flex-shrink-0">
              <Database className="w-4 h-4 text-white" />
            </div>
            <div className="hidden sm:flex flex-col justify-center">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent leading-none mb-0.5">
                REVO
              </span>
              <p className="text-[9px] text-slate-400 leading-none">B2B Outreach OS</p>
            </div>
          </div>
          
          <div className="hidden md:block h-6 w-px bg-slate-800"></div>

          {/* Custom Project Workspace Dropdown with High Contrast */}
          <div className="relative" ref={dropdownRef}>
            <div className="flex items-center space-x-1 bg-slate-900 border border-slate-700/80 hover:border-slate-600 rounded-xl px-2 py-1 transition-all shadow-md">
              <button
                type="button"
                onClick={() => setIsProjectDropdownOpen(!isProjectDropdownOpen)}
                className="flex items-center space-x-1.5 text-left focus:outline-none cursor-pointer py-0.5"
                title="Переключить проект"
              >
                <Briefcase className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                <span className="text-xs font-bold text-white max-w-[110px] sm:max-w-[150px] truncate">
                  {currentProject ? currentProject.name : (projects.length === 0 ? 'Загрузка...' : 'Выберите проект')}
                </span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isProjectDropdownOpen ? 'rotate-180 text-white' : ''}`} />
              </button>

              {onOpenCreateProject && (
                <button
                  type="button"
                  onClick={onOpenCreateProject}
                  title="Создать новый проект"
                  className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors ml-0.5 border-l border-slate-800 pl-1.5"
                >
                  <Plus className="w-3.5 h-3.5 text-indigo-300" />
                </button>
              )}
            </div>

            {/* Custom High-Contrast Dropdown Menu */}
            {isProjectDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-64 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl z-50 p-2 space-y-1 backdrop-blur-xl animate-fade-in">
                <div className="px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 mb-1 flex items-center justify-between">
                  <span>Проекты (Воркспейсы)</span>
                  <span className="text-slate-500 font-mono">{projects.length}</span>
                </div>

                {projects.length === 0 ? (
                  <div className="px-3 py-4 text-center text-xs text-slate-300 flex items-center justify-center space-x-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                    <span>Загрузка проектов...</span>
                  </div>
                ) : (
                  <div className="max-h-60 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                    {projects.map(p => {
                      const isSelected = p.id === (currentProject?.id);
                      return (
                        <div
                          key={p.id}
                          className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-all group ${
                            isSelected
                              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                              : 'text-slate-100 hover:bg-slate-800/80 hover:text-white'
                          }`}
                        >
                          <button
                            type="button"
                            onClick={() => {
                              setCurrentProjectId(p.id);
                              setIsProjectDropdownOpen(false);
                            }}
                            className="flex-1 flex items-center space-x-2 truncate text-left cursor-pointer py-0.5"
                          >
                            <span className="truncate">{p.name}</span>
                            {p.is_default && (
                              <span className={`text-[9px] px-1.5 py-0.5 rounded border flex-shrink-0 ${
                                isSelected 
                                  ? 'bg-white/20 text-white border-white/30' 
                                  : 'bg-indigo-500/20 text-indigo-200 border-indigo-500/30'
                              }`}>
                                Основной
                              </span>
                            )}
                          </button>

                          <div className="flex items-center space-x-1 flex-shrink-0 ml-1.5">
                            {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                            {!p.is_default && onDeleteProject && (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setProjectToDelete(p);
                                }}
                                title="Удалить проект"
                                className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-slate-400 hover:text-rose-300 hover:bg-rose-500/20 transition-all cursor-pointer"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {onOpenCreateProject && (
                  <div className="pt-1.5 border-t border-slate-800 mt-1">
                    <button
                      type="button"
                      onClick={() => {
                        setIsProjectDropdownOpen(false);
                        onOpenCreateProject();
                      }}
                      className="w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-semibold text-indigo-300 hover:bg-indigo-500/10 hover:text-indigo-200 transition-colors cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Создать новый проект</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Center: Scrollable Nav Tabs */}
        <div className="flex-1 flex overflow-x-auto hide-scrollbar [scrollbar-width:none] px-1 mask-linear-fade">
          <nav className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800 flex-shrink-0 mx-auto space-x-1">
            
            {/* NEW: Audiences Tab */}
            <button
              onClick={() => setActiveTab('audiences')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'audiences'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Аудитории</span>
            </button>

            {/* NEW: Products Tab */}
            <button
              onClick={() => setActiveTab('products')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'products'
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Package className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Продукты</span>
            </button>

            {/* NEW: AI Funnel Studio Tab */}
            <button
              onClick={() => setActiveTab('funnel')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'funnel'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span className="hidden lg:inline">AI Воронка</span>
            </button>

            {/* NEW: Manual Review Queue Tab */}
            <button
              onClick={() => setActiveTab('review')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'review'
                  ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5 text-amber-300" />
              <span className="hidden lg:inline">Модерация</span>
            </button>

            {/* NEW: Smart Inbox Tab */}
            <button
              onClick={() => setActiveTab('inbox')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'inbox'
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Inbox className="w-3.5 h-3.5 text-emerald-300" />
              <span className="hidden lg:inline">Smart Inbox</span>
            </button>

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

        {/* Right: Actions & Profile */}
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

      {/* Delete Project Confirmation Modal */}
      {projectToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0f172a] border border-rose-500/30 rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <div className="flex items-center space-x-3">
              <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Удалить проект?</h3>
                <p className="text-xs text-slate-400">Это действие невозможно отменить</p>
              </div>
            </div>

            <p className="text-sm text-slate-300">
              Вы действительно хотите удалить проект <span className="font-bold text-white">«{projectToDelete.name}»</span>?
              Все связанные с ним базы лидов, продукты и кампании будут также удалены.
            </p>

            {deleteError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {deleteError}
              </div>
            )}

            <div className="flex items-center justify-end space-x-3 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => {
                  setProjectToDelete(null);
                  setDeleteError(null);
                }}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
              >
                Отмена
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 transition-all cursor-pointer"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Удаление...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Удалить проект</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
