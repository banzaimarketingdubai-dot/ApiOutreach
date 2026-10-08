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

export async function fetchApifyBalance() {
  const res = await fetch(`${API_BASE}/apify/balance`);
  if (!res.ok) throw new Error('Failed to fetch Apify balance');
  return res.json();
}

export function getExportCsvUrl(filters = {}) {
  const query = new URLSearchParams(filters).toString();
  return `${API_BASE}/export/csv?${query}`;
}
