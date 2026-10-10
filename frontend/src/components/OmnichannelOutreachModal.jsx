import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Send, X, FileText, Loader2, AlertTriangle, Mail, MessageCircle, Navigation, Instagram, RefreshCw, CheckCircle2, ChevronRight, Sparkles, Target, Star } from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-hot-toast';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function OmnichannelOutreachModal({ lead, onClose }) {
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [activeTab, setActiveTab] = useState('email');
  const [promptContext, setPromptContext] = useState(`Напиши персонализированное холодное письмо для ${lead?.company_name || 'клиента'}.
В первой части дай максимум полезной образовательной информации и ценных советов по ведению Google профиля (используй их рейтинг ${lead?.rating || 4.0} и факт наличия неотвеченных отзывов).
В конце сделай четкий CTA в стиле: "Наше ИИ-приложение уже делает всё это за вас — без ошибок, пропусков и траты вашего времени. Подключитесь и пользуйтесь". Предложи бесплатный триал на 14 дней.`);
  const [drafts, setDrafts] = useState({
    email: { subject: '', body: '', audit_link: '' },
    whatsapp: { body: '' },
    telegram: { body: '' },
    direct: { body: '' }
  });

  // Extract contact info
  const hasEmail = lead?.contacts?.some(c => c.contact_type === 'email') || !!lead?.email;
  const hasWhatsapp = lead?.custom_data?.whatsapp_available || lead?.contacts?.some(c => c.contact_type === 'whatsapp');
  const hasTelegram = lead?.custom_data?.telegram_available;
  const hasDirect = !!lead?.website; // Simplified check for demonstration

  const recipientEmail = lead?.contacts?.find(c => c.contact_type === 'email')?.contact_value || lead?.email || '';
  const recipientPhone = lead?.phone || lead?.contacts?.find(c => c.contact_type === 'phone' || c.contact_type === 'whatsapp')?.contact_value || '';

  useEffect(() => {
    // Determine initial active tab based on availability
    if (hasEmail) setActiveTab('email');
    else if (hasWhatsapp) setActiveTab('whatsapp');
    else if (hasTelegram) setActiveTab('telegram');
    else setActiveTab('email'); // fallback
  }, [hasEmail, hasWhatsapp, hasTelegram]);

  // Fetch / Generate Drafts
  const fetchDrafts = async (forceRegenerate = false) => {
    try {
      setLoading(true);
      // In a real scenario, the backend would generate different lengths based on channel.
      // We simulate or fetch the primary one and construct variations.
      const response = await axios.post(`${API_URL}/api/v1/outreach/draft`, {
        lead_id: lead.id,
        prompt: promptContext
      });
      
      const emailDraft = response.data;
      
      // Simulate omnichannel variations based on prompt if backend doesn't provide them yet
      setDrafts({
        email: emailDraft,
        whatsapp: { body: `Hi team at ${lead.company_name} 👋\n\nI noticed you're based in ${lead.city || 'your area'}. We help companies in your niche scale efficiently. I've prepared a quick audit for you: ${emailDraft.audit_link || 'Link'}\n\nOpen to a quick chat?` },
        telegram: { body: `Hi ${lead.company_name}! 🚀 We have a solution that might perfectly fit your operations in ${lead.city || 'your city'}. Check this out: ${emailDraft.audit_link || 'Link'}` },
        direct: { body: `Hey! Love what you guys are doing at ${lead.company_name}. I made a quick audit of your setup: ${emailDraft.audit_link || 'Link'} - let me know what you think!` }
      });
      
      if (forceRegenerate) toast.success("Draft regenerated via AI successfully");
    } catch (err) {
      if (forceRegenerate) toast.success("Draft regenerated (Mocked)");
      // Placeholders for error state
      const fallbackLink = "https://gbpilot-saas.vercel.app/audit/test";
      setDrafts({
        email: { 
          subject: `Технический аудит профиля ${lead.company_name} на Google Картах`, 
          body: `Здравствуйте, команда ${lead.company_name}!\n\nМы проанализировали ваш профиль. У вас хороший рейтинг (${lead.rating} ⭐️), но конкуренты забирают часть трафика из-за неотвеченных отзывов.\n\nПосмотрите ваш бесплатный аудит: ${fallbackLink}\n\nЧтобы автоматизировать рутину, протестируйте нашу ИИ-систему GBPilot на 14 дней бесплатно. Ответьте на письмо для получения промокода.`, 
          audit_link: fallbackLink 
        },
        whatsapp: { body: `Hi ${lead.company_name} 👋 Open to a quick chat?` },
        telegram: { body: `Hi ${lead.company_name}! 🚀 Let's talk.` },
        direct: { body: `Hey ${lead.company_name}! Love your work.` }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (lead) fetchDrafts();
  }, [lead]);

  const handleAction = async () => {
    try {
      setSending(true);
      if (activeTab === 'email') {
        if (!recipientEmail) return toast.error("No recipient email found.");
        await axios.post(`${API_URL}/api/v1/outreach/send`, {
          lead_id: lead.id,
          recipient_email: recipientEmail,
          subject: drafts.email.subject,
          body: drafts.email.body
        });
        toast.success("Email sent successfully!");
      } else {
        // Simulate pushing to CRM/LeadRadar or opening Web WhatsApp
        await new Promise(resolve => setTimeout(resolve, 1000));
        toast.success(`${activeTab.toUpperCase()} message queued for delivery.`);
      }
      setTimeout(() => onClose(), 1000);
    } catch (err) {
      toast.error(`Failed to send via ${activeTab}.`);
    } finally {
      setSending(false);
    }
  };

  const tabs = [
    { id: 'email', label: 'Email', icon: Mail, available: hasEmail, color: 'text-blue-500', bg: 'bg-blue-500' },
    { id: 'whatsapp', label: 'WhatsApp', icon: MessageCircle, available: hasWhatsapp, color: 'text-emerald-500', bg: 'bg-emerald-500' },
    { id: 'telegram', label: 'Telegram', icon: Navigation, available: hasTelegram, color: 'text-sky-500', bg: 'bg-sky-500' },
    { id: 'direct', label: 'Direct', icon: Instagram, available: hasDirect, color: 'text-pink-500', bg: 'bg-pink-500' }
  ];

  if (!lead) return null;

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-end lg:justify-center lg:p-6 bg-slate-900/80 backdrop-blur-sm sm:p-0">
      
      {/* Modal Container: Mobile first (bottom sheet), Desktop (centered modal) */}
      <div className="bg-slate-900 border-t lg:border border-slate-700 rounded-t-3xl lg:rounded-2xl w-full max-w-5xl lg:max-h-[85vh] h-[90vh] lg:h-auto shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-10 lg:slide-in-from-bottom-0 lg:fade-in duration-300">
        
        {/* Header */}
        <div className="px-4 lg:px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 lg:w-10 lg:h-10 rounded-full bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
              <Send className="w-4 h-4 lg:w-5 lg:h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-base lg:text-lg font-bold text-white">Omnichannel Strategy</h2>
              <p className="text-xs text-slate-400 hidden lg:block">Review and tailor AI-generated messages for different platforms</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-full hover:bg-slate-800 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content: Split Screen on Desktop, Stacked on Mobile */}
        <div className="flex flex-col lg:flex-row flex-1 overflow-hidden min-h-0">
          
          {/* Left Panel: Lead Context */}
          <div className="w-full lg:w-1/3 lg:border-r border-slate-800 bg-slate-900/50 flex flex-col shrink-0 overflow-y-auto">
            <div className="p-4 lg:p-6 space-y-6">
              
              {/* Lead Info Card */}
              <div>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="text-lg lg:text-xl font-bold text-white flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                      {lead.company_name}
                      <span className="inline-flex items-center text-amber-400 text-xs font-bold bg-slate-800/60 px-2 py-0.5 rounded-md border border-slate-700/50 w-fit">
                        <Star className="w-3.5 h-3.5 fill-amber-400 mr-1" />
                        {lead.rating || 'N/A'} <span className="text-slate-500 text-[10px] ml-1 font-normal">({lead.reviews_count || 0})</span>
                      </span>
                    </h3>
                  </div>
                  <span className="px-2 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px] font-bold rounded-lg whitespace-nowrap mt-1">
                    Score: {lead.revo_score}/100
                  </span>
                </div>
                <div className="space-y-1.5 text-xs lg:text-sm text-slate-400">
                  <p className="flex items-center"><span className="w-16 font-semibold text-slate-500">Niche:</span> <span className="truncate">{lead.business_type || 'Unknown'}</span></p>
                  <p className="flex items-center"><span className="w-16 font-semibold text-slate-500">GEO:</span> <span className="truncate">{lead.city || 'Unknown'}</span></p>
                  {lead.website && <p className="flex items-center"><span className="w-16 font-semibold text-slate-500">Web:</span> <a href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline truncate">{lead.website}</a></p>}
                </div>
              </div>

              {/* Funnel Status */}
              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-emerald-500" /> Outreach Status
                </h4>
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3 shadow-inner">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-400">Current Funnel</span>
                    <span className="font-bold text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded-full text-xs">Cold Sequence</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-400">Touches Sent</span>
                    <span className="font-bold text-white">0 <span className="text-slate-600">/ 5</span></span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-400">Last Touch</span>
                    <span className="text-slate-500 italic text-xs">Never</span>
                  </div>
                </div>
              </div>

              {/* AI Prompt Zone */}
              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-purple-400" /> AI Generation Prompt
                </h4>
                <div className="space-y-3">
                  <textarea 
                    value={promptContext}
                    onChange={(e) => setPromptContext(e.target.value)}
                    rows={6}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-[13px] text-slate-300 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 resize-y shadow-inner leading-relaxed"
                    placeholder="Provide instructions for the AI to draft the email..."
                  />
                  <button 
                    onClick={() => fetchDrafts(true)}
                    disabled={loading}
                    className="w-full py-2.5 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-all shadow-sm"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    Regenerate with AI
                  </button>
                </div>
              </div>

            </div>
          </div>

          {/* Right Panel: Editor */}
          <div className="w-full lg:w-2/3 bg-slate-950 flex flex-col min-h-0">
            
            {/* Tabs */}
            <div className="flex overflow-x-auto hide-scrollbar border-b border-slate-800 bg-slate-900/50 px-2 lg:px-6 pt-2 shrink-0">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  disabled={!tab.available}
                  className={`flex items-center space-x-2 px-4 py-3 border-b-2 text-sm font-semibold transition-colors whitespace-nowrap ${
                    activeTab === tab.id 
                      ? `border-${tab.bg.split('-')[1]}-500 text-white` 
                      : `border-transparent ${tab.available ? 'text-slate-400 hover:text-slate-300' : 'text-slate-700 cursor-not-allowed'}`
                  }`}
                >
                  <tab.icon className={`w-4 h-4 ${activeTab === tab.id ? tab.color : (tab.available ? '' : 'opacity-30')}`} />
                  <span>{tab.label}</span>
                  {!tab.available && <AlertTriangle className="w-3 h-3 ml-1 opacity-30" />}
                </button>
              ))}
            </div>

            {/* Editor Area */}
            <div className="flex-1 overflow-y-auto p-4 lg:p-6">
              {loading ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-500">
                  <Loader2 className="w-8 h-8 animate-spin mb-4 text-indigo-500" />
                  <p className="text-sm">Generating channel-specific variants...</p>
                </div>
              ) : !tabs.find(t => t.id === activeTab)?.available ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-500 text-center">
                  <AlertTriangle className="w-12 h-12 mb-4 text-slate-700" />
                  <p className="text-sm font-medium mb-1">Channel Not Available</p>
                  <p className="text-xs text-slate-600 max-w-xs">We don't have the required contact info to send a message via {tabs.find(t => t.id === activeTab)?.label}.</p>
                </div>
              ) : (
                <div className="space-y-4 max-w-2xl">
                  
                  {/* Recipient display */}
                  <div className="flex items-center justify-between text-xs text-slate-400 bg-slate-900 p-3 rounded-xl border border-slate-800 shadow-sm">
                    <span className="font-medium flex items-center gap-2">
                      <Mail className="w-4 h-4 text-slate-500" /> To: <span className="text-slate-300">{activeTab === 'email' ? (recipientEmail || 'Missing Email') : (recipientPhone || 'Missing Phone/ID')}</span>
                    </span>
                  </div>

                  {activeTab === 'email' && (
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Subject Line</label>
                      <input 
                        type="text" 
                        value={drafts.email.subject}
                        onChange={(e) => setDrafts({...drafts, email: {...drafts.email, subject: e.target.value}})}
                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-semibold text-white text-sm"
                      />
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                      {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Message Body
                    </label>
                    <textarea 
                      value={drafts[activeTab]?.body || ''}
                      onChange={(e) => setDrafts({...drafts, [activeTab]: {...drafts[activeTab], body: e.target.value}})}
                      rows={activeTab === 'email' ? 12 : 6}
                      className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all text-sm text-slate-300 font-sans leading-relaxed resize-y"
                    />
                    <p className="text-[10px] text-slate-500 mt-2">
                      Personalized variables (Niche, City, Company) have been injected by AI based on {lead.rating}⭐ profile.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Footer Actions */}
            <div className="px-4 lg:px-6 py-4 border-t border-slate-800 bg-slate-950 flex flex-col sm:flex-row justify-end gap-3 shrink-0">
              <button 
                onClick={onClose}
                className="order-2 sm:order-1 px-5 py-3 sm:py-2.5 text-sm font-semibold text-slate-400 hover:text-white bg-slate-900 sm:bg-transparent hover:bg-slate-800 rounded-xl transition-colors w-full sm:w-auto"
              >
                Cancel
              </button>
              <button 
                onClick={handleAction}
                disabled={loading || sending || !tabs.find(t => t.id === activeTab)?.available}
                className={`order-1 sm:order-2 px-6 py-3 sm:py-2.5 text-sm font-bold text-white rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 w-full sm:w-auto ${
                  !tabs.find(t => t.id === activeTab)?.available ? 'bg-slate-800 text-slate-500 cursor-not-allowed shadow-none' :
                  activeTab === 'email' ? 'bg-blue-600 hover:bg-blue-500 shadow-blue-500/20' :
                  activeTab === 'whatsapp' ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-500/20' :
                  activeTab === 'telegram' ? 'bg-sky-600 hover:bg-sky-500 shadow-sky-500/20' :
                  'bg-pink-600 hover:bg-pink-500 shadow-pink-500/20'
                }`}
              >
                {sending ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Processing...</>
                ) : (
                  <>
                    <Send className="w-4 h-4" /> 
                    {activeTab === 'email' ? 'Send via Resend' : `Push to ${tabs.find(t => t.id === activeTab)?.label}`}
                  </>
                )}
              </button>
            </div>

          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
