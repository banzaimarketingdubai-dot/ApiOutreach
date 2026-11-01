import React, { useState, useEffect } from 'react';
import { Users, X, Loader2, AlertCircle, Briefcase } from 'lucide-react';
import { createAudience } from '../services/api';

export default function CreateAudienceModal({ 
  isOpen, 
  onClose, 
  projectId, 
  projects = [], 
  onAudienceCreated 
}) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sourceType, setSourceType] = useState('PARSER');
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
      const created = await createAudience({
        project_id: effectiveProjectId,
        name: name.trim(),
        description: description.trim() || null,
        source_type: sourceType
      });
      setName('');
      setDescription('');
      if (onAudienceCreated) {
        onAudienceCreated(created);
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0f172a] border border-slate-700/80 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100">Новая аудитория</h3>
              <p className="text-xs text-slate-400">Сегмент контактов для аутрича</p>
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
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {projects.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center space-x-1.5">
                <Briefcase className="w-3.5 h-3.5 text-indigo-400" />
                <span>Проект / Воркспейс <span className="text-rose-400">*</span></span>
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
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
              Название аудитории <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Напр., Стоматологии Варшавы (Premium)"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Описание / Критерии отбора
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Клиники с рейтингом > 4.2, имплантация, премиальный сегмент..."
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Основной источник наполнения
            </label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            >
              <option value="PARSER">Парсер карт (Google Maps, 2GIS)</option>
              <option value="CSV_IMPORT">Импорт файлов (CSV, Excel)</option>
              <option value="MANUAL">Ручное добавление / API</option>
            </select>
          </div>

          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center space-x-2 text-rose-400 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Footer */}
          <div className="pt-2 flex items-center justify-end space-x-3">
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
              className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:pointer-events-none flex items-center space-x-1.5 shadow-lg shadow-indigo-600/20"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>{loading ? 'Создание...' : 'Создать аудиторию'}</span>
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
