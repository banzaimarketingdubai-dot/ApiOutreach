import React, { useState, useEffect } from 'react';
import { 
  Inbox, Sparkles, Send, CheckCircle2, AlertCircle, RefreshCw, 
  MessageSquare, User, Building, Clock, Flame, HelpCircle, 
  Slash, CornerDownLeft, Loader2, Play
} from 'lucide-react';
import { fetchInboundReplies, sendInboxResponse, simulateInboundReply, fetchLeads } from '../services/api';

export default function InboxHub({ currentProjectId }) {
  const [replies, setReplies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [intentFilter, setIntentFilter] = useState(''); // '' for all
  
  // Replying state
  const [respondingId, setRespondingId] = useState(null);
  const [responseTextMap, setResponseTextMap] = useState({});
  const [sendingId, setSendingId] = useState(null);

  // Simulation modal
  const [isSimulateModalOpen, setIsSimulateModalOpen] = useState(false);
  const [leadsForSim, setLeadsForSim] = useState([]);
  const [simLeadId, setSimLeadId] = useState('');
  const [simMessage, setSimMessage] = useState('Здравствуйте! Ваше предложение заинтересовало, сколько стоит внедрение и можно ли посмотреть демо?');
  const [simulating, setSimulating] = useState(false);

  const [notice, setNotice] = useState(null);

  const loadReplies = async () => {
    setLoading(true);
    try {
      const data = await fetchInboundReplies({
        project_id: currentProjectId,
        intent: intentFilter || undefined
      });
      setReplies(data || []);

      // Pre-fill response text map with AI drafts
      const initMap = {};
      (data || []).forEach(r => {
        if (r.ai_draft_response) {
          initMap[r.id] = r.ai_draft_response;
        }
      });
      setResponseTextMap(prev => ({ ...initMap, ...prev }));
    } catch (err) {
      console.error('Failed to load inbound replies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReplies();
  }, [currentProjectId, intentFilter]);

  // Load leads for simulation modal
  useEffect(() => {
    if (!isSimulateModalOpen) return;
    fetchLeads({ project_id: currentProjectId, page_size: 15 })
      .then(res => {
        const items = res?.items || [];
        setLeadsForSim(items);
        if (items.length > 0 && !simLeadId) {
          setSimLeadId(items[0].id);
        }
      })
      .catch(console.error);
  }, [isSimulateModalOpen, currentProjectId]);

  const showNotice = (msg, type = 'info') => {
    setNotice({ msg, type });
    setTimeout(() => setNotice(null), 4000);
  };

  const handleSendResponse = async (reply) => {
    const textToSend = responseTextMap[reply.id] || reply.ai_draft_response;
    if (!textToSend || !textToSend.trim()) {
      showNotice('Введите текст ответа клиенту', 'error');
      return;
    }

    setSendingId(reply.id);
    try {
      await sendInboxResponse(reply.id, {
        response_body: textToSend.trim(),
        subject: `Re: ${reply.subject || 'Ответ'}`
      });
      setReplies(prev => prev.map(r => r.id === reply.id ? { ...r, is_handled: true } : r));
      setRespondingId(null);
      showNotice(`Ответ успешно отправлен на ${reply.from_email}!`, 'success');
    } catch (err) {
      showNotice(err.message || 'Ошибка отправки ответа', 'error');
    } finally {
      setSendingId(null);
    }
  };

  const handleSimulateSubmit = async (e) => {
    e.preventDefault();
    if (!simLeadId) {
      showNotice('Выберите лида для симуляции', 'error');
      return;
    }
    if (!simMessage.trim()) {
      showNotice('Введите текст сообщения', 'error');
      return;
    }

    setSimulating(true);
    try {
      const res = await simulateInboundReply({
        lead_id: simLeadId,
        message_body: simMessage.trim()
      });
      setIsSimulateModalOpen(false);
      loadReplies();
      showNotice(`Ответ обработан ИИ! Интенция: ${res.intent}`, 'success');
    } catch (err) {
      showNotice(err.message || 'Ошибка симуляции', 'error');
    } finally {
      setSimulating(false);
    }
  };

  const getIntentBadge = (intent) => {
    switch (intent) {
      case 'INTERESTED':
        return (
          <span className="inline-flex items-center space-x-1 text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-semibold">
            <Flame className="w-3 h-3 text-amber-400" />
            <span>🔥 Горячий интерес</span>
          </span>
        );
      case 'OBJECTION':
        return (
          <span className="inline-flex items-center space-x-1 text-xs px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 font-semibold">
            <HelpCircle className="w-3 h-3" />
            <span>Возражение</span>
          </span>
        );
      case 'QUESTION':
        return (
          <span className="inline-flex items-center space-x-1 text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/20 font-semibold">
            <HelpCircle className="w-3 h-3" />
            <span>Уточняющий вопрос</span>
          </span>
        );
      case 'UNSUBSCRIBE':
        return (
          <span className="inline-flex items-center space-x-1 text-xs px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-semibold">
            <Slash className="w-3 h-3" />
            <span>Отказ / Отписка</span>
          </span>
        );
      case 'OUT_OF_OFFICE':
        return (
          <span className="inline-flex items-center space-x-1 text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-semibold">
            <Clock className="w-3 h-3" />
            <span>Автоответчик</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400">
            <span>Нейтрально</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-600 text-white flex items-center justify-center shadow-lg shadow-emerald-600/20">
              <Inbox className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">Smart Inbox (Входящие ответы & ИИ-реакция)</h2>
              <p className="text-xs text-slate-400">
                Детекция входящих писем, мгновенная классификация намерений через ИИ и автогенерация ответов
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              onClick={() => setIsSimulateModalOpen(true)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center space-x-2 transition-all"
            >
              <Play className="w-3.5 h-3.5 text-emerald-400" />
              <span>Симулировать входящий ответ</span>
            </button>

            <button
              onClick={loadReplies}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-200 bg-slate-800 border border-slate-700 transition-colors"
              title="Обновить входящие"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Intent Filter Tabs */}
        <div className="flex flex-wrap items-center gap-2 mt-6 pt-5 border-t border-slate-800">
          {[
            { id: '', label: 'Все ответы' },
            { id: 'INTERESTED', label: '🔥 Горячий интерес' },
            { id: 'QUESTION', label: '❓ Вопросы' },
            { id: 'OBJECTION', label: '💡 Возражения' },
            { id: 'UNSUBSCRIBE', label: '🛑 Отписки' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setIntentFilter(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                intentFilter === tab.id
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
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

      {/* Replies List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-emerald-400" />
          <p className="text-xs">Загрузка входящих писем...</p>
        </div>
      ) : replies.length === 0 ? (
        <div className="border border-dashed border-slate-800 rounded-2xl p-12 text-center space-y-4 bg-slate-900/20">
          <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <Inbox className="w-7 h-7" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-slate-200">Входящих ответов пока нет</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Когда адресат ответит на отправленное письмо, сообщение автоматически появится здесь с готовым драфтом ответа от ИИ.
            </p>
          </div>
          <button
            onClick={() => setIsSimulateModalOpen(true)}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 transition-all inline-flex items-center space-x-2"
          >
            <Play className="w-3.5 h-3.5 text-emerald-400" />
            <span>Протестировать через симуляцию</span>
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          {replies.map((reply) => {
            const isHandled = reply.is_handled;
            const currentResponseText = responseTextMap[reply.id] ?? (reply.ai_draft_response || '');

            return (
              <div
                key={reply.id}
                className="bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 shadow-lg space-y-4"
              >
                
                {/* Header: Lead info & Intent */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                  <div className="flex items-center space-x-3">
                    <div className="space-y-0.5">
                      <div className="flex items-center space-x-2">
                        <Building className="w-4 h-4 text-emerald-400" />
                        <h4 className="text-sm font-bold text-slate-100">{reply.company_name}</h4>
                        {reply.city && (
                          <span className="text-[11px] text-slate-400">({reply.city})</span>
                        )}
                      </div>
                      <span className="text-xs font-mono text-slate-400 block">{reply.from_email}</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {getIntentBadge(reply.intent)}
                    {isHandled ? (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-medium">
                        Обработано
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 font-semibold border border-amber-500/20">
                        Ожидает ответа
                      </span>
                    )}
                  </div>
                </div>

                {/* Body split: Inbound Message vs AI Assistant */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                  
                  {/* Left: Customer Inbound Message */}
                  <div className="lg:col-span-6 space-y-2">
                    <span className="text-[10px] font-mono text-slate-400 uppercase block">
                      Входящее сообщение клиента:
                    </span>
                    <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 text-xs text-slate-200 whitespace-pre-wrap leading-relaxed min-h-[120px]">
                      {reply.message_body}
                    </div>

                    {reply.ai_analysis && (
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 text-[11px] text-slate-400">
                        <span className="font-semibold text-slate-300 block mb-0.5">🔍 Анализ намерения:</span>
                        <p>{reply.ai_analysis}</p>
                      </div>
                    )}
                  </div>

                  {/* Right: AI Smart Reply Draft */}
                  <div className="lg:col-span-6 space-y-2 flex flex-col justify-between">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono text-purple-400 uppercase flex items-center space-x-1">
                          <Sparkles className="w-3 h-3" />
                          <span>Предложенный ответ от ИИ:</span>
                        </span>
                        {isHandled && (
                          <span className="text-[11px] text-emerald-400 flex items-center space-x-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Ответ отправлен</span>
                          </span>
                        )}
                      </div>

                      <textarea
                        rows={5}
                        disabled={isHandled}
                        value={currentResponseText}
                        onChange={(e) => setResponseTextMap(prev => ({ ...prev, [reply.id]: e.target.value }))}
                        placeholder="Текст ответа клиенту..."
                        className="w-full bg-slate-950/90 border border-purple-500/30 text-xs text-slate-100 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-purple-500/50 font-sans leading-relaxed resize-none disabled:opacity-60"
                      />
                    </div>

                    {!isHandled && (
                      <div className="flex justify-end pt-2">
                        <button
                          onClick={() => handleSendResponse(reply)}
                          disabled={sendingId === reply.id}
                          className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-md shadow-emerald-600/20 flex items-center space-x-1.5 transition-all"
                        >
                          {sendingId === reply.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <CornerDownLeft className="w-3.5 h-3.5" />
                          )}
                          <span>Отправить ответ клиенту</span>
                        </button>
                      </div>
                    )}

                  </div>

                </div>

              </div>
            );
          })}
        </div>
      )}

      {/* Simulator Modal */}
      {isSimulateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0f172a] border border-slate-700/80 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div className="flex items-center space-x-2">
                <Play className="w-4 h-4 text-emerald-400" />
                <h3 className="text-base font-semibold text-slate-100">Симуляция ответа клиента</h3>
              </div>
              <button onClick={() => setIsSimulateModalOpen(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSimulateSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">От какого лида пришел ответ:</label>
                <select
                  value={simLeadId}
                  onChange={(e) => setSimLeadId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-100 rounded-xl px-3 py-2"
                >
                  {leadsForSim.map(l => (
                    <option key={l.id} value={l.id}>{l.company_name} ({l.city})</option>
                  ))}
                  {leadsForSim.length === 0 && (
                    <option value="">Нет лидов в текущем проекте</option>
                  )}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Текст ответа:</label>
                <div className="flex flex-wrap gap-1 mb-2">
                  {[
                    "Да, нам интересно! Сколько стоит внедрение?",
                    "Сейчас нет бюджета, напишите через полгода.",
                    "Пожалуйста, удалите наш адрес из вашей рассылки."
                  ].map((preset, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setSimMessage(preset)}
                      className="text-[10px] px-2 py-0.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 truncate max-w-xs"
                    >
                      {preset}
                    </button>
                  ))}
                </div>
                <textarea
                  rows={4}
                  value={simMessage}
                  onChange={(e) => setSimMessage(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-100 rounded-xl p-3 resize-none"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsSimulateModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={simulating || !simLeadId}
                  className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 flex items-center space-x-1.5"
                >
                  {simulating && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Прогнать через ИИ</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
