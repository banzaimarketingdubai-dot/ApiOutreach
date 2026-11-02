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

    if (res.status === 401) {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth:expired', { detail: errorDetail }));
      }
    }

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

export async function fetchStats(projectId = null, audienceId = null) {
  const params = new URLSearchParams();
  if (projectId) params.append('project_id', projectId);
  if (audienceId) params.append('audience_id', audienceId);
  const qs = params.toString();
  return apiCall(`${API_BASE}/leads/stats${qs ? `?${qs}` : ''}`);
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

export async function startCampaign(id) {
  return apiCall(`${API_BASE}/campaigns/${id}/start`, { method: 'POST' });
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

export async function fetchAnalytics(params = {}) {
  let query = '';
  if (typeof params === 'string') {
    query = params ? `?campaign_id=${encodeURIComponent(params)}` : '';
  } else if (params && typeof params === 'object') {
    const q = new URLSearchParams();
    if (params.project_id) q.set('project_id', params.project_id);
    if (params.campaign_id) q.set('campaign_id', params.campaign_id);
    if (params.product_id) q.set('product_id', params.product_id);
    if (params.audience_id) q.set('audience_id', params.audience_id);
    const qs = q.toString();
    query = qs ? `?${qs}` : '';
  }
  return apiCall(`${API_BASE}/outreach/analytics${query}`);
}

// =============== USERS MANAGEMENT (SUPER_ADMIN) ===============
export async function fetchUsers() {
  return apiCall(`${API_BASE}/users`);
}

export async function updateUserRole(userId, role) {
  return apiCall(`${API_BASE}/users/${userId}/role`, {
    method: 'PATCH',
    body: JSON.stringify({ role })
  });
}

export async function inviteUser(email, role) {
  return apiCall(`${API_BASE}/users/invite`, {
    method: 'POST',
    body: JSON.stringify({ email, role })
  });
}

export async function deleteUser(userId) {
  const res = await fetch(`${API_BASE}/users/${userId}`, {
    method: 'DELETE',
    headers: getHeaders()
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'API request failed');
  }
  return true;
}

// =============== MULTI-PROJECT & AUDIENCES API ===============

// --- Projects ---
export async function fetchProjects() {
  return apiCall(`${API_BASE}/projects`);
}

export async function createProject(projectData) {
  return apiCall(`${API_BASE}/projects`, {
    method: 'POST',
    body: JSON.stringify(projectData)
  });
}

export async function updateProject(projectId, data) {
  return apiCall(`${API_BASE}/projects/${projectId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function deleteProject(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: 'DELETE',
    headers: getHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Не удалось удалить проект');
  }
  return true;
}

// --- Audiences ---
export async function fetchAudiences(projectId) {
  const query = projectId ? `?project_id=${projectId}` : '';
  return apiCall(`${API_BASE}/audiences${query}`);
}

export async function createAudience(audienceData) {
  return apiCall(`${API_BASE}/audiences`, {
    method: 'POST',
    body: JSON.stringify(audienceData)
  });
}

export async function updateAudience(audienceId, data) {
  return apiCall(`${API_BASE}/audiences/${audienceId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function deleteAudience(audienceId) {
  const res = await fetch(`${API_BASE}/audiences/${audienceId}`, {
    method: 'DELETE',
    headers: getHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to delete audience');
  }
  return true;
}

export async function exportAudienceToGoogleSheets(audienceId, spreadsheetId = null, customTemplate = null) {
  return apiCall(`${API_BASE}/audiences/${audienceId}/export-google-sheets`, {
    method: 'POST',
    body: JSON.stringify({
      spreadsheet_id: spreadsheetId,
      custom_template: customTemplate
    })
  });
}

export async function importAudienceRows(audienceId, rows) {
  return apiCall(`${API_BASE}/audiences/${audienceId}/import-rows`, {
    method: 'POST',
    body: JSON.stringify({ rows })
  });
}

export async function importAudienceFile(audienceId, file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const res = await fetch(`${API_ROOT}${API_BASE}/audiences/${audienceId}/import-file`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to import file');
  }
  return res.json();
}

export async function enrichAudience(audienceId, options = {}) {
  return apiCall(`${API_BASE}/audiences/${audienceId}/enrich`, {
    method: 'POST',
    body: JSON.stringify(options)
  });
}

export async function recalculateAudienceStats(audienceId) {
  return apiCall(`${API_BASE}/audiences/${audienceId}/recalculate-stats`, {
    method: 'POST'
  });
}

export async function attachAudienceLeads(audienceId, filters = {}) {
  return apiCall(`${API_BASE}/audiences/${audienceId}/attach-leads`, {
    method: 'POST',
    body: JSON.stringify(filters)
  });
}

// --- Products ---
export async function fetchProducts(projectId) {
  const query = projectId ? `?project_id=${projectId}` : '';
  return apiCall(`${API_BASE}/products${query}`);
}

export async function createProduct(productData) {
  return apiCall(`${API_BASE}/products`, {
    method: 'POST',
    body: JSON.stringify(productData)
  });
}

export async function updateProduct(productId, data) {
  return apiCall(`${API_BASE}/products/${productId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function deleteProduct(productId) {
  const res = await fetch(`${API_ROOT}${API_BASE}/products/${productId}`, {
    method: 'DELETE',
    headers: getHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to delete product');
  }
  return true;
}

// --- Funnel Sequences & AI Studio ---
export async function fetchFunnels(projectId, productId) {
  let query = '';
  const params = [];
  if (projectId) params.push(`project_id=${projectId}`);
  if (productId) params.push(`product_id=${productId}`);
  if (params.length > 0) query = `?${params.join('&')}`;
  return apiCall(`${API_BASE}/funnels${query}`);
}

export async function createFunnel(funnelData) {
  return apiCall(`${API_BASE}/funnels`, {
    method: 'POST',
    body: JSON.stringify(funnelData)
  });
}

export async function updateFunnel(funnelId, data) {
  return apiCall(`${API_BASE}/funnels/${funnelId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function deleteFunnel(funnelId) {
  const res = await fetch(`${API_ROOT}${API_BASE}/funnels/${funnelId}`, {
    method: 'DELETE',
    headers: getHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to delete funnel');
  }
  return true;
}

export async function generateAIFunnel(payload) {
  return apiCall(`${API_BASE}/funnels/ai-generate`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function renderEmailPreview(payload) {
  return apiCall(`${API_BASE}/funnels/render-preview`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

// --- Multi-Campaign Launch, Review Queue & Smart Inbox ---
export async function launchMultiCampaign(campaignData) {
  return apiCall(`${API_BASE}/outreach/launch-multi-campaign`, {
    method: 'POST',
    body: JSON.stringify(campaignData)
  });
}

export async function fetchReviewQueue(params = {}) {
  const cleanParams = Object.fromEntries(Object.entries(params).filter(([_, v]) => v !== '' && v !== null && v !== undefined));
  const query = new URLSearchParams(cleanParams).toString();
  return apiCall(`${API_BASE}/outreach/review-queue?${query}`);
}

export async function approveReviewDrafts(payload) {
  return apiCall(`${API_BASE}/outreach/review-queue/approve`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function rejectReviewDrafts(sequenceIds) {
  return apiCall(`${API_BASE}/outreach/review-queue/reject`, {
    method: 'POST',
    body: JSON.stringify({ sequence_ids: sequenceIds })
  });
}

export async function updateReviewDraft(sequenceId, data) {
  return apiCall(`${API_BASE}/outreach/review-queue/${sequenceId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function fetchInboundReplies(params = {}) {
  const cleanParams = Object.fromEntries(Object.entries(params).filter(([_, v]) => v !== '' && v !== null && v !== undefined));
  const query = new URLSearchParams(cleanParams).toString();
  return apiCall(`${API_BASE}/outreach/inbox?${query}`);
}

export async function simulateInboundReply(payload) {
  return apiCall(`${API_BASE}/outreach/inbox/simulate-reply`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function sendInboxResponse(replyId, payload) {
  return apiCall(`${API_BASE}/outreach/inbox/${replyId}/send-response`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}
