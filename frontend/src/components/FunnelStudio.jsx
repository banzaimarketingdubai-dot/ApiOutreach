import React, { useState, useEffect } from 'react';
import { 
  Sparkles, Package, Users, Send, CheckCircle2, AlertCircle, 
  Loader2, ArrowRight, Save, Eye, EyeOff, Copy, RefreshCw, 
  Clock, Tag, HelpCircle, Layers, ChevronRight
} from 'lucide-react';
import { 
  fetchProducts, fetchAudiences, fetchFunnels, createFunnel, 
  generateAIFunnel, fetchLeads, renderEmailPreview 
} from '../services/api';

export default function FunnelStudio({ 
  currentProjectId, 
  initialProductId = null, 
  onLaunchCampaignWithFunnel 
}) {
  const [products, setProducts] = useState([]);
  const [audiences, setAudiences] = useState([]);
  const [savedFunnels, setSavedFunnels] = useState([]);

  // Selected parameters
  const [selectedProductId, setSelectedProductId] = useState(initialProductId || '');
  const [selectedAudienceId, setSelectedAudienceId] = useState('');
  const [touchesCount, setTouchesCount] = useState(3);
  const [toneOfVoice, setToneOfVoice] = useState('Деловой и эмпатичный');
  const [customInstructions, setCustomInstructions] = useState('');

  // Funnel Sequence State
  const [funnelName, setFunnelName] = useState('');
  const [funnelSteps, setFunnelSteps] = useState([]);
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  // Live Preview State
  const [sampleLeads, setSampleLeads] = useState([]);
  const [previewLeadId, setPreviewLeadId] = useState('');
  const [renderedPreview, setRenderedPreview] = useState(null);
  const [isPreviewMode, setIsPreviewMode] = useState(false);

  // Status flags
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState(null);

  useEffect(() => {
    if (initialProductId) {
      setSelectedProductId(initialProductId);
    }
  }, [initialProductId]);

  useEffect(() => {
    if (!currentProjectId) return;
    
    // Load products, audiences, and saved funnels for current project
    fetchProducts(currentProjectId).then(data => {
      setProducts(data || []);
      if (!selectedProductId && data?.length > 0) {
        setSelectedProductId(data[0].id);
      }
    }).catch(console.error);

    fetchAudiences(currentProjectId).then(data => {
      setAudiences(data || []);
      if (!selectedAudienceId && data?.length > 0) {
        setSelectedAudienceId(data[0].id);
      }
    }).catch(console.error);

    loadSavedFunnels();
  }, [currentProjectId]);

  const loadSavedFunnels = async () => {
    try {
      const funnels = await fetchFunnels(currentProjectId);
      setSavedFunnels(funnels || []);
    } catch (e) {
      console.error(e);
    }
  };

  // Load sample leads for the selected audience
  useEffect(() => {
    if (!selectedAudienceId) return;
    fetchLeads({ audience_id: selectedAudienceId, page_size: 5 })
      .then(res => {
        const items = res?.items || [];
        setSampleLeads(items);
        if (items.length > 0) {
          setPreviewLeadId(items[0].id);
        }
      })
      .catch(console.error);
  }, [selectedAudienceId]);

  // Handle AI Funnel Generation
  const handleGenerateFunnel = async () => {
    if (!selectedProductId) {
      showNotice('Выберите продукт для генерации воронки', 'error');
      return;
    }
    if (!selectedAudienceId) {
      showNotice('Выберите целевую аудиторию', 'error');
      return;
    }

    setGenerating(true);
    setNotice(null);

    try {
      const res = await generateAIFunnel({
        product_id: selectedProductId,
        audience_id: selectedAudienceId,
        touches_count: touchesCount,
        tone_of_voice: toneOfVoice,
        custom_instructions: customInstructions
      });

      if (res && res.steps) {
        setFunnelName(res.funnel_name || 'Сгенерированная воронка');
        setFunnelSteps(res.steps);
        setActiveStepIndex(0);
        showNotice(`Воронка из ${res.steps.length} шагов успешно сгенерирована ИИ!`, 'success');
      }
    } catch (err) {
      showNotice(err.message || 'Ошибка генерации воронки', 'error');
    } finally {
      setGenerating(false);
    }
  };

  // Load an existing saved funnel
  const handleSelectSavedFunnel = (funnelId) => {
    const f = savedFunnels.find(item => item.id === funnelId);
    if (f) {
      setFunnelName(f.name);
      setFunnelSteps(f.steps || []);
      setActiveStepIndex(0);
      if (f.product_id) setSelectedProductId(f.product_id);
      if (f.audience_id) setSelectedAudienceId(f.audience_id);
      showNotice(`Загружена воронка "${f.name}"`, 'info');
    }
  };

  // Save Funnel
  const handleSaveFunnel = async () => {
    if (!funnelName.trim()) {
      showNotice('Введите название воронки', 'error');
      return;
    }
    if (funnelSteps.length === 0) {
      showNotice('Воронка не содержит шагов для сохранения', 'error');
      return;
    }

    setSaving(true);
    try {
      const saved = await createFunnel({
        project_id: currentProjectId,
        product_id: selectedProductId || null,
        audience_id: selectedAudienceId || null,
        name: funnelName.trim(),
        description: `Воронка из ${funnelSteps.length} касаний`,
        tone_of_voice: toneOfVoice,
        steps: funnelSteps
      });
      loadSavedFunnels();
      showNotice(`Воронка "${saved.name}" успешно сохранена в шаблоны!`, 'success');
    } catch (err) {
      showNotice(err.message || 'Ошибка сохранения воронки', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Step field modification
  const handleCurrentStepChange = (field, value) => {
    setFunnelSteps(prev => {
      const updated = [...prev];
      updated[activeStepIndex] = { ...updated[activeStepIndex], [field]: value };
      return updated;
    });
  };

  // Insert variable tag into body
  const insertVariableTag = (tag) => {
    const currentBody = funnelSteps[activeStepIndex]?.body_template || '';
    handleCurrentStepChange('body_template', currentBody + ' ' + tag);
  };

  // Render Live Preview
  useEffect(() => {
    if (!isPreviewMode || !previewLeadId || !funnelSteps[activeStepIndex]) return;
    const currentStep = funnelSteps[activeStepIndex];

    renderEmailPreview({
      subject_template: currentStep.subject_template || '',
      body_template: currentStep.body_template || '',
      lead_id: previewLeadId
    })
      .then(res => setRenderedPreview(res))
      .catch(console.error);
  }, [isPreviewMode, previewLeadId, activeStepIndex, funnelSteps]);

  const showNotice = (msg, type = 'info') => {
    setNotice({ msg, type });
    setTimeout(() => setNotice(null), 4000);
  };

  const currentStep = funnelSteps[activeStepIndex] || null;

  return (
    <div className="space-y-6">
      
      {/* Configuration Header Box */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white flex items-center justify-center shadow-lg shadow-purple-600/20">
              <Sparkles className="w-6 h-6 animate-pulse text-amber-300" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">AI Funnel Studio (Воронка касаний)</h2>
              <p className="text-xs text-slate-400">
                ИИ-копирайтер генерирует многошаговую цепочку персонализированных писем на основе вашего продукта и целевой аудитории
              </p>
            </div>
          </div>

          {/* Load from saved funnels */}
          {savedFunnels.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-400">Шаблон:</span>
              <select
                onChange={(e) => handleSelectSavedFunnel(e.target.value)}
                className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              >
                <option value="">-- Выбрать сохраненную воронку --</option>
                {savedFunnels.map(f => (
                  <option key={f.id} value={f.id}>{f.name} ({f.steps?.length} касаний)</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Studio Inputs Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-5">
          
          {/* Product Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center space-x-1.5">
              <Package className="w-3.5 h-3.5 text-purple-400" />
              <span>Продукт / Оффер</span>
            </label>
            <select
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
            >
              {products.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
              {products.length === 0 && (
                <option value="">Нет созданных продуктов</option>
              )}
            </select>
          </div>

          {/* Audience Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center space-x-1.5">
              <Users className="w-3.5 h-3.5 text-indigo-400" />
              <span>Целевая Аудитория</span>
            </label>
            <select
              value={selectedAudienceId}
              onChange={(e) => setSelectedAudienceId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
            >
              {audiences.map(a => (
                <option key={a.id} value={a.id}>{a.name} ({a.leads_count || a.stats?.total_leads || 0} контактов)</option>
              ))}
              {audiences.length === 0 && (
                <option value="">Нет созданных аудиторий</option>
              )}
            </select>
          </div>

          {/* Touches Count */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-blue-400" />
              <span>Количество касаний</span>
            </label>
            <div className="flex space-x-1">
              {[2, 3, 4, 5].map(num => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setTouchesCount(num)}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    touchesCount === num
                      ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                      : 'bg-slate-900 border border-slate-700 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>

          {/* Tone of Voice */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Тон общения (Tone of Voice)
            </label>
            <select
              value={toneOfVoice}
              onChange={(e) => setToneOfVoice(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
            >
              <option value="Деловой и эмпатичный">Деловой и эмпатичный</option>
              <option value="Короткий и прямой (Direct)">Короткий и прямой (Direct)</option>
              <option value="Консультативный эксперт">Консультативный эксперт</option>
              <option value="Партнерский и дружелюбный">Партнерский и дружелюбный</option>
            </select>
          </div>

        </div>

        {/* Custom Angle / Instructions */}
        <div className="mt-4 pt-4 border-t border-slate-800 flex flex-col md:flex-row items-stretch md:items-center gap-3">
          <input
            type="text"
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            placeholder="Дополнительные пожелания к письмам (напр., «сделать упор на кейс с ростом выручки на 30%»)..."
            className="flex-1 bg-slate-900 border border-slate-700 text-xs text-slate-100 placeholder-slate-500 rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
          />

          <button
            onClick={handleGenerateFunnel}
            disabled={generating || !selectedProductId || !selectedAudienceId}
            className="px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center space-x-2 shadow-lg shadow-purple-600/25 transition-all transform hover:-translate-y-0.5 flex-shrink-0"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Генерация воронки (Gemini)...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-amber-300 animate-pulse" />
                <span>Сгенерировать воронку ИИ</span>
              </>
            )}
          </button>
        </div>

      </div>

      {/* Notice Toast */}
      {notice && (
        <div className={`p-4 rounded-xl flex items-center space-x-3 text-xs font-medium border animate-fade-in ${
          notice.type === 'error'
            ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
            : notice.type === 'success'
            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
            : 'bg-blue-500/10 text-blue-300 border-blue-500/30'
        }`}>
          {notice.type === 'error' ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          <span>{notice.msg}</span>
        </div>
      )}

      {/* Funnel Sequence Steps Editor Area */}
      {funnelSteps.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-sm">
          
          {/* Stepper Header (Touch 1 -> Touch 2 -> Touch 3) */}
          <div className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            
            <div className="flex items-center space-x-3 flex-1">
              <input
                type="text"
                value={funnelName}
                onChange={(e) => setFunnelName(e.target.value)}
                placeholder="Название воронки..."
                className="bg-transparent text-base font-bold text-slate-100 border-b border-transparent hover:border-slate-700 focus:border-purple-500 focus:outline-none px-1 py-0.5"
              />
            </div>

            {/* Stepper Tabs */}
            <div className="flex items-center space-x-2 overflow-x-auto">
              {funnelSteps.map((step, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveStepIndex(idx)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                    activeStepIndex === idx
                      ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                      : 'bg-slate-800/80 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <span>Touch {step.step_number || idx + 1}</span>
                  <span className="text-[10px] opacity-75 font-mono">
                    ({step.delay_days === 0 ? 'День 0' : `+${step.delay_days}д`})
                  </span>
                </button>
              ))}
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSaveFunnel}
                disabled={saving}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center space-x-1.5 transition-colors"
              >
                {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5 text-purple-400" />}
                <span>Сохранить воронку</span>
              </button>

              {onLaunchCampaignWithFunnel && (
                <button
                  onClick={() => onLaunchCampaignWithFunnel({ name: funnelName, steps: funnelSteps, product_id: selectedProductId, audience_id: selectedAudienceId })}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/20 flex items-center space-x-1.5 transition-colors"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>В рассылку</span>
                </button>
              )}
            </div>

          </div>

          {/* Current Step Editor & Live Preview */}
          {currentStep && (
            <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Left Column: Form Editor (8 cols) */}
              <div className="lg:col-span-7 space-y-4">
                
                {/* Meta details */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="col-span-2">
                    <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                      Название и цель этапа
                    </label>
                    <input
                      type="text"
                      value={currentStep.step_name || ''}
                      onChange={(e) => handleCurrentStepChange('step_name', e.target.value)}
                      placeholder="Напр., Хук и главная боль"
                      className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-100 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                      Задержка отправки
                    </label>
                    <div className="flex items-center space-x-1.5">
                      <input
                        type="number"
                        min="0"
                        max="30"
                        value={currentStep.delay_days ?? 0}
                        onChange={(e) => handleCurrentStepChange('delay_days', parseInt(e.target.value) || 0)}
                        className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-100 rounded-xl px-3 py-2 text-center font-mono focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                      />
                      <span className="text-xs text-slate-400">дней</span>
                    </div>
                  </div>
                </div>

                {/* Subject Line */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-semibold text-slate-400">
                      Тема письма (Subject Line)
                    </label>
                    {currentStep.subject_variants?.length > 0 && (
                      <span className="text-[10px] text-slate-500">Варианты от ИИ (кликните для замены):</span>
                    )}
                  </div>
                  <input
                    type="text"
                    value={currentStep.subject_template || ''}
                    onChange={(e) => handleCurrentStepChange('subject_template', e.target.value)}
                    placeholder="Напр., Вопрос по сайту {{company_name}}"
                    className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-100 font-medium rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  />

                  {/* Subject Variant Chips */}
                  {currentStep.subject_variants?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {currentStep.subject_variants.map((v, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => handleCurrentStepChange('subject_template', v)}
                          className="text-[11px] px-2 py-0.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors text-left truncate max-w-xs"
                          title="Использовать этот вариант темы"
                        >
                          {v}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Body Editor with Variables Clicker */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-[11px] font-semibold text-slate-400">
                      Текст письма (Email Body)
                    </label>
                    
                    {/* Tags Quick-Insert Bar */}
                    <div className="flex items-center space-x-1 text-[11px]">
                      <span className="text-slate-500 mr-1">Вставить тег:</span>
                      <button
                        type="button"
                        onClick={() => insertVariableTag('{{company_name}}')}
                        className="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 font-mono text-[10px] border border-indigo-500/20"
                      >
                        + {{company_name}}
                      </button>
                      <button
                        type="button"
                        onClick={() => insertVariableTag('{{city}}')}
                        className="px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 font-mono text-[10px] border border-blue-500/20"
                      >
                        + {{city}}
                      </button>
                      <button
                        type="button"
                        onClick={() => insertVariableTag('{{website}}')}
                        className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 font-mono text-[10px] border border-purple-500/20"
                      >
                        + {{website}}
                      </button>
                    </div>
                  </div>

                  <textarea
                    rows={9}
                    value={currentStep.body_template || ''}
                    onChange={(e) => handleCurrentStepChange('body_template', e.target.value)}
                    placeholder="Текст письма с тегами персонализации..."
                    className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-100 rounded-xl p-3.5 focus:outline-none focus:ring-2 focus:ring-purple-500/50 font-sans leading-relaxed resize-none"
                  />
                </div>

                {/* Rationale & CTA */}
                {currentStep.rationale && (
                  <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1">
                    <span className="font-semibold text-slate-300 block">💡 Стратегия этого касания:</span>
                    <p>{currentStep.rationale}</p>
                  </div>
                )}

              </div>

              {/* Right Column: Live Real Lead Preview (5 cols) */}
              <div className="lg:col-span-5 bg-slate-950/70 rounded-2xl p-4 border border-slate-800 flex flex-col justify-between">
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-200">
                      <Eye className="w-4 h-4 text-emerald-400" />
                      <span>Предпросмотр реального письма</span>
                    </div>

                    <button
                      type="button"
                      onClick={() => setIsPreviewMode(!isPreviewMode)}
                      className={`text-[11px] px-2.5 py-1 rounded-lg font-medium transition-colors ${
                        isPreviewMode
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {isPreviewMode ? 'Подстановка вкл' : 'Включить рендер'}
                    </button>
                  </div>

                  {/* Sample Lead Selector */}
                  <div>
                    <label className="block text-[10px] uppercase font-semibold text-slate-500 mb-1">
                      Пример лида из базы:
                    </label>
                    <select
                      value={previewLeadId}
                      onChange={(e) => { setPreviewLeadId(e.target.value); setIsPreviewMode(true); }}
                      className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-2.5 py-1.5 focus:outline-none"
                    >
                      {sampleLeads.map(l => (
                        <option key={l.id} value={l.id}>
                          {l.company_name} ({l.city || 'Город не указан'})
                        </option>
                      ))}
                      {sampleLeads.length === 0 && (
                        <option value="">В этой аудитории пока нет лидов</option>
                      )}
                    </select>
                  </div>

                  {/* Preview Box */}
                  <div className="p-4 bg-slate-900/90 rounded-xl border border-slate-800/80 space-y-3 min-h-[220px]">
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase font-mono">Тема:</span>
                      <p className="text-xs font-bold text-slate-100">
                        {isPreviewMode && renderedPreview 
                          ? renderedPreview.rendered_subject 
                          : currentStep.subject_template || '(пусто)'}
                      </p>
                    </div>

                    <div className="h-px bg-slate-800" />

                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase font-mono mb-1">Сообщение:</span>
                      <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed font-sans">
                        {isPreviewMode && renderedPreview 
                          ? renderedPreview.rendered_body 
                          : currentStep.body_template || '(пусто)'}
                      </p>
                    </div>
                  </div>

                </div>

                <div className="pt-3 text-[11px] text-slate-500 text-center">
                  Все теги <code>&#123;&#123;переменные&#125;&#125;</code> заменяются на реальные данные лида в момент отправки.
                </div>

              </div>

            </div>
          )}

        </div>
      )}

    </div>
  );
}
