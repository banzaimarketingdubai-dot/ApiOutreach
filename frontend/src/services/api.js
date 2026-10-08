const IS_PROD = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');
const API_BASE = IS_PROD
  ? 'https://web-production-c4d98.up.railway.app/api/v1'
  : '/api/v1';

export async function fetchLeads(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/leads?${query}`);
  if (!res.ok) throw new Error('Failed to fetch leads');
  return res.json();
}

export async function generateAIStrategy(user_goal, geo, additional_notes) {
  const res = await fetch(`${API_BASE}/ai/strategy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_goal, geo, additional_notes })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'AI Strategy generation failed');
  }
  return res.json();
}

export async function createCampaign(campaignData) {
  const res = await fetch(`${API_BASE}/campaigns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(campaignData)
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to launch campaign');
  }
  return res.json();
}

export async function fetchCampaigns() {
  const res = await fetch(`${API_BASE}/campaigns`);
  if (!res.ok) throw new Error('Failed to fetch campaigns');
  return res.json();
}

export async function getCampaignStatus(id) {
  const res = await fetch(`${API_BASE}/campaigns/${id}/status`);
  if (!res.ok) throw new Error('Failed to fetch campaign status');
  return res.json();
}

export async function updateCampaign(id, data) {
  const res = await fetch(`${API_BASE}/campaigns/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to update campaign');
  return res.json();
}

export async function deleteCampaign(id) {
  const res = await fetch(`${API_BASE}/campaigns/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete campaign');
  return res.json();
}

export async function retryFailed(id) {
  const res = await fetch(`${API_BASE}/campaigns/${id}/retry-failed`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to retry');
  return res.json();
}

export async function recalculateScore(id, scoring_rules) {
  const res = await fetch(`${API_BASE}/campaigns/${id}/recalculate-score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scoring_rules })
  });
  if (!res.ok) throw new Error('Failed to recalculate score');
  return res.json();
}

export async function getSuspectedDuplicates() {
  const res = await fetch(`${API_BASE}/leads/tools/duplicates`);
  if (!res.ok) throw new Error('Failed to fetch duplicates');
  return res.json();
}

export async function mergeLeads(sourceId, targetId) {
  const res = await fetch(`${API_BASE}/leads/${sourceId}/merge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_lead_id: targetId })
  });
  if (!res.ok) throw new Error('Failed to merge leads');
  return res.json();
}

export async function dryRunAI(prompt_template, lead_ids) {
  const res = await fetch(`${API_BASE}/ai/dry-run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt_template, lead_ids })
  });
  if (!res.ok) throw new Error('Failed to run AI dry run');
  return res.json();
}

export async function pauseCampaign(id) {
  const res = await fetch(`${API_BASE}/campaigns/${id}/pause`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to pause campaign');
  return res.json();
}

export async function resumeCampaign(id) {
  const res = await fetch(`${API_BASE}/campaigns/${id}/resume`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to resume campaign');
  return res.json();
}

export async function stopCampaign(id) {
  const res = await fetch(`${API_BASE}/campaigns/${id}/stop`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to stop campaign');
  return res.json();
}

export async function fetchApifyBalance() {
  const res = await fetch(`${API_BASE}/apify/balance`);
  if (!res.ok) throw new Error('Failed to fetch Apify balance');
  return res.json();
}

export function getExportCsvUrl(filters = {}) {
  const query = new URLSearchParams(filters).toString();
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
