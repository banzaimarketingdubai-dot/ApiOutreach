const IS_PROD = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');
const API_ROOT = IS_PROD ? 'https://web-production-c4d98.up.railway.app' : '';
const API_BASE = IS_PROD
  ? 'https://web-production-c4d98.up.railway.app/api/v1'
  : '/api/v1';

function getHeaders(extraHeaders = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extraHeaders
  };
}

export async function apiCall(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_ROOT}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: getHeaders(options.headers)
  });
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errData = await res.json();
      errorDetail = errData.detail || errorDetail;
    } catch (e) {}
    throw new Error(`API call failed: ${errorDetail}`);
  }
  return res.json();
}

// Authentication API
export async function loginWithGoogle(credential, email, name, picture) {
  return apiCall(`${API_BASE}/auth/google`, {
    method: 'POST',
    body: JSON.stringify({ credential, email, name, picture })
  });
}

export async function loginWithPassword(email, password) {
  return apiCall(`${API_BASE}/auth/login`, {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
}

export async function fetchCurrentUser() {
  return apiCall(`${API_BASE}/auth/me`);
}


export async function fetchLeads(params = {}) {
  const cleanParams = Object.fromEntries(Object.entries(params).filter(([_, v]) => v !== '' && v !== null && v !== undefined && v !== 'null'));
  const query = new URLSearchParams(cleanParams).toString();
  return apiCall(`${API_BASE}/leads?${query}`);
}

export async function createLead(leadData) {
  return apiCall(`${API_BASE}/leads`, {
    method: 'POST',
    body: JSON.stringify(leadData)
  });
}

export async function checkMessengers(payload) {
  return apiCall(`${API_BASE}/leads/check_messengers`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function exportLeadRadar(payload) {
  return apiCall(`${API_BASE}/leads/export_lead_radar`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function fetchStats() {
  return apiCall(`${API_BASE}/leads/stats`);
}

export async function generateAIStrategy(user_goal, geo, additional_notes) {
  return apiCall(`${API_BASE}/ai/strategy`, {
    method: 'POST',
    body: JSON.stringify({ user_goal, geo, additional_notes })
  });
}


export async function createCampaign(campaignData) {
  return apiCall(`${API_BASE}/campaigns`, {
    method: 'POST',
    body: JSON.stringify(campaignData)
  });
}

export async function fetchCampaigns() {
  return apiCall(`${API_BASE}/campaigns`);
}

export async function getCampaignStatus(id) {
  return apiCall(`${API_BASE}/campaigns/${id}/status`);
}

export async function updateCampaign(id, data) {
  return apiCall(`${API_BASE}/campaigns/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data)
  });
}

export async function deleteCampaign(id) {
  return apiCall(`${API_BASE}/campaigns/${id}`, { method: 'DELETE' });
}

export async function retryFailed(id) {
  return apiCall(`${API_BASE}/campaigns/${id}/retry-failed`, { method: 'POST' });
}

export async function recalculateScore(id, scoring_rules) {
  return apiCall(`${API_BASE}/campaigns/${id}/recalculate-score`, {
    method: 'POST',
    body: JSON.stringify({ scoring_rules })
  });
}

export async function getSuspectedDuplicates(campaign_id = '') {
  const query = campaign_id ? `?campaign_id=${campaign_id}` : '';
  return apiCall(`${API_BASE}/leads/tools/duplicates${query}`);
}

export async function mergeLeads(sourceId, targetId) {
  return apiCall(`${API_BASE}/leads/${sourceId}/merge`, {
    method: 'POST',
    body: JSON.stringify({ target_lead_id: targetId })
  });
}

export async function dryRunAI(prompt_template, lead_ids) {
  return apiCall(`${API_BASE}/ai/dry-run`, {
    method: 'POST',
    body: JSON.stringify({ prompt_template, lead_ids })
  });
}

export async function resetEnrichment(lead_ids) {
  return apiCall(`${API_BASE}/leads/tools/reset_enrichment`, {
    method: 'POST',
    body: JSON.stringify({ lead_ids })
  });
}

export async function pauseCampaign(id) {
  return apiCall(`${API_BASE}/campaigns/${id}/suspend`, { method: 'POST' });
}

export async function resumeCampaign(id) {
  return apiCall(`${API_BASE}/campaigns/${id}/resume`, { method: 'POST' });
}

export async function stopCampaign(id) {
  return apiCall(`${API_BASE}/campaigns/${id}/halt`, { method: 'POST' });
}

export async function fetchApifyBalance() {
  return apiCall(`${API_BASE}/apify/balance`);
}


export function getExportCsvUrl(filters = {}) {
  const cleanFilters = Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== '' && v !== null && v !== undefined && v !== 'null'));
  const query = new URLSearchParams(cleanFilters).toString();
  return `${API_BASE}/export/csv?${query}`;
}

// Vault / Settings
export async function getVaultStatus() {
  const res = await fetch(`${API_BASE}/settings/vault`);
  if (!res.ok) throw new Error('Failed to fetch vault');
  return res.json();
}

export async function setVaultKey(provider, api_key) {
  const res = await fetch(`${API_BASE}/settings/vault`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key })
  });
  if (!res.ok) throw new Error('Failed to set key');
  return res.json();
}

// Templates
export async function getTemplates() {
  const res = await fetch(`${API_BASE}/templates`);
  if (!res.ok) throw new Error('Failed to fetch templates');
  return res.json();
}

export async function createTemplate(data) {
  const res = await fetch(`${API_BASE}/templates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to create template');
  return res.json();
}

export async function deleteTemplate(id) {
  const res = await fetch(`${API_BASE}/templates/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete template');
  return res.json();
}

// Funnel Management
export async function startFunnel(lead_ids, funnel_type) {
  return apiCall(`${API_BASE}/outreach/funnels/start`, {
    method: 'POST',
    body: JSON.stringify({ lead_ids, funnel_type })
  });
}

export async function pauseFunnel(lead_ids) {
  return apiCall(`${API_BASE}/outreach/funnels/pause`, {
    method: 'POST',
    body: JSON.stringify({ lead_ids })
  });
}

export async function resumeFunnel(lead_ids) {
  return apiCall(`${API_BASE}/outreach/funnels/resume`, {
    method: 'POST',
    body: JSON.stringify({ lead_ids })
  });
}

export async function overrideFunnel(lead_id, email_subject, email_content) {
  return apiCall(`${API_BASE}/outreach/funnels/override`, {
    method: 'POST',
    body: JSON.stringify({ lead_id, email_subject, email_content })
  });
}

export async function generateSandboxFunnel(lead_id, funnel_type) {
  return apiCall(`${API_BASE}/outreach/sandbox/generate`, {
    method: 'POST',
    body: JSON.stringify({ lead_id, funnel_type })
  });
}

export async function fetchAnalytics(campaignId) {
  const query = campaignId ? `?campaign_id=${campaignId}` : '';
  return apiCall(`${API_BASE}/outreach/analytics${query}`);
}
