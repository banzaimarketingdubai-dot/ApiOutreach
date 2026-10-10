import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, AreaChart, Area } from 'recharts';
import { Loader2, TrendingUp, MailOpen, MousePointerClick, Reply, Send } from 'lucide-react';
import { fetchAnalytics } from '../services/api';

export default function AnalyticsDashboard({ globalCampaignId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [globalCampaignId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchAnalytics(globalCampaignId);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] space-y-4">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
        <p className="text-slate-400 font-medium">Crunching conversion numbers...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 flex items-center justify-center h-[70vh]">
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-6 rounded-xl flex flex-col items-center max-w-md text-center">
          <p className="font-bold mb-2">Error</p>
          <p className="text-sm">{error}</p>
          <button onClick={loadData} className="mt-4 px-4 py-2 bg-slate-800 rounded-lg text-white text-xs hover:bg-slate-700">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { overall, funnels, touches } = data;

  const kpiCards = [
    { title: 'Total Sent', value: overall.sent, icon: <Send className="w-5 h-5 text-blue-400" />, color: 'from-blue-600/20 to-blue-900/10', border: 'border-blue-500/30' },
    { title: 'Open Rate', value: `${overall.sent ? Math.round((overall.opened / overall.sent) * 100) : 0}%`, subtext: `${overall.opened} opened`, icon: <MailOpen className="w-5 h-5 text-emerald-400" />, color: 'from-emerald-600/20 to-emerald-900/10', border: 'border-emerald-500/30' },
    { title: 'Click Rate', value: `${overall.opened ? Math.round((overall.clicked / overall.opened) * 100) : 0}%`, subtext: `${overall.clicked} clicked`, icon: <MousePointerClick className="w-5 h-5 text-purple-400" />, color: 'from-purple-600/20 to-purple-900/10', border: 'border-purple-500/30' },
    { title: 'Reply Rate', value: `${overall.sent ? Math.round((overall.replied / overall.sent) * 100) : 0}%`, subtext: `${overall.replied} replies`, icon: <Reply className="w-5 h-5 text-amber-400" />, color: 'from-amber-600/20 to-amber-900/10', border: 'border-amber-500/30' },
  ];

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center">
          <TrendingUp className="w-6 h-6 mr-3 text-blue-400" />
          Outreach Analytics
        </h1>
        <p className="text-slate-400 text-sm mt-1">Real-time performance tracking for your email sequences.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((card, idx) => (
          <div key={idx} className={`bg-gradient-to-br ${card.color} border ${card.border} rounded-2xl p-5 shadow-lg backdrop-blur-sm relative overflow-hidden group`}>
            <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-40 transition-opacity transform group-hover:scale-110 duration-300">
              {card.icon}
            </div>
            <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">{card.title}</p>
            <h3 className="text-3xl font-black text-white">{card.value}</h3>
            {card.subtext && <p className="text-xs text-slate-500 mt-1">{card.subtext}</p>}
          </div>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Funnel Performance (Bar Chart) */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-bold text-white mb-6">Performance by Audience (Funnel)</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnels} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                  cursor={{ fill: '#1e293b', opacity: 0.4 }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="sent" name="Sent" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={20} />
                <Bar dataKey="opened" name="Opened" fill="#10b981" radius={[4, 4, 0, 0]} barSize={20} />
                <Bar dataKey="clicked" name="Clicked" fill="#a855f7" radius={[4, 4, 0, 0]} barSize={20} />
                <Bar dataKey="replied" name="Replied" fill="#f59e0b" radius={[4, 4, 0, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Touch Level Drop-off (Area Chart) */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-bold text-white mb-6">Drop-off by Touch Level</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={touches} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorOpened" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorClicked" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="touch_level" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `Touch ${v}`} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
                <Area type="monotone" dataKey="opened" name="Opened" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorOpened)" />
                <Area type="monotone" dataKey="clicked" name="Clicked" stroke="#a855f7" strokeWidth={2} fillOpacity={1} fill="url(#colorClicked)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        
      </div>
    </div>
  );
}
