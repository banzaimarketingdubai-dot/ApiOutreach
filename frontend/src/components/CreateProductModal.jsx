import React, { useState, useEffect } from 'react';
import { Package, X, Loader2, AlertCircle, Plus, Trash2, Briefcase } from 'lucide-react';
import { createProduct, updateProduct } from '../services/api';

export default function CreateProductModal({ 
  isOpen, 
  onClose, 
  projectId, 
  projects = [], 
  productToEdit, 
  onProductSaved 
}) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [targetAudienceIcp, setTargetAudienceIcp] = useState('');
  const [painPoints, setPainPoints] = useState(['']);
  const [valueProps, setValueProps] = useState(['']);
  const [targetActionCta, setTargetActionCta] = useState('Обсудить 15 минут в Zoom');
  const [pricingDetails, setPricingDetails] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState(projectId || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (projectId) {
      setSelectedProjectId(projectId);
    } else if (projects.length > 0) {
      const def = projects.find(p => p.is_default) || projects[0];
      setSelectedProjectId(def.id);
    }
  }, [projectId, projects, isOpen]);

  useEffect(() => {
    if (productToEdit) {
      setName(productToEdit.name || '');
      setDescription(productToEdit.description || '');
      setTargetAudienceIcp(productToEdit.target_audience_icp || '');
      setPainPoints(productToEdit.pain_points?.length ? productToEdit.pain_points : ['']);
      setValueProps(productToEdit.value_props?.length ? productToEdit.value_props : ['']);
      setTargetActionCta(productToEdit.target_action_cta || 'Обсудить 15 минут в Zoom');
      setPricingDetails(productToEdit.pricing_details || '');
    } else {
      setName('');
      setDescription('');
      setTargetAudienceIcp('');
      setPainPoints(['']);
      setValueProps(['']);
      setTargetActionCta('Обсудить 15 минут в Zoom');
      setPricingDetails('');
    }
    setError(null);
  }, [productToEdit, isOpen]);

  if (!isOpen) return null;

  const handleAddPain = () => setPainPoints(prev => [...prev, '']);
  const handleRemovePain = (index) => setPainPoints(prev => prev.filter((_, i) => i !== index));
  const handlePainChange = (index, val) => {
    const updated = [...painPoints];
    updated[index] = val;
    setPainPoints(updated);
  };

  const handleAddUsp = () => setValueProps(prev => [...prev, '']);
  const handleRemoveUsp = (index) => setValueProps(prev => prev.filter((_, i) => i !== index));
  const handleUspChange = (index, val) => {
    const updated = [...valueProps];
    updated[index] = val;
    setValueProps(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Введите название продукта / услуги');
      return;
    }

    const effectiveProjectId = selectedProjectId || projectId || (projects.length > 0 ? (projects.find(p => p.is_default)?.id || projects[0].id) : null);
    if (!effectiveProjectId && !productToEdit) {
      setError('Не выбран активный проект');
      return;
    }

    setLoading(true);
    setError(null);

    const payload = {
      name: name.trim(),
      description: description.trim() || null,
      target_audience_icp: targetAudienceIcp.trim() || null,
      pain_points: painPoints.map(p => p.trim()).filter(Boolean),
      value_props: valueProps.map(v => v.trim()).filter(Boolean),
      target_action_cta: targetActionCta.trim() || null,
      pricing_details: pricingDetails.trim() || null
    };

    try {
      let saved;
      if (productToEdit) {
        saved = await updateProduct(productToEdit.id, payload);
      } else {
        saved = await createProduct({ ...payload, project_id: effectiveProjectId });
      }
      if (onProductSaved) {
        onProductSaved(saved);
      }
      onClose();
    } catch (err) {
      const msg = err.message || '';
      if (msg.includes('Signature has expired') || msg.includes('Could not validate credentials')) {
        setError('Срок действия сессии истек. Пожалуйста, перезайдите в аккаунт через кнопку выхода в правом верхнем углу.');
      } else {
        setError(msg || 'Ошибка сохранения продукта');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="bg-[#0f172a] border border-slate-700/80 rounded-2xl w-full max-w-xl shadow-2xl my-8 overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60 flex-shrink-0">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
              <Package className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100">
                {productToEdit ? 'Редактировать продукт' : 'Новый продукт / Оффер'}
              </h3>
              <p className="text-xs text-slate-400">База знаний для обучения ИИ-копирайтера</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {projects.length > 0 && !productToEdit && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center space-x-1.5">
                <Briefcase className="w-3.5 h-3.5 text-purple-400" />
                <span>Проект / Воркспейс <span className="text-rose-400">*</span></span>
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              >
                {projects.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} {p.is_default ? '(Основной проект)' : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Название продукта / оффера <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Напр., AI-аудит репутации или B2B LeadGen подписка"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Краткое описание (Суть предложения)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="В чем заключается услуга, какую ценность несет..."
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Целевой клиент (ICP — Ideal Customer Profile)
            </label>
            <input
              type="text"
              value={targetAudienceIcp}
              onChange={(e) => setTargetAudienceIcp(e.target.value)}
              placeholder="Владельцы клиник, директора по маркетингу, управляющие салонов"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
            />
          </div>

          {/* Pain Points */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Боли клиента (Pain Points), которые вы закрываете
              </label>
              <button
                type="button"
                onClick={handleAddPain}
                className="text-[11px] text-purple-400 hover:text-purple-300 font-medium flex items-center space-x-1"
              >
                <Plus className="w-3 h-3" />
                <span>Добавить боль</span>
              </button>
            </div>
            <div className="space-y-2">
              {painPoints.map((pain, idx) => (
                <div key={idx} className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={pain}
                    onChange={(e) => handlePainChange(idx, e.target.value)}
                    placeholder="Напр., Низкая конверсия сайта, слив бюджета на рекламу"
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                  {painPoints.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemovePain(idx)}
                      className="p-1.5 text-slate-500 hover:text-rose-400"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Value Props / USPs */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Ключевые УТП и выгоды (Value Propositions)
              </label>
              <button
                type="button"
                onClick={handleAddUsp}
                className="text-[11px] text-purple-400 hover:text-purple-300 font-medium flex items-center space-x-1"
              >
                <Plus className="w-3 h-3" />
                <span>Добавить выгоду</span>
              </button>
            </div>
            <div className="space-y-2">
              {valueProps.map((usp, idx) => (
                <div key={idx} className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={usp}
                    onChange={(e) => handleUspChange(idx, e.target.value)}
                    placeholder="Напр., Рост обращений на 35% за 14 дней без переделки сайта"
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                  {valueProps.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveUsp(idx)}
                      className="p-1.5 text-slate-500 hover:text-rose-400"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Целевое действие (Call to Action)
              </label>
              <input
                type="text"
                value={targetActionCta}
                onChange={(e) => setTargetActionCta(e.target.value)}
                placeholder="Обсудить 15 минут в Zoom / Получить аудит"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Условия / Стоимость (Опционально)
              </label>
              <input
                type="text"
                value={pricingDetails}
                onChange={(e) => setPricingDetails(e.target.value)}
                placeholder="От $290/мес или Бесплатный аудит"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center space-x-2 text-rose-400 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Footer */}
          <div className="pt-3 flex items-center justify-end space-x-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:pointer-events-none flex items-center space-x-1.5 shadow-lg shadow-purple-600/20"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>{loading ? 'Сохранение...' : 'Сохранить продукт'}</span>
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
