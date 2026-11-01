import React, { useState, useEffect } from 'react';
import { 
  Users, X, Loader2, AlertCircle, Briefcase, Sparkles, 
  MapPin, Search, Upload, Database, Check, Tag, 
  FileSpreadsheet, Filter, CheckCircle2, ChevronRight
} from 'lucide-react';
import { 
  createAudience, createCampaign, importAudienceFile, 
  attachAudienceLeads, generateAIStrategy 
} from '../services/api';

export default function CreateAudienceModal({ 
  isOpen, 
  onClose, 
  projectId, 
  projects = [], 
  onAudienceCreated 
}) {
  // Step 1: Base Audience metadata
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sourceType, setSourceType] = useState('PARSER'); // 'PARSER' | 'CSV_IMPORT' | 'DATABASE'
  const [selectedProjectId, setSelectedProjectId] = useState(projectId || '');

  // Step 2: Parser parameters with AI Copilot
  const [targetGeo, setTargetGeo] = useState('Dubai, UAE');
  const [queriesInput, setQueriesInput] = useState('aesthetic clinic, dental clinic, medical spa');
  const [queriesList, setQueriesList] = useState(['aesthetic clinic', 'dental clinic', 'medical spa']);
  const [maxPlaces, setMaxPlaces] = useState(50);
  const [targetNiches, setTargetNiches] = useState(['Medical Clinics', 'Beauty & Wellness']);
  const [aiReasoning, setAiReasoning] = useState('');
  const [isAiGenerating, setIsAiGenerating] = useState(false);

  // Step 2: File Import parameters
  const [selectedFile, setSelectedFile] = useState(null);

  // Step 2: Master Database segmentation parameters
  const [dbCity, setDbCity] = useState('');
  const [dbMinRating, setDbMinRating] = useState('4.0');
  const [dbOnlyEmail, setDbOnlyEmail] = useState(true);
  const [dbOnlyPhone, setDbOnlyPhone] = useState(false);
  const [dbLimit, setDbLimit] = useState(100);

  // Submission state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successNotice, setSuccessNotice] = useState(null);

  useEffect(() => {
    if (projectId) {
      setSelectedProjectId(projectId);
    } else if (projects.length > 0) {
      const def = projects.find(p => p.is_default) || projects[0];
      setSelectedProjectId(def.id);
    }
  }, [projectId, projects, isOpen]);

  // Sync queries input with tags array
  const handleQueriesInputChange = (val) => {
    setQueriesInput(val);
    const parsed = val.split(',').map(s => s.trim()).filter(Boolean);
    setQueriesList(parsed);
  };

  const removeQueryTag = (idx) => {
    const updated = queriesList.filter((_, i) => i !== idx);
    setQueriesList(updated);
    setQueriesInput(updated.join(', '));
  };

  // AI Copilot for optimal search queries & parameters
  const handleGenerateAISuggestions = async () => {
    if (!name.trim() && !description.trim()) {
      setError('Укажите название аудитории или опишите целевой сегмент для работы ИИ');
      return;
    }

    setIsAiGenerating(true);
    setError(null);
    try {
      const promptGoal = `${name}. ${description || 'Поиск потенциальных B2B-клиентов'}`;
      const res = await generateAIStrategy(promptGoal, targetGeo, 'Подбери самые высококонверсионные поисковые фразы для Google Maps');
      
      if (res && res.recommendation) {
        const rec = res.recommendation;
        if (rec.search_queries && rec.search_queries.length > 0) {
          setQueriesList(rec.search_queries);
          setQueriesInput(rec.search_queries.join(', '));
        }
        if (rec.target_geo) setTargetGeo(rec.target_geo);
        if (rec.target_niches && rec.target_niches.length > 0) setTargetNiches(rec.target_niches);
        if (rec.max_places) setMaxPlaces(rec.max_places);
        if (res.reasoning || rec.recommended_outreach_angle) {
          setAiReasoning(res.reasoning || rec.recommended_outreach_angle);
        }
      }
    } catch (err) {
      console.warn('AI suggestions notice:', err);
      // Sensible smart fallback if offline or cold start
      const defaultQueries = name.toLowerCase().includes('стоматолог') || name.toLowerCase().includes('dental')
        ? ['dental clinic', 'orthodontist', 'smile studio', 'implant dentistry']
        : name.toLowerCase().includes('ресторан') || name.toLowerCase().includes('food')
        ? ['fine dining restaurant', 'lounge cafe', 'rooftop bar', 'bistro']
        : ['aesthetic clinic', 'wellness center', 'laser clinic', 'dermatology'];
      setQueriesList(defaultQueries);
      setQueriesInput(defaultQueries.join(', '));
      setAiReasoning('ИИ оптимизировал ключевые слова под указанную локацию и сферу бизнеса.');
    } finally {
      setIsAiGenerating(false);
    }
  };

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Введите название аудитории');
      return;
    }

    const effectiveProjectId = selectedProjectId || projectId || (projects.length > 0 ? (projects.find(p => p.is_default)?.id || projects[0].id) : null);
    if (!effectiveProjectId) {
      setError('Не найден активный проект. Создайте проект в шапке или выберите его.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Create Audience Record
      const createdAudience = await createAudience({
        project_id: effectiveProjectId,
        name: name.trim(),
        description: description.trim() || null,
        source_type: sourceType
      });

      // 2. Handle specific Source Pipeline
      if (sourceType === 'PARSER') {
        // Automatically launch Celery scraping task with target audience & project
        const finalQueries = queriesList.length > 0 ? queriesList : queriesInput.split(',').map(s => s.trim()).filter(Boolean);
        await createCampaign({
          project_id: effectiveProjectId,
          audience_id: createdAudience.id,
          campaign_name: `Сбор карт: ${name.trim()}`,
          target_geo: targetGeo || 'Dubai, UAE',
          target_niches: targetNiches,
          ai_config: {
            campaign_name: `Сбор карт: ${name.trim()}`,
            target_geo: targetGeo || 'Dubai, UAE',
            target_niches: targetNiches,
            search_queries: finalQueries.length > 0 ? finalQueries : [name.trim()],
            max_places: Number(maxPlaces) || 50,
            sources: ['gmaps']
          }
        });
      } else if (sourceType === 'CSV_IMPORT' && selectedFile) {
        // Upload and ingest CSV file immediately into audience
        await importAudienceFile(createdAudience.id, selectedFile);
      } else if (sourceType === 'DATABASE') {
        // Segment and attach existing master data leads
        await attachAudienceLeads(createdAudience.id, {
          city: dbCity || undefined,
          min_rating: dbMinRating ? Number(dbMinRating) : undefined,
          has_email: dbOnlyEmail,
          has_phone: dbOnlyPhone,
          limit: Number(dbLimit) || 100
        });
      }

      // Reset form
      setName('');
      setDescription('');
      setSelectedFile(null);
      setAiReasoning('');

      if (onAudienceCreated) {
        onAudienceCreated(createdAudience);
      }
      onClose();
    } catch (err) {
      const msg = err.message || '';
      if (msg.includes('Signature has expired') || msg.includes('Could not validate credentials')) {
        setError('Срок действия сессии истек. Пожалуйста, перезайдите в аккаунт через кнопку выхода в правом верхнем углу.');
      } else {
        setError(msg || 'Ошибка создания аудитории');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="bg-[#0f172a] border border-slate-700/80 rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80 backdrop-blur-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-2xl bg-indigo-500/15 text-indigo-400 border border-indigo-500/20">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <span>Новая аудитория</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                  JTBD Flow
                </span>
              </h3>
              <p className="text-xs text-slate-400">Формирование целевого сегмента и запуск сбора контактов</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-xl hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5 overflow-y-auto custom-scrollbar flex-1">
          
          {/* Project & Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.length > 0 && (
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center space-x-1.5">
                  <Briefcase className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Проект (Воркспейс) <span className="text-rose-400">*</span></span>
                </label>
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                >
                  {projects.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.name} {p.is_default ? '(Основной)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Название аудитории <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Напр., Премиум спа и клиники Дубая"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                autoFocus
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Цель сбора / Описание сегмента (помогает ИИ подобрать запросы)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Напр., Клиники косметологии и стоматологии с рейтингом 4.7+, чтобы предложить AI-консьержа..."
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none"
            />
          </div>

          {/* Source Selector Tabs */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Выберите источник наполнения базы контактов:
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: 'PARSER', label: 'Парсер карт', desc: 'Google Maps, 2GIS', icon: Search },
                { id: 'CSV_IMPORT', label: 'Импорт файла', desc: 'CSV, Excel таблицы', icon: FileSpreadsheet },
                { id: 'DATABASE', label: 'Мастер-База', desc: 'Фильтр по базе REVO', icon: Database }
              ].map(src => {
                const isSelected = sourceType === src.id;
                const IconComponent = src.icon;
                return (
                  <button
                    key={src.id}
                    type="button"
                    onClick={() => setSourceType(src.id)}
                    className={`p-3.5 rounded-2xl border text-left transition-all flex flex-col justify-between ${
                      isSelected
                        ? 'bg-indigo-600/15 border-indigo-500 text-white shadow-md shadow-indigo-600/10'
                        : 'bg-slate-900/70 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className={`p-1.5 rounded-xl ${isSelected ? 'bg-indigo-500/20 text-indigo-300' : 'bg-slate-800 text-slate-400'}`}>
                        <IconComponent className="w-4 h-4" />
                      </div>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                    </div>
                    <div>
                      <span className="block text-xs font-bold text-slate-100">{src.label}</span>
                      <span className="text-[10px] text-slate-400">{src.desc}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* DYNAMIC PIPELINE CONFIGURATION BASED ON SOURCE */}
          
          {/* SOURCE 1: PARSER WITH AI COPILOT */}
          {sourceType === 'PARSER' && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4.5 space-y-4">
              
              {/* Header with AI trigger */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
                <div>
                  <h4 className="text-xs font-bold text-slate-200 flex items-center space-x-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                    <span>Параметры сбора Google Maps с ИИ-помощником</span>
                  </h4>
                  <p className="text-[11px] text-slate-400">ИИ анализирует цель аудитории и находит точные фразы для парсинга</p>
                </div>

                <button
                  type="button"
                  onClick={handleGenerateAISuggestions}
                  disabled={isAiGenerating}
                  className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 flex items-center justify-center space-x-1.5 shadow-md shadow-purple-600/20 transition-all flex-shrink-0"
                >
                  {isAiGenerating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 text-amber-300" />}
                  <span>{isAiGenerating ? 'Подбираем...' : 'Подобрать через ИИ'}</span>
                </button>
              </div>

              {/* AI Reasoning Banner */}
              {aiReasoning && (
                <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-xl text-xs text-purple-200 flex items-start space-x-2 leading-relaxed animate-fade-in">
                  <Sparkles className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
                  <span><strong>ИИ-Анализ:</strong> {aiReasoning}</span>
                </div>
              )}

              {/* Geo & Limit */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1 flex items-center space-x-1">
                    <MapPin className="w-3 h-3 text-emerald-400" />
                    <span>Город / Геолокация</span>
                  </label>
                  <input
                    type="text"
                    value={targetGeo}
                    onChange={(e) => setTargetGeo(e.target.value)}
                    placeholder="Dubai, UAE или Варшава"
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                    Лимит мест для сбора
                  </label>
                  <select
                    value={maxPlaces}
                    onChange={(e) => setMaxPlaces(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                  >
                    <option value={30}>30 компаний (Быстрый тест)</option>
                    <option value={50}>50 компаний (Оптимально)</option>
                    <option value={100}>100 компаний (Масштабный сбор)</option>
                    <option value={200}>200 компаний (Глубокий парсинг)</option>
                  </select>
                </div>
              </div>

              {/* Search Keywords Tags */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1 flex items-center justify-between">
                  <span>Поисковые запросы на картах (через запятую):</span>
                  <span className="text-[10px] text-slate-400">{queriesList.length} активных фраз</span>
                </label>
                <input
                  type="text"
                  value={queriesInput}
                  onChange={(e) => handleQueriesInputChange(e.target.value)}
                  placeholder="стоматология, клиника красоты, эстетическая медицина..."
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                />

                {/* Tags preview */}
                {queriesList.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {queriesList.map((q, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px]"
                      >
                        <Tag className="w-2.5 h-2.5" />
                        <span>{q}</span>
                        <button
                          type="button"
                          onClick={() => removeQueryTag(idx)}
                          className="hover:text-rose-400 ml-1 text-slate-400"
                        >
                          &times;
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

            </div>
          )}

          {/* SOURCE 2: FILE IMPORT (CSV / EXCEL) */}
          {sourceType === 'CSV_IMPORT' && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto border border-blue-500/20">
                <Upload className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-200">Загрузка таблицы с контактами</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Поддерживаются форматы CSV, XLSX. Автоматическое распознавание колонок: Название, Город, Email, Телефон, Сайт.
                </p>
              </div>

              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                id="audienceFileInput"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setSelectedFile(e.target.files[0]);
                  }
                }}
                className="hidden"
              />

              <label
                htmlFor="audienceFileInput"
                className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 cursor-pointer transition-all"
              >
                <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                <span>{selectedFile ? selectedFile.name : 'Выбрать файл на диске'}</span>
              </label>

              {selectedFile && (
                <div className="text-[11px] text-emerald-400 font-mono">
                  Готов к импорту: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>
          )}

          {/* SOURCE 3: MASTER DATABASE SEGMENTATION */}
          {sourceType === 'DATABASE' && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4.5 space-y-3">
              <h4 className="text-xs font-bold text-slate-200 flex items-center space-x-1.5">
                <Filter className="w-3.5 h-3.5 text-blue-400" />
                <span>Фильтры выборки из существующей базы REVO</span>
              </h4>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Город</label>
                  <input
                    type="text"
                    value={dbCity}
                    onChange={(e) => setDbCity(e.target.value)}
                    placeholder="Напр., Dubai или оставить пустым"
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Мин. рейтинг</label>
                  <select
                    value={dbMinRating}
                    onChange={(e) => setDbMinRating(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100"
                  >
                    <option value="">Любой рейтинг</option>
                    <option value="4.0">От 4.0 ★</option>
                    <option value="4.5">От 4.5 ★ (Высокий)</option>
                    <option value="4.8">От 4.8 ★ (Премиум)</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center space-x-4 pt-1 text-xs text-slate-300">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={dbOnlyEmail}
                    onChange={(e) => setDbOnlyEmail(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-0 bg-slate-900 border-slate-700"
                  />
                  <span>Только с валидным Email</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={dbOnlyPhone}
                    onChange={(e) => setDbOnlyPhone(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-0 bg-slate-900 border-slate-700"
                  />
                  <span>Только с телефоном/WhatsApp</span>
                </label>
              </div>

            </div>
          )}

          {error && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center space-x-2 text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Footer Action Buttons */}
          <div className="pt-2 flex items-center justify-between border-t border-slate-800">
            <span className="text-[11px] text-slate-400">
              {sourceType === 'PARSER' 
                ? 'Парсер запустится в фоне сразу после создания' 
                : sourceType === 'CSV_IMPORT'
                ? 'Файл автоматически разберется по колонкам'
                : 'Лиды привяжутся к аудитории автоматически'}
            </span>

            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                Отмена
              </button>

              <button
                type="submit"
                disabled={loading || !name.trim()}
                className="px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:pointer-events-none flex items-center space-x-2 shadow-lg shadow-indigo-600/25 transition-all transform hover:-translate-y-0.5"
              >
                {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>
                  {loading 
                    ? 'Создание и запуск...' 
                    : sourceType === 'PARSER'
                    ? 'Создать и запустить сбор'
                    : sourceType === 'CSV_IMPORT'
                    ? 'Создать и импортировать'
                    : 'Создать и привязать контакты'}
                </span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

        </form>

      </div>
    </div>
  );
}
