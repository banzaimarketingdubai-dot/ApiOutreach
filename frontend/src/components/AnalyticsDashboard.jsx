import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, 
  AreaChart, Area 
} from 'recharts';
import { 
  Loader2, TrendingUp, MailOpen, MousePointerClick, Reply, Send, 
  Flame, Users, Package, RefreshCw, Filter, Layers, CheckCircle2,
  AlertTriangle, ShieldCheck, HelpCircle, UserX, ArrowRight
} from 'lucide-react';
import { fetchAnalytics, fetchProducts, fetchAudiences } from '../services/api';

export default function AnalyticsDashboard({ currentProjectId, projects = [], globalCampaignId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sub-filters within the project
  const [products, setProducts] = useState([]);
  const [audiences, setAudiences] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedAudienceId, setSelectedAudienceId] = useState('');

  const currentProject = projects.find(p => p.id === currentProjectId);

  // Load project filters
  useEffect(() => {
    if (!currentProjectId) return;
    fetchProducts(currentProjectId)
      .then(p => setProducts(p || []))
      .catch(console.error);
    fetchAudiences(currentProjectId)
      .then(a => setAudiences(a || []))
      .catch(console.error);
    setSelectedProductId('');
    setSelectedAudienceId('');
  }, [currentProjectId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        project_id: currentProjectId || undefined,
        campaign_id: globalCampaignId || undefined,
        product_id: selectedProductId || undefined,
        audience_id: selectedAudienceId || undefined
      };
      const res = await fetchAnalytics(params);
      setData(res);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки аналитики');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentProjectId, globalCampaignId, selectedProductId, selectedAudienceId]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-[65vh] space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-slate-400 font-medium text-sm">Сбор и расчет проектной статистики конверсий...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-8 flex items-center justify-center h-[65vh]">
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-6 rounded-2xl flex flex-col items-center max-w-md text-center">
          <AlertTriangle className="w-8 h-8 mb-2 text-rose-400" />
          <p className="font-bold mb-1">Ошибка загрузки аналитики</p>
          <p className="text-xs text-rose-300/80 mb-4">{error}</p>
          <button 
            onClick={loadData} 
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-white text-xs transition-colors"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  const overall = data?.overall || { sent: 0, opened: 0, clicked: 0, replied: 0, interested: 0, bounced: 0, open_rate: 0, click_rate: 0, reply_rate: 0, hot_rate: 0 };
  const funnels = data?.funnels || [];
  const touches = data?.touches || [];
  const byProduct = data?.by_product || [];
  const byAudience = data?.by_audience || [];
  const intents = data?.intents || [];

  const kpiCards = [
    { 
      title: 'Отправлено писем', 
      value: overall.sent, 
      subtext: `Всего в очереди: ${overall.total_sequences || overall.sent}`, 
      icon: <Send className="w-5 h-5 text-blue-400" />, 
      color: 'from-blue-600/20 to-blue-900/10', 
      border: 'border-blue-500/30' 
    },
    { 
      title: 'Open Rate (Открытия)', 
      value: `${overall.open_rate || 0}%`, 
      subtext: `${overall.opened} открыто получателями`, 
      icon: <MailOpen className="w-5 h-5 text-emerald-400" />, 
      color: 'from-emerald-600/20 to-emerald-900/10', 
      border: 'border-emerald-500/30' 
    },
    { 
      title: 'Click Rate (Переходы)', 
      value: `${overall.click_rate || 0}%`, 
      subtext: `${overall.clicked} кликов по ссылкам`, 
      icon: <MousePointerClick className="w-5 h-5 text-purple-400" />, 
      color: 'from-purple-600/20 to-purple-900/10', 
      border: 'border-purple-500/30' 
    },
    { 
      title: 'Reply Rate (Ответы)', 
      value: `${overall.reply_rate || 0}%`, 
      subtext: `${overall.replied} прямых ответов`, 
      icon: <Reply className="w-5 h-5 text-amber-400" />, 
      color: 'from-amber-600/20 to-amber-900/10', 
      border: 'border-amber-500/30' 
    },
    { 
      title: 'Горячие лиды (Hot)', 
      value: overall.interested || 0, 
      subtext: `${overall.hot_rate || 0}% от отправленных`, 
      icon: <Flame className="w-5 h-5 text-emerald-400" />, 
      color: 'from-emerald-600/30 to-teal-900/20', 
      border: 'border-emerald-500/40' 
    },
    { 
      title: 'Bounced / Ошибки', 
      value: overall.bounced || 0, 
      subtext: 'Не доставленные адреса', 
      icon: <UserX className="w-5 h-5 text-rose-400" />, 
      color: 'from-rose-600/20 to-rose-900/10', 
      border: 'border-rose-500/30' 
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      
      {/* Top Controls Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur-sm">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white flex items-center space-x-2">
                <span>Аналитика рассылок</span>
                {currentProject && (
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {currentProject.name}
                  </span>
                )}
              </h1>
              <p className="text-xs text-slate-400">
                Конверсионная воронка касаний, сегментация по продуктам и классификация входящих ответов
              </p>
            </div>
          </div>
        </div>

        {/* Filter Selectors */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Product Filter */}
          {products.length > 0 && (
            <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-700/80 rounded-xl px-2.5 py-1.5 text-xs">
              <Package className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
              <select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                className="bg-transparent text-slate-200 focus:outline-none cursor-pointer max-w-[140px] truncate"
              >
                <option value="" className="bg-slate-900 text-slate-300">Все продукты</option>
                {products.map(p => (
                  <option key={p.id} value={p.id} className="bg-slate-900 text-slate-200">{p.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Audience Filter */}
          {audiences.length > 0 && (
            <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-700/80 rounded-xl px-2.5 py-1.5 text-xs">
              <Users className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
              <select
                value={selectedAudienceId}
                onChange={(e) => setSelectedAudienceId(e.target.value)}
                className="bg-transparent text-slate-200 focus:outline-none cursor-pointer max-w-[140px] truncate"
              >
                <option value="" className="bg-slate-900 text-slate-300">Все аудитории</option>
                {audiences.map(a => (
                  <option key={a.id} value={a.id} className="bg-slate-900 text-slate-200">{a.name}</option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={loadData}
            title="Обновить аналитику"
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards Grid (6 metrics) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {kpiCards.map((card, idx) => (
          <div 
            key={idx} 
            className={`bg-gradient-to-br ${card.color} border ${card.border} rounded-2xl p-4 shadow-lg backdrop-blur-sm relative overflow-hidden group transition-transform duration-200 hover:-translate-y-0.5`}
          >
            <div className="absolute top-2 right-2 p-2 opacity-25 group-hover:opacity-40 transition-opacity">
              {card.icon}
            </div>
            <p className="text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1.5 truncate">
              {card.title}
            </p>
            <h3 className="text-2xl font-black text-white">{card.value}</h3>
            {card.subtext && (
              <p className="text-[11px] text-slate-400/90 mt-1 truncate">{card.subtext}</p>
            )}
          </div>
        ))}
      </div>

      {/* Smart Inbox Inbound Sentiment & Intent Analysis */}
      {intents.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Flame className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">Классификация входящих ответов (Smart Inbox)</h3>
            </div>
            <span className="text-xs text-slate-400">
              Всего ответов: {intents.reduce((acc, i) => acc + i.count, 0)}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {intents.map((item, idx) => (
              <div 
                key={idx} 
                className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300">{item.label}</span>
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-xl font-bold text-white">{item.count}</span>
                  <span 
                    className="w-2.5 h-2.5 rounded-full" 
                    style={{ backgroundColor: item.color }} 
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comparison Sections: By Product & By Audience */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Breakdown by Product */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Package className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-bold text-white">Результативность по Продуктам</h3>
              </div>
              <span className="text-[11px] text-slate-400">Отклик (Reply Rate)</span>
            </div>

            {byProduct.length === 0 ? (
              <div className="py-10 text-center text-xs text-slate-500">
                В этом проекте пока нет продуктов или по ним не запускались рассылки
              </div>
            ) : (
              <div className="space-y-3">
                {byProduct.map(p => (
                  <div key={p.product_id} className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 truncate">
                        <span className="text-xs font-bold text-slate-200 truncate">{p.name}</span>
                        {p.price_tier && (
                          <span className="text-[10px] px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20">
                            {p.price_tier}
                          </span>
                        )}
                      </div>
                      <span className="text-xs font-bold text-amber-400 ml-2">
                        {p.reply_rate}% отклик
                      </span>
                    </div>

                    <div className="grid grid-cols-4 gap-2 text-center text-[11px] bg-slate-900/60 rounded-lg p-2 border border-slate-800">
                      <div>
                        <span className="text-slate-500 block text-[10px]">Отправлено</span>
                        <span className="font-semibold text-slate-200">{p.sent}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Открыто</span>
                        <span className="font-semibold text-emerald-300">{p.opened}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Клики</span>
                        <span className="font-semibold text-purple-300">{p.clicked}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Ответы</span>
                        <span className="font-semibold text-amber-300">{p.replied}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Breakdown by Audience */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">Результативность по Аудиториям</h3>
              </div>
              <span className="text-[11px] text-slate-400">Отклик (Reply Rate)</span>
            </div>

            {byAudience.length === 0 ? (
              <div className="py-10 text-center text-xs text-slate-500">
                В этом проекте пока нет аудиторий или по ним не запускались рассылки
              </div>
            ) : (
              <div className="space-y-3">
                {byAudience.map(a => (
                  <div key={a.audience_id} className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 truncate">
                        <span className="text-xs font-bold text-slate-200 truncate">{a.name}</span>
                        <span className="text-[10px] text-slate-400">
                          ({a.total_leads || 0} лидов)
                        </span>
                      </div>
                      <span className="text-xs font-bold text-amber-400 ml-2">
                        {a.reply_rate}% отклик
                      </span>
                    </div>

                    <div className="grid grid-cols-4 gap-2 text-center text-[11px] bg-slate-900/60 rounded-lg p-2 border border-slate-800">
                      <div>
                        <span className="text-slate-500 block text-[10px]">Отправлено</span>
                        <span className="font-semibold text-slate-200">{a.sent}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Открыто</span>
                        <span className="font-semibold text-emerald-300">{a.opened}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Клики</span>
                        <span className="font-semibold text-purple-300">{a.clicked}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Ответы</span>
                        <span className="font-semibold text-amber-300">{a.replied}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Charts Row: Funnels & Touch-level Drop-off */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Performance by Touch (Multi-Touch Drop-off) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center space-x-2">
            <span>Воронка касаний (Drop-off по Touch 1..5)</span>
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={touches} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis 
                  dataKey="touch_level" 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(v) => `Touch ${v}`} 
                />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '12px' }}
                  itemStyle={{ fontSize: '12px' }}
                  cursor={{ fill: '#1e293b', opacity: 0.4 }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                <Bar dataKey="sent" name="Отправлено" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={18} />
                <Bar dataKey="opened" name="Открыто" fill="#10b981" radius={[4, 4, 0, 0]} barSize={18} />
                <Bar dataKey="replied" name="Ответов" fill="#f59e0b" radius={[4, 4, 0, 0]} barSize={18} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Audience Conversion Funnel Area */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm">
          <h3 className="text-sm font-bold text-white mb-4">
            Динамика конверсии по касаниям
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={touches} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorOpened" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorReplied" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis 
                  dataKey="touch_level" 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(v) => `Касание ${v}`} 
                />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '12px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                <Area type="monotone" dataKey="opened" name="Открытия" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorOpened)" />
                <Area type="monotone" dataKey="replied" name="Ответы" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#colorReplied)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

    </div>
  );
}
