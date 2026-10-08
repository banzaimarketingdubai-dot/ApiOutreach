const API_BASE = '/api/v1';

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
  if (!res.ok) throw new Error('AI Strategy generation failed');
  return res.json();
}

export async function createCampaign(campaignData) {
  const res = await fetch(`${API_BASE}/campaigns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(campaignData)
  });
  if (!res.ok) throw new Error('Failed to launch campaign');
  return res.json();
}

export async function fetchCampaigns() {
  const res = await fetch(`${API_BASE}/campaigns`);
  if (!res.ok) throw new Error('Failed to fetch campaigns');
  return res.json();
}

export function getExportCsvUrl(filters = {}) {
  const query = new URLSearchParams(filters).toString();
  return `${API_BASE}/export/csv?${query}`;
}
