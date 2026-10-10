import React, { useState } from 'react';
import { UserPlus, Loader2, Save } from 'lucide-react';
import { createLead } from '../services/api';

export default function CreateLeadModal({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    company_name: '',
    business_type: '',
    city: '',
    rating: 4.5,
    reviews_count: 10,
    email: ''
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      const payload = {
        company_name: formData.company_name,
        business_type: formData.business_type,
        city: formData.city,
        rating: parseFloat(formData.rating),
        reviews_count: parseInt(formData.reviews_count, 10),
        revo_score: 80, // Default mock
        contacts: []
      };
      
      if (formData.email) {
        payload.contacts.push({
          contact_type: 'email',
          contact_value: formData.email
        });
      }

      await createLead(payload);
      onSuccess();
    } catch (err) {
      setError(err.message || 'Failed to create lead');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="bg-slate-900 border border-slate-700/50 rounded-2xl w-full max-w-md shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <UserPlus className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Create Test Lead</h2>
              <p className="text-xs text-slate-400">Instantly add a lead to test funnels</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Company Name</label>
            <input 
              required
              type="text"
              value={formData.company_name}
              onChange={(e) => setFormData({...formData, company_name: e.target.value})}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors"
              placeholder="e.g. Acme Corp"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Niche</label>
              <input 
                type="text"
                value={formData.business_type}
                onChange={(e) => setFormData({...formData, business_type: e.target.value})}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500/50"
                placeholder="e.g. Plumber"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">City</label>
              <input 
                type="text"
                value={formData.city}
                onChange={(e) => setFormData({...formData, city: e.target.value})}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500/50"
                placeholder="e.g. Dubai"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Rating</label>
              <input 
                type="number"
                step="0.1"
                min="1"
                max="5"
                value={formData.rating}
                onChange={(e) => setFormData({...formData, rating: e.target.value})}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Reviews</label>
              <input 
                type="number"
                value={formData.reviews_count}
                onChange={(e) => setFormData({...formData, reviews_count: e.target.value})}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500/50"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Test Email</label>
            <input 
              required
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500/50"
              placeholder="you@example.com"
            />
          </div>

          <div className="pt-4 flex justify-end space-x-3">
            <button 
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button 
              type="submit"
              disabled={isSaving}
              className="flex items-center space-x-2 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium transition-all"
            >
              {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              <span>Create Lead</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
