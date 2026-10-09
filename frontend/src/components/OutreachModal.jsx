import React, { useState, useEffect } from 'react';
import { Send, X, FileText, CheckCircle, ExternalLink, Loader2 } from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-hot-toast';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function OutreachModal({ lead, onClose }) {
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [draft, setDraft] = useState({ subject: '', body: '', audit_link: '' });
  const [recipient, setRecipient] = useState('');

  // Extract primary email if available
  useEffect(() => {
    if (lead && lead.contacts) {
      const emails = lead.contacts.filter(c => c.type === 'EMAIL');
      if (emails.length > 0) {
        setRecipient(emails[0].value);
      }
    }
  }, [lead]);

  // Fetch draft
  useEffect(() => {
    const fetchDraft = async () => {
      try {
        setLoading(true);
        const response = await axios.post(`${API_URL}/api/v1/outreach/draft`, {
          lead_id: lead.id
        });
        setDraft(response.data);
      } catch (err) {
        toast.error("Failed to generate draft. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    if (lead) fetchDraft();
  }, [lead]);

  const handleSend = async () => {
    if (!recipient) {
      toast.error("Please provide a recipient email address.");
      return;
    }

    try {
      setSending(true);
      await axios.post(`${API_URL}/api/v1/outreach/send`, {
        lead_id: lead.id,
        recipient_email: recipient,
        subject: draft.subject,
        body: draft.body
      });
      toast.success("Email sent successfully!");
      onClose();
    } catch (err) {
      toast.error("Failed to send email. Check API key or logs.");
    } finally {
      setSending(false);
    }
  };

  if (!lead) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
              <Send className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold">Draft Outreach Email</h2>
              <p className="text-xs text-blue-100 opacity-90">{lead.company_name} (Rating: {lead.rating}⭐)</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-white/70 hover:text-white rounded-full hover:bg-white/10 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 bg-gray-50/50">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <Loader2 className="w-8 h-8 animate-spin mb-4 text-blue-600" />
              <p>Analyzing profile and drafting hyper-personalized email...</p>
            </div>
          ) : (
            <div className="space-y-6">
              
              {/* Recipient */}
              <div>
                <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">Recipient Email</label>
                <input 
                  type="email" 
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  placeholder="Enter email address"
                  className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium text-gray-800"
                />
                {!recipient && (
                  <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> No email found from scraping. Please enter manually.
                  </p>
                )}
              </div>

              {/* Subject */}
              <div>
                <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">Subject Line</label>
                <input 
                  type="text" 
                  value={draft.subject}
                  onChange={(e) => setDraft({...draft, subject: e.target.value})}
                  className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-bold text-gray-900"
                />
              </div>

              {/* Body */}
              <div>
                <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">Email Body (Generated based on {lead.rating}⭐ rating)</label>
                <textarea 
                  value={draft.body}
                  onChange={(e) => setDraft({...draft, body: e.target.value})}
                  rows={10}
                  className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-sm text-gray-700 font-sans leading-relaxed resize-y"
                />
              </div>

              {/* Audit Link Box */}
              <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex items-center justify-between">
                <div className="flex items-center gap-3 text-blue-800">
                  <FileText className="w-5 h-5 text-blue-600" />
                  <div>
                    <strong className="block text-sm">Generated Audit Report Link</strong>
                    <span className="text-xs opacity-80">{draft.audit_link}</span>
                  </div>
                </div>
                <a 
                  href={draft.audit_link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs font-bold text-blue-600 hover:text-blue-800 bg-white px-3 py-1.5 rounded-lg border border-blue-200 shadow-sm flex items-center gap-1"
                >
                  Preview <ExternalLink className="w-3 h-3" />
                </a>
              </div>

            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-gray-100 bg-white flex justify-end gap-3 rounded-b-2xl">
          <button 
            onClick={onClose}
            className="px-5 py-2.5 text-sm font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleSend}
            disabled={loading || sending || !recipient}
            className="px-6 py-2.5 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 rounded-xl shadow-md shadow-blue-600/20 transition-all flex items-center gap-2"
          >
            {sending ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Sending...</>
            ) : (
              <><Send className="w-4 h-4" /> Send Email via Resend</>
            )}
          </button>
        </div>

      </div>
    </div>
  );
}
