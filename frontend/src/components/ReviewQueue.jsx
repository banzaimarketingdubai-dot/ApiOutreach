import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, Check, X, Edit3, Save, RefreshCw, 
  Send, AlertCircle, CheckCircle2, Building, Mail, MapPin, 
  ChevronDown, ChevronUp, Layers, CheckSquare, Square
} from 'lucide-react';
import { fetchReviewQueue, approveReviewDrafts, rejectReviewDrafts, updateReviewDraft } from '../services/api';

export default function ReviewQueue({ currentProjectId }) {
  const [drafts, setDrafts] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);

  // Inline editing state
  const [editingId, setEditingId] = useState(null);
  const [editSubject, setEditSubject] = useState('');
  const [editContent, setEditContent] = useState('');

  const [notice, setNotice] = useState(null);

  const loadQueue = async () => {
    setLoading(true);
    try {
      const res = await fetchReviewQueue({ project_id: currentProjectId, page_size: 50 });
      setDrafts(res.items || []);
      setTotalCount(res.total || 0);
      setSelectedIds([]);
    } catch (err) {
      console.error('Failed to load review queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [currentProjectId]);

  const showNotice = (msg, type = 'info') => {
    setNotice({ msg, type });
    setTimeout(() => setNotice(null), 4000);
  };

  const handleToggleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedIds.length === drafts.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(drafts.map(d => d.id));
    }
  };

  // Actions
  const handleApprove = async (id) => {
    try {
      await approveReviewDrafts({ sequence_ids: [id] });
      setDrafts(prev => prev.filter(d => d.id !== id));
      setTotalCount(prev => Math.max(0, prev - 1));
      showNotice('Письмо одобрено и отправлено в очередь доставки', 'success');
    } catch (err) {
      showNotice(err.message || 'Ошибка одобрения', 'error');
    }
  };

  const handleApproveSelected = async () => {
    if (selectedIds.length === 0) return;
    try {
      await approveReviewDrafts({ sequence_ids: selectedIds });
      setDrafts(prev => prev.filter(d => !selectedIds.includes(d.id)));
      setTotalCount(prev => Math.max(0, prev - selectedIds.length));
      setSelectedIds([]);
      showNotice(`Одобрено писем: ${selectedIds.length}`, 'success');
    } catch (err) {
      showNotice(err.message || 'Ошибка одобрения', 'error');
    }
  };

  const handleApproveAll = async () => {
    if (!window.confirm(`Вы уверены, что хотите одобрить все ${totalCount} писем в очереди?`)) return;
    try {
      await approveReviewDrafts({ approve_all: true });
      setDrafts([]);
      setTotalCount(0);
      showNotice('Все письма очереди одобрены к отправке!', 'success');
    } catch (err) {
      showNotice(err.message || 'Ошибка одобрения', 'error');
    }
  };

  const handleReject = async (id) => {
    try {
      await rejectReviewDrafts([id]);
      setDrafts(prev => prev.filter(d => d.id !== id));
      setTotalCount(prev => Math.max(0, prev - 1));
      showNotice('Письмо отменено', 'info');
    } catch (err) {
      showNotice(err.message || 'Ошибка отмены', 'error');
    }
  };

  const startEdit = (draft) => {
    setEditingId(draft.id);
    setEditSubject(draft.email_subject || '');
    setEditContent(draft.email_content || '');
  };

  const saveEdit = async (draftId) => {
    try {
      await updateReviewDraft(draftId, {
        email_subject: editSubject,
        email_content: editContent
      });
      setDrafts(prev => prev.map(d => d.id === draftId ? { ...d, email_subject: editSubject, email_content: editContent } : d));
      setEditingId(null);
      showNotice('Текст письма обновлен', 'success');
    } catch (err) {
      showNotice(err.message || 'Ошибка обновления текста', 'error');
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-bold text-slate-100">Review Queue (Ручная модерация)</h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-300 font-mono font-semibold border border-blue-500/20">
                  {totalCount} на проверке
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Персонализированные черновики перед отправкой. Проверьте подстановку данных, отредактируйте текст или одобрите отправку.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              onClick={loadQueue}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-200 bg-slate-800 border border-slate-700 transition-colors"
              title="Обновить очередь"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            {selectedIds.length > 0 && (
              <button
                onClick={handleApproveSelected}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 shadow-md shadow-blue-600/20 flex items-center space-x-1.5 transition-all"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Одобрить выбранные ({selectedIds.length})</span>
              </button>
            )}

            {totalCount > 0 && (
              <button
                onClick={handleApproveAll}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center space-x-1.5 transition-colors"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Одобрить все ({totalCount})</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Notice Toast */}
      {notice && (
        <div className={`p-4 rounded-xl flex items-center space-x-3 text-xs font-medium border animate-fade-in ${
          notice.type === 'error'
            ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
            : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
        }`}>
          {notice.type === 'error' ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          <span>{notice.msg}</span>
        </div>
      )}

      {/* Drafts List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-400" />
          <p className="text-xs">Загрузка черновиков очереди...</p>
        </div>
      ) : drafts.length === 0 ? (
        <div className="border border-dashed border-slate-800 rounded-2xl p-12 text-center space-y-4 bg-slate-900/20">
          <div className="w-14 h-14 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-7 h-7" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-slate-200">Очередь модерации пуста</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Все подготовленные письма уже одобрены или отправлены. Чтобы сформировать новые черновики, запустите кампанию в режиме ручного контроля.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          
          {/* Select all bar */}
          <div className="flex items-center justify-between px-3 text-xs text-slate-400">
            <button
              onClick={handleSelectAll}
              className="flex items-center space-x-1.5 hover:text-slate-200"
            >
              {selectedIds.length === drafts.length ? (
                <CheckSquare className="w-4 h-4 text-blue-400" />
              ) : (
                <Square className="w-4 h-4" />
              )}
              <span>Выбрать все на странице ({drafts.length})</span>
            </button>
            <span>Показано: {drafts.length} из {totalCount}</span>
          </div>

          {drafts.map((draft) => {
            const isEditing = editingId === draft.id;
            const isSelected = selectedIds.includes(draft.id);

            return (
              <div
                key={draft.id}
                className={`bg-slate-900/80 border rounded-2xl p-5 transition-all shadow-md ${
                  isSelected ? 'border-blue-500/50 bg-blue-950/20' : 'border-slate-800 hover:border-slate-700/80'
                }`}
              >
                
                {/* Header row: Recipient & Touch */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                  <div className="flex items-center space-x-3">
                    <button
                      type="button"
                      onClick={() => handleToggleSelect(draft.id)}
                      className="text-slate-400 hover:text-blue-400"
                    >
                      {isSelected ? (
                        <CheckSquare className="w-4 h-4 text-blue-400" />
                      ) : (
                        <Square className="w-4 h-4" />
                      )}
                    </button>

                    <div className="space-y-0.5">
                      <div className="flex items-center space-x-2">
                        <Building className="w-3.5 h-3.5 text-blue-400" />
                        <h4 className="text-sm font-bold text-slate-100">{draft.company_name}</h4>
                        {draft.city && (
                          <span className="text-[11px] text-slate-400 flex items-center space-x-0.5">
                            <MapPin className="w-3 h-3 text-slate-500" />
                            <span>{draft.city}</span>
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2 text-xs text-slate-400">
                        <Mail className="w-3 h-3 text-slate-500" />
                        <span className="font-mono text-slate-300">{draft.recipient_email || 'Email отсутствует'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-300 font-mono font-semibold border border-purple-500/20">
                      Touch {draft.current_touch || 1}
                    </span>

                    <button
                      onClick={() => handleApprove(draft.id)}
                      className="px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 flex items-center space-x-1 shadow-md shadow-blue-600/20"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Одобрить</span>
                    </button>

                    <button
                      onClick={() => handleReject(draft.id)}
                      className="p-1.5 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-slate-800"
                      title="Пропустить отправку"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Content Area */}
                <div className="pt-3 space-y-2">
                  {!isEditing ? (
                    <>
                      <div>
                        <span className="text-[10px] font-mono text-slate-500 uppercase block">Тема:</span>
                        <p className="text-xs font-semibold text-slate-200">{draft.email_subject}</p>
                      </div>

                      <div>
                        <span className="text-[10px] font-mono text-slate-500 uppercase block">Текст:</span>
                        <p className="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                          {draft.email_content}
                        </p>
                      </div>

                      <div className="flex justify-end pt-1">
                        <button
                          onClick={() => startEdit(draft)}
                          className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center space-x-1 font-medium"
                        >
                          <Edit3 className="w-3 h-3" />
                          <span>Отредактировать текст перед отправкой</span>
                        </button>
                      </div>
                    </>
                  ) : (
                    /* Inline Editing Mode */
                    <div className="space-y-3 pt-1">
                      <div>
                        <label className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                          Редактирование темы:
                        </label>
                        <input
                          type="text"
                          value={editSubject}
                          onChange={(e) => setEditSubject(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-700 text-xs text-slate-100 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                        />
                      </div>

                      <div>
                        <label className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                          Редактирование текста сообщения:
                        </label>
                        <textarea
                          rows={6}
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-700 text-xs text-slate-100 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-sans leading-relaxed resize-none"
                        />
                      </div>

                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => setEditingId(null)}
                          className="px-3 py-1.5 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                        >
                          Отмена
                        </button>
                        <button
                          onClick={() => saveEdit(draft.id)}
                          className="px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 flex items-center space-x-1"
                        >
                          <Save className="w-3.5 h-3.5" />
                          <span>Сохранить изменения</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
