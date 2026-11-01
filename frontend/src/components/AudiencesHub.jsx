import React, { useState, useEffect } from 'react';
import { 
  Users, Plus, Upload, Sparkles, Database, Mail, Phone, 
  Trash2, RefreshCw, CheckCircle2, AlertCircle, ArrowUpRight, 
  Layers, Filter, FileText, Activity, Play
} from 'lucide-react';
import { 
  fetchAudiences, deleteAudience, enrichAudience, recalculateAudienceStats, fetchCampaigns 
} from '../services/api';
import CreateAudienceModal from './CreateAudienceModal';
import AudienceImportModal from './AudienceImportModal';
import CampaignControlPanel from './CampaignControlPanel';

export default function AudiencesHub({ 
  currentProjectId, 
  projects = [],
  onViewLeadsInTable, 
  onOpenScraper 
}) {
  const [audiences, setAudiences] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [liveCampaignId, setLiveCampaignId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedAudienceForImport, setSelectedAudienceForImport] = useState(null);
  const [enrichingId, setEnrichingId] = useState(null);
  const [actionNotice, setActionNotice] = useState(null);

  const effectiveProjectId = currentProjectId || (projects.length > 0 ? (projects.find(p => p.is_default)?.id || projects[0].id) : null);

  const loadAudiences = async () => {
    if (!effectiveProjectId) return;
    setLoading(true);
    try {
      const [data, camps] = await Promise.all([
        fetchAudiences(effectiveProjectId),
        fetchCampaigns().catch(() => [])
      ]);
      setAudiences(data || []);
      setCampaigns(camps || []);
    } catch (err) {
      console.error('Failed to load audiences:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudiences();
  }, [effectiveProjectId]);

  const handleDelete = async (aud) => {
    if (!window.confirm(`Вы уверены, что хотите удалить аудиторию "${aud.name}"? Это также удалит связанные лиды этой аудитории.`)) {
      return;
    }
    try {
      await deleteAudience(aud.id);
      setAudiences(prev => prev.filter(a => a.id !== aud.id));
      showNotice(`Аудитория "${aud.name}" удалена`, 'success');
    } catch (err) {
      showNotice(err.message || 'Ошибка удаления', 'error');
    }
  };

  const handleEnrich = async (aud) => {
    setEnrichingId(aud.id);
    try {
      const res = await enrichAudience(aud.id);
      showNotice(res.message || 'Обогащение запущено в фоновом режиме', 'success');
      // Refresh stats after short delay
      setTimeout(() => {
        handleRecalculate(aud.id);
      }, 3000);
    } catch (err) {
      showNotice(err.message || 'Ошибка запуска обогащения', 'error');
    } finally {
      setEnrichingId(null);
    }
  };

  const handleRecalculate = async (audienceId) => {
    try {
      const updated = await recalculateAudienceStats(audienceId);
      setAudiences(prev => prev.map(a => a.id === audienceId ? { ...a, ...updated } : a));
    } catch (err) {
      console.error('Failed to recalculate stats:', err);
    }
  };

  const showNotice = (msg, type = 'info') => {
    setActionNotice({ msg, type });
    setTimeout(() => setActionNotice(null), 4000);
  };

  // Aggregated totals
  const totalLeadsSum = audiences.reduce((acc, a) => acc + (a.leads_count || a.stats?.total_leads || 0), 0);
  const totalEmailsSum = audiences.reduce((acc, a) => acc + (a.stats?.with_email || 0), 0);
  const totalEnrichedSum = audiences.reduce((acc, a) => acc + (a.stats?.enriched || 0), 0);

  return (
    <div className="space-y-6">
      
      {/* Top Banner & Stats */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">База Аудиторий</h2>
              <p className="text-xs text-slate-400">
                Сегментируйте клиентов, запускайте парсинг, импортируйте базы и проводите ИИ-обогащение
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {onOpenScraper && (
              <button
                onClick={onOpenScraper}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center space-x-2 transition-all"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                <span>Спарсить с карт</span>
              </button>
            )}

            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/25 flex items-center space-x-2 transition-all transform hover:-translate-y-0.5"
            >
              <Plus className="w-4 h-4" />
              <span>Создать аудиторию</span>
            </button>
          </div>
        </div>

        {/* Global Project Audience Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-800/80">
          <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
            <span className="text-[11px] text-slate-400 block font-medium">Аудиторий в проекте</span>
            <span className="text-xl font-bold text-indigo-400 font-mono">{audiences.length}</span>
          </div>

          <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
            <span className="text-[11px] text-slate-400 block font-medium">Всего контактов</span>
            <span className="text-xl font-bold text-slate-200 font-mono">{totalLeadsSum.toLocaleString()}</span>
          </div>

          <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
            <span className="text-[11px] text-slate-400 block font-medium">С валидным Email</span>
            <span className="text-xl font-bold text-emerald-400 font-mono">{totalEmailsSum.toLocaleString()}</span>
          </div>

          <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
            <span className="text-[11px] text-slate-400 block font-medium">ИИ-Обогащено</span>
            <span className="text-xl font-bold text-purple-400 font-mono">{totalEnrichedSum.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Action Notification Toast */}
      {actionNotice && (
        <div className={`p-4 rounded-xl flex items-center space-x-3 text-xs font-medium border animate-fade-in ${
          actionNotice.type === 'error'
            ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
            : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
        }`}>
          {actionNotice.type === 'error' ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          <span>{actionNotice.msg}</span>
        </div>
      )}

      {/* Audiences Cards Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
          <p className="text-xs">Загрузка аудиторий...</p>
        </div>
      ) : audiences.length === 0 ? (
        <div className="border border-dashed border-slate-800 rounded-2xl p-12 text-center space-y-4 bg-slate-900/20">
          <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <Users className="w-7 h-7" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-slate-200">В этом проекте пока нет аудиторий</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Создайте аудиторию, чтобы импортировать CSV-базу или настроить парсинг с Google Maps под ваши критерии.
            </p>
          </div>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition-all inline-flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Создать первую аудиторию</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {audiences.map((aud) => {
            const leadsCount = aud.leads_count || aud.stats?.total_leads || 0;
            const withEmail = aud.stats?.with_email || 0;
            const withPhone = aud.stats?.with_phone || 0;
            const enriched = aud.stats?.enriched || 0;

            const emailPercent = leadsCount > 0 ? Math.round((withEmail / leadsCount) * 100) : 0;
            const enrichedPercent = leadsCount > 0 ? Math.round((enriched / leadsCount) * 100) : 0;

            return (
              <div 
                key={aud.id} 
                className="bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 flex flex-col justify-between transition-all hover:shadow-xl hover:shadow-black/40 group"
              >
                <div className="space-y-3">
                  
                  {/* Card Header & Source Tag */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <h3 className="text-base font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">
                        {aud.name}
                      </h3>
                      {aud.description && (
                        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                          {aud.description}
                        </p>
                      )}
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-medium border border-slate-700 flex-shrink-0">
                      {aud.source_type === 'PARSER' ? 'Maps Scraper' : aud.source_type === 'CSV_IMPORT' ? 'CSV Import' : 'Database'}
                    </span>
                  </div>

                  {/* Metrics & Progress Bars */}
                  <div className="space-y-2.5 pt-2">
                    
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Всего контактов:</span>
                      <span className="font-bold text-slate-200 font-mono">{leadsCount.toLocaleString()}</span>
                    </div>

                    {/* Email progress bar */}
                    <div>
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                        <span className="flex items-center space-x-1">
                          <Mail className="w-3 h-3 text-emerald-400" />
                          <span>С почтой: {withEmail}</span>
                        </span>
                        <span className="font-mono text-emerald-400 font-semibold">{emailPercent}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                          style={{ width: `${emailPercent}%` }}
                        />
                      </div>
                    </div>

                    {/* AI Enriched progress bar */}
                    <div>
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                        <span className="flex items-center space-x-1">
                          <Sparkles className="w-3 h-3 text-purple-400" />
                          <span>ИИ-обогащено: {enriched}</span>
                        </span>
                        <span className="font-mono text-purple-400 font-semibold">{enrichedPercent}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-purple-500 rounded-full transition-all duration-500"
                          style={{ width: `${enrichedPercent}%` }}
                        />
                      </div>
                    </div>

                  </div>

                </div>

                {/* Live Parser Progress Indicator if campaign is attached */}
                {(() => {
                  const audCamp = campaigns.find(c => c.audience_id === aud.id);
                  if (!audCamp) return null;
                  const isRunning = audCamp.status === 'RUNNING';
                  return (
                    <div className="mt-3 p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/90 flex items-center justify-between text-xs animate-fade-in">
                      <div className="flex items-center space-x-2 truncate">
                        <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-blue-400 animate-ping' : audCamp.status === 'COMPLETED' ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                        <span className="text-[11px] font-medium text-slate-300 truncate">
                          {isRunning ? 'Идет сбор контактов...' : 'Парсинг карт завершен'}
                        </span>
                      </div>
                      <button
                        onClick={() => setLiveCampaignId(audCamp.id)}
                        className="px-2.5 py-1 rounded-lg text-[10px] font-bold text-blue-300 bg-blue-500/15 hover:bg-blue-500/25 border border-blue-500/30 flex items-center space-x-1 transition-all flex-shrink-0 cursor-pointer"
                        title="Открыть живые логи и статус выполнения"
                      >
                        <Activity className="w-3 h-3 text-blue-400" />
                        <span>Живой прогресс</span>
                      </button>
                    </div>
                  );
                })()}

                {/* Card Actions */}
                <div className="pt-5 mt-5 border-t border-slate-800/80 space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => onViewLeadsInTable(aud.id)}
                      className="px-3 py-2 rounded-xl text-xs font-semibold text-white bg-blue-600/80 hover:bg-blue-600 flex items-center justify-center space-x-1.5 transition-colors"
                    >
                      <Database className="w-3.5 h-3.5" />
                      <span>Открыть базу</span>
                    </button>

                    <button
                      onClick={() => setSelectedAudienceForImport(aud)}
                      className="px-3 py-2 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700/80 flex items-center justify-center space-x-1.5 transition-colors"
                    >
                      <Upload className="w-3.5 h-3.5" />
                      <span>Импорт CSV</span>
                    </button>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <button
                      onClick={() => handleEnrich(aud)}
                      disabled={enrichingId === aud.id}
                      className="text-xs text-purple-400 hover:text-purple-300 flex items-center space-x-1 transition-colors disabled:opacity-50"
                    >
                      <Sparkles className={`w-3.5 h-3.5 ${enrichingId === aud.id ? 'animate-spin' : ''}`} />
                      <span>{enrichingId === aud.id ? 'Обогащаем...' : 'Запустить ИИ'}</span>
                    </button>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleRecalculate(aud.id)}
                        title="Пересчитать статистику"
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => handleDelete(aud)}
                        title="Удалить аудиторию"
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

              </div>
            );
          })}
        </div>
      )}

      {/* Create Audience Modal */}
      <CreateAudienceModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        projectId={effectiveProjectId}
        projects={projects}
        onAudienceCreated={(newAud, newCamp) => {
          setAudiences(prev => [newAud, ...prev]);
          if (newCamp && newCamp.id) {
            setLiveCampaignId(newCamp.id);
            showNotice(`Аудитория "${newAud.name}" создана! Парсер запущен в фоне, открыт Live Execution Center.`, 'success');
          } else {
            showNotice(`Аудитория "${newAud.name}" успешно создана!`, 'success');
          }
          loadAudiences();
        }}
      />

      {/* Import File Modal */}
      <AudienceImportModal
        isOpen={Boolean(selectedAudienceForImport)}
        onClose={() => setSelectedAudienceForImport(null)}
        audience={selectedAudienceForImport}
        onImportSuccess={() => {
          if (selectedAudienceForImport) {
            handleRecalculate(selectedAudienceForImport.id);
          }
        }}
      />

      {/* Live Campaign Execution Center Modal */}
      {liveCampaignId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col rounded-3xl shadow-2xl">
            <CampaignControlPanel
              campaignId={liveCampaignId}
              onClose={() => {
                setLiveCampaignId(null);
                loadAudiences();
              }}
            />
          </div>
        </div>
      )}

    </div>
  );
}
