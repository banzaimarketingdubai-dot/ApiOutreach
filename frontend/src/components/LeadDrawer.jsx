import React from 'react';
import { X, ExternalLink, Star, Phone, Mail, MessageSquare, Globe, ShieldAlert, CheckCircle, Copy } from 'lucide-react';

export default function LeadDrawer({ lead, onClose }) {
  if (!lead) return null;

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert(`Copied: ${text}`);
  };

  const phones = (lead.contacts || []).filter(c => c.contact_type === 'phone');
  const emails = (lead.contacts || []).filter(c => c.contact_type === 'email');
  const customData = lead.custom_data || {};

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/60 backdrop-blur-sm animate-fade-in">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col">
          
          {/* Header */}
          <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-950/40">
            <div>
              <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 mb-2 inline-block">
                Golden Record Card
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">{lead.company_name}</h2>
              <p className="text-xs text-slate-400 mt-1">{lead.business_type} • {lead.city}</p>
            </div>
            <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
            
            {/* Quick Stats & Links */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">Revo Lead Score</span>
                <span className="text-2xl font-extrabold text-amber-400">{lead.revo_score}/100</span>
              </div>
              <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">Google Rating</span>
                <div className="flex items-center space-x-1 mt-1">
                  <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                  <span className="text-lg font-bold text-white">{lead.rating}</span>
                  <span className="text-slate-500 text-[10px]">({lead.reviews_count} reviews)</span>
                </div>
              </div>
            </div>

            {/* Website & Address */}
            <div className="space-y-2">
              <span className="font-semibold text-slate-400 block uppercase tracking-wider text-[10px]">Location & Web</span>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                <p className="text-slate-300">
                  <strong>Address:</strong>{' '}
                  {lead.address ? (
                    <a href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(lead.company_name + ' ' + (lead.city || '') + ' ' + lead.address)}`} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">
                      {lead.address}
                    </a>
                  ) : 'N/A'}
                </p>
                {lead.website && (
                  <p className="text-slate-300 flex items-center space-x-1">
                    <strong>Website:</strong>
                    <a
                      href={lead.website.startsWith && lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-400 hover:underline inline-flex items-center ml-1"
                    >
                      <span>{lead.website}</span>
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </p>
                )}
              </div>
            </div>

            {/* Verified Contacts */}
            <div className="space-y-2">
              <span className="font-semibold text-slate-400 block uppercase tracking-wider text-[10px]">Extracted Contacts</span>
              <div className="space-y-2">
                {lead.contacts && lead.contacts.length > 0 ? (
                  lead.contacts.map((c) => {
                    let href = "#";
                    if (c.contact_type === 'phone') href = `tel:${c.contact_value}`;
                    if (c.contact_type === 'email') href = `mailto:${c.contact_value}`;
                    if (c.contact_type === 'whatsapp') {
                       const digits = c.contact_value.replace(/\D/g,'');
                       href = `https://wa.me/${digits}`;
                    }
                    if (c.contact_type === 'telegram') {
                       const handle = c.contact_value.replace('@','');
                       href = `https://t.me/${handle}`;
                    }

                    return (
                      <div key={c.id} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                        <div className="flex items-center space-x-2">
                          {c.contact_type === 'phone' && <Phone className="w-4 h-4 text-emerald-400" />}
                          {c.contact_type === 'email' && <Mail className="w-4 h-4 text-blue-400" />}
                          {c.contact_type === 'whatsapp' && <MessageSquare className="w-4 h-4 text-teal-400" />}
                          <a href={href} target="_blank" rel="noreferrer" className="font-mono text-blue-400 hover:underline text-xs">
                            {c.contact_value}
                          </a>
                          <span className="text-[10px] text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded">
                            {c.source}
                          </span>
                        </div>
                        <button
                          onClick={() => copyToClipboard(c.contact_value)}
                          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
                        >
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-slate-500 italic">No standard contacts extracted yet.</p>
                )}
              </div>
            </div>

            {/* Revo Audit Note */}
            {lead.audit_notes && (
              <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/20 space-y-1">
                <span className="font-bold text-amber-400 flex items-center space-x-1.5">
                  <ShieldAlert className="w-4 h-4" />
                  <span>Revo Pitch Audit Notes</span>
                </span>
                <p className="text-slate-300 leading-relaxed">{lead.audit_notes}</p>
              </div>
            )}

            {/* Custom LLM Extracted Data (JSONB) */}
            <div className="space-y-2">
              <span className="font-semibold text-slate-400 block uppercase tracking-wider text-[10px]">Smart LLM Enriched Custom Variables</span>
              <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 font-mono text-[11px] overflow-x-auto text-amber-300">
                <pre>{JSON.stringify(customData, null, 2)}</pre>
              </div>
            </div>

            {/* AI Action Logs (Terminal Style) */}
            <div className="space-y-2">
              <span className="font-semibold text-slate-400 block uppercase tracking-wider text-[10px] flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-fuchsia-500 animate-pulse"></span>
                <span>Live AI Enrichment Log</span>
              </span>
              <div className="p-4 rounded-2xl bg-[#0a0a0a] border border-slate-800 font-mono text-[11px] overflow-y-auto max-h-48 text-slate-300 space-y-2">
                <div className="text-slate-500">[{new Date().toISOString()}] [INFO] Starting deep analysis for {lead.company_name}...</div>
                {lead.website ? (
                  <>
                    <div className="text-emerald-400">[{new Date().toISOString()}] [SUCCESS] Successfully connected to {lead.website}</div>
                    <div className="text-slate-500">[{new Date().toISOString()}] [INFO] Scraping DOM and converting to Markdown...</div>
                    {lead.custom_data?.enrichment_status === 'in_progress' && (
                      <div className="text-blue-400 animate-pulse">[{new Date().toISOString()}] [PROCESSING] AI is currently analyzing the content...</div>
                    )}
                    {lead.custom_data?.enrichment_status === 'completed' && (
                      <>
                        <div className="text-slate-300">[{new Date().toISOString()}] [AI_REASONING] Checked contact pages. Emails found: {emails.length}. Phone numbers found: {phones.length}.</div>
                        {emails.length === 0 && (
                          <div className="text-amber-400">[{new Date().toISOString()}] [WARNING] No email addresses were found on the website. Fallback to social media parsing recommended.</div>
                        )}
                        <div className="text-emerald-400">[{new Date().toISOString()}] [SUCCESS] Enrichment workflow completed successfully.</div>
                      </>
                    )}
                    {lead.custom_data?.enrichment_status === 'failed' && (
                      <div className="text-red-400">[{new Date().toISOString()}] [ERROR] Website blocked access or returned empty HTML. AI analysis aborted.</div>
                    )}
                    {lead.custom_data?.enrichment_status === 'no_website' && (
                      <div className="text-slate-400">[{new Date().toISOString()}] [WARNING] No website provided. Skipped.</div>
                    )}
                    {lead.custom_data?.enrichment_status === 'social_only' && (
                      <div className="text-pink-400">[{new Date().toISOString()}] [WARNING] Social media link ignored. Requires specialized scraper.</div>
                    )}
                  </>
                ) : (
                  <div className="text-red-400">[{new Date().toISOString()}] [ERROR] No website provided. Aborting AI enrichment.</div>
                )}
                {lead.custom_data?.ai_logs && (Array.isArray(lead.custom_data.ai_logs) ? lead.custom_data.ai_logs : [lead.custom_data.ai_logs]).map((log, idx) => {
                  const isOld = lead.custom_data.enrichment_status === 'in_progress';
                  return (
                    <div key={idx} className={isOld ? "text-slate-500" : "text-fuchsia-400"}>
                      [AI_CUSTOM] {log} {isOld && "(from previous run)"}
                    </div>
                  );
                })}
              </div>
            </div>

          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-800 bg-slate-950/50 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium"
            >
              Close Drawer
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
