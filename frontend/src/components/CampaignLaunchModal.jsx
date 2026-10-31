import React, { useState, useEffect } from 'react';
import { 
  Send, X, Loader2, AlertCircle, ShieldCheck, Zap, 
  Calendar, Clock, Sliders, CheckCircle2, Users, Package, Layers 
} from 'lucide-react';
import { fetchProducts, fetchAudiences, fetchFunnels, launchMultiCampaign } from '../services/api';

export default function CampaignLaunchModal({ 
  isOpen, 
  onClose, 
  currentProjectId, 
  presetData = null, 
  onCampaignLaunched 
}) {
  const [products, setProducts] = useState([]);
  const [audiences, setAudiences] = useState([]);
  const [funnels, setFunnels] = useState([]);

  const [campaignName, setCampaignName] = useState('');
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedAudienceId, setSelectedAudienceId] = useState('');
  const [selectedFunnelId, setSelectedFunnelId] = useState('');

  // Schedule and review options
  const [isManualReviewRequired, setIsManualReviewRequired] = useState(true);
  const [dailyLimit, setDailyLimit] = useState(50);
  const [startHour, setStartHour] = useState(9);
  const [endHour, setEndHour] = useState(18);
  const [workdaysOnly, setWorkdaysOnly] = useState(true);
  const [delaySec, setDelaySec] = useState(120);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !currentProjectId) return;

    fetchProducts(currentProjectId).then(data => {
      setProducts(data || []);
      if (!selectedProductId && data?.length > 0) setSelectedProductId(data[0].id);
    }).catch(console.error);

    fetchAudiences(currentProjectId).then(data => {
      setAudiences(data || []);
      if (!selectedAudienceId && data?.length > 0) setSelectedAudienceId(data[0].id);
    }).catch(console.error);

    fetchFunnels(currentProjectId).then(data => {
      setFunnels(data || []);
      if (!selectedFunnelId && data?.length > 0) setSelectedFunnelId(data[0].id);
    }).catch(console.error);

    if (presetData) {
      if (presetData.name) setCampaignName(presetData.name);
      if (presetData.product_id) setSelectedProductId(presetData.product_id);
      if (presetData.audience_id) setSelectedAudienceId(presetData.audience_id);
    } else {
      setCampaignName('Новая рассылка ' + new Date().toLocaleDateString('ru-RU'));
    }
    setError(null);
  }, [isOpen, currentProjectId, presetData]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!campaignName.trim()) {
      setError('Введите название кампании');
      return;
    }
    if (!selectedAudienceId) {
      setError('Выберите целевую аудиторию');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        project_id: currentProjectId,
        product_id: selectedProductId || null,
        audience_id: selectedAudienceId,
        funnel_sequence_id: selectedFunnelId || null,
        steps: presetData?.steps || null,
        campaign_name: campaignName.trim(),
        is_manual_review_required: isManualReviewRequired,
        schedule_config: {
          daily_limit: dailyLimit,
          send_start_hour: startHour,
          send_end_hour: endHour,
          workdays_only: workdaysOnly,
          delay_between_emails_sec: delaySec
        }
      };

      const res = await launchMultiCampaign(payload);
      if (onCampaignLaunched) {
        onCampaignLaunched(res);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Ошибка запуска кампании');
    } finally {
      setLoading(false);
    }
  };

  const selectedAudience = audiences.find(a => a.id === selectedAudienceId);
  const leadsCount = selectedAudience?.leads_count || selectedAudience?.stats?.total_leads || 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="bg-[#0f172a] border border-slate-700/80 rounded-2xl w-full max-w-xl shadow-2xl my-8 overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
              <Send className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100">Запуск рассылочной кампании</h3>
              <p className="text-xs text-slate-400">Настройка связки, расписания и контроля качества</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Название кампании <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              placeholder="Напр., AI-аудит: Стоматологии Варшавы (Q4)"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              autoFocus
            />
          </div>

          {/* Triad: Product + Audience + Funnel */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                Продукт / Оффер
              </label>
              <select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-2.5 py-2 focus:outline-none"
              >
                {products.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                Целевая аудитория
              </label>
              <select
                value={selectedAudienceId}
                onChange={(e) => setSelectedAudienceId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-2.5 py-2 focus:outline-none"
              >
                {audiences.map(a => (
                  <option key={a.id} value={a.id}>{a.name} ({a.leads_count || a.stats?.total_leads || 0})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                Воронка касаний
              </label>
              <select
                value={selectedFunnelId}
                onChange={(e) => setSelectedFunnelId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-2.5 py-2 focus:outline-none"
              >
                {presetData?.steps && (
                  <option value="">Сгенерированная в студии ({presetData.steps.length} шагов)</option>
                )}
                {funnels.map(f => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
                {funnels.length === 0 && !presetData?.steps && (
                  <option value="">Базовая 3-шаговая воронка</option>
                )}
              </select>
            </div>
          </div>

          {/* Mode Switcher: Manual Review vs Autopilot */}
          <div className="pt-2">
            <span className="block text-xs font-semibold text-slate-300 mb-2">
              Режим контроля качества (Dispatch Mode):
            </span>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setIsManualReviewRequired(true)}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  isManualReviewRequired
                    ? 'bg-blue-600/10 border-blue-500/50 text-white shadow-md shadow-blue-500/10'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center space-x-2 text-blue-400 mb-1">
                  <ShieldCheck className="w-4 h-4" />
                  <span className="text-xs font-bold">Ручной контроль (Review Queue)</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-tight">
                  Письма генерируются в черновики. Вы сможете лично просмотреть и одобрить каждое перед отправкой.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setIsManualReviewRequired(false)}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  !isManualReviewRequired
                    ? 'bg-purple-600/10 border-purple-500/50 text-white shadow-md shadow-purple-500/10'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center space-x-2 text-purple-400 mb-1">
                  <Zap className="w-4 h-4" />
                  <span className="text-xs font-bold">Полный автопилот</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-tight">
                  Письма уходят автоматически по заданному расписанию без дополнительного подтверждения.
                </p>
              </button>
            </div>
          </div>

          {/* Schedule & Limits */}
          <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-3">
            <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-blue-400" />
              <span>Расписание отправки & Лимиты безопасности:</span>
            </span>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Дневной лимит:</label>
                <input
                  type="number"
                  min="5"
                  max="500"
                  value={dailyLimit}
                  onChange={(e) => setDailyLimit(parseInt(e.target.value) || 50)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-center font-mono text-slate-200"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Рабочие часы:</label>
                <div className="flex items-center space-x-1">
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={startHour}
                    onChange={(e) => setStartHour(parseInt(e.target.value) || 9)}
                    className="w-10 bg-slate-950 border border-slate-700 rounded-lg px-1 py-1 text-center font-mono text-slate-200"
                  />
                  <span>-</span>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={endHour}
                    onChange={(e) => setEndHour(parseInt(e.target.value) || 18)}
                    className="w-10 bg-slate-950 border border-slate-700 rounded-lg px-1 py-1 text-center font-mono text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Пауза между письмами:</label>
                <div className="flex items-center space-x-1">
                  <input
                    type="number"
                    min="30"
                    max="600"
                    value={delaySec}
                    onChange={(e) => setDelaySec(parseInt(e.target.value) || 120)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-center font-mono text-slate-200"
                  />
                  <span className="text-[10px] text-slate-500">сек</span>
                </div>
              </div>

              <div className="flex flex-col justify-end">
                <label className="flex items-center space-x-1.5 cursor-pointer pb-1">
                  <input
                    type="checkbox"
                    checked={workdaysOnly}
                    onChange={(e) => setWorkdaysOnly(e.target.checked)}
                    className="rounded border-slate-700 text-blue-600 focus:ring-0"
                  />
                  <span className="text-[11px] text-slate-300">Только будни</span>
                </label>
              </div>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center space-x-2 text-rose-400 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Footer */}
          <div className="pt-2 flex items-center justify-between border-t border-slate-800">
            <span className="text-xs text-slate-400">
              Лидов в аудитории: <strong className="text-slate-200">{leadsCount}</strong>
            </span>

            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={loading || !campaignName.trim() || !selectedAudienceId}
                className="px-6 py-2 rounded-xl text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:pointer-events-none flex items-center space-x-1.5 shadow-lg shadow-blue-600/20"
              >
                {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>{loading ? 'Формирование писем...' : 'Запустить кампанию'}</span>
              </button>
            </div>
          </div>

        </form>

      </div>
    </div>
  );
}
