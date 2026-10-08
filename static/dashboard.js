// BanzAI Revo Web Admin Dashboard Logic

let currentLeads = [];
let searchDebounceTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  refreshAllData();

  // Авто-обновление логов каждые 4 секунды
  setInterval(fetchLogs, 4000);
  setInterval(fetchStats, 6000);
  setInterval(updateServerClock, 1000);
});

// Навигация по вкладкам
function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const tabs = document.querySelectorAll('.tab-content');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const tabName = item.getAttribute('data-tab');

      navItems.forEach(n => n.classList.remove('active'));
      tabs.forEach(t => t.classList.remove('active'));

      item.classList.add('active');
      const targetTab = document.getElementById(`tab-${tabName}`);
      if (targetTab) targetTab.classList.add('active');

      const titleMap = {
        'dashboard': 'Аналитика и Мониторинг',
        'crm': 'База Лидов и CRM Управление',
        'console': 'Консоль Процессов (Live Log)',
        'queue': 'Очередь Защиты от Спама (24h)'
      };
      document.getElementById('page-title').innerText = titleMap[tabName] || 'BanzAI Revo Portal';
    });
  });
}

function updateServerClock() {
  const now = new Date();
  document.getElementById('server-clock').innerText = now.toLocaleTimeString();
}

// Загрузка статистики
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();

    document.getElementById('stat-total-leads').innerText = data.total_leads || 0;
    document.getElementById('stat-email-pct').innerText = `${data.email_coverage_pct || 0}%`;
    document.getElementById('stat-email-count').innerText = `${data.with_email || 0} имейлов найдено`;

    document.getElementById('stat-messenger-pct').innerText = `${data.messenger_coverage_pct || 0}%`;
    document.getElementById('stat-messenger-count').innerText = `${data.mobile_messengers_count || 0} мобильных номеров`;

    document.getElementById('stat-queue-count').innerText = data.queue_count || 0;
  } catch (err) {
    console.error('Ошибка загрузки статистики:', err);
  }
}

// Загрузка таблицы CRM
async function fetchLeads(query = '') {
  try {
    const res = await fetch(`/api/leads?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    currentLeads = data.leads || [];

    document.getElementById('crm-count').innerText = data.total || 0;
    renderLeadsTable(currentLeads);
  } catch (err) {
    console.error('Ошибка загрузки лидов:', err);
  }
}

function renderLeadsTable(leads) {
  const tbody = document.getElementById('crm-table-body');
  if (!leads || leads.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Лиды не найдены</td></tr>`;
    return;
  }

  const rows = leads.map((lead, idx) => {
    const phone = lead.phone ? lead.phone.replace(/^'/, '') : '';
    const cleanPhone = phone.replace(/[^\d]/g, '');
    const score = lead.revo_score || 50;
    const scoreClass = score >= 60 ? 'high' : 'mid';

    const waBtn = cleanPhone ? `<a href="https://wa.me/${cleanPhone}" target="_blank" class="btn-msg btn-wa">WhatsApp</a>` : '';
    const viberBtn = cleanPhone ? `<a href="viber://chat?number=%2B${cleanPhone}" class="btn-msg btn-viber">Viber</a>` : '';
    const tgBtn = cleanPhone ? `<a href="https://t.me/+${cleanPhone}" target="_blank" class="btn-msg btn-tg">Telegram</a>` : '';

    return `
      <tr>
        <td>${idx + 1}</td>
        <td><span class="badge-score mid">${lead.business_type || 'Категория'}</span></td>
        <td><strong>${lead.company_name || 'Без названия'}</strong><br><small class="text-muted">${lead.address || ''}</small></td>
        <td>
          ${phone ? `📞 ${phone}<br>` : ''}
          ${lead.email ? `📧 ${lead.email}` : '<small class="text-muted">No Email</small>'}
        </td>
        <td>
          <div class="messenger-btns">
            ${waBtn} ${viberBtn} ${tgBtn}
          </div>
        </td>
        <td><span class="badge-score ${scoreClass}">${score}%</span></td>
        <td><small class="text-muted">${lead.status || 'Готов к рассылке'}</small></td>
      </tr>
    `;
  }).join('');

  tbody.innerHTML = rows;
}

function debounceSearch() {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    const q = document.getElementById('crm-search').value;
    fetchLeads(q);
  }, 300);
}

// Загрузка логов
async function fetchLogs() {
  try {
    const res = await fetch('/api/logs');
    const data = await res.json();
    const logs = data.logs || [];

    const logHtml = logs.map(line => `<div class="log-line">${line}</div>`).join('');
    
    const miniTerm = document.getElementById('mini-terminal');
    const fullTerm = document.getElementById('full-terminal');

    if (miniTerm) {
      miniTerm.innerHTML = logHtml || '<div class="log-line text-muted">Нет новых логов</div>';
      miniTerm.scrollTop = miniTerm.scrollHeight;
    }
    if (fullTerm) {
      fullTerm.innerHTML = logHtml || '<div class="log-line text-muted">Нет новых логов</div>';
      fullTerm.scrollTop = fullTerm.scrollHeight;
    }
  } catch (err) {
    console.error('Ошибка загрузки логов:', err);
  }
}

// Загрузка очереди
async function fetchQueue() {
  try {
    const res = await fetch('/api/queue');
    const data = await res.json();
    const queue = data.queue || [];
    const container = document.getElementById('queue-container');

    if (queue.length === 0) {
      container.innerHTML = `<div class="text-muted py-3">Очередь отложенных имейлов пуста (все 24ч лимиты соблюдены).</div>`;
      return;
    }

    container.innerHTML = queue.map(item => `
      <div class="kpi-card glass" style="margin-bottom:12px;">
        <div class="kpi-icon purple">⏳</div>
        <div class="kpi-data">
          <strong>${item.company_name}</strong> (${item.email})
          <div class="kpi-sub">Запланированная отправка: <strong>${item.scheduled_formatted}</strong></div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Ошибка загрузки очереди:', err);
  }
}

// Триггер 1-click действий
async function triggerAction(actionName) {
  showToast('🚀 Процесс запускается...');
  try {
    const res = await fetch(`/api/action/${actionName}`, { method: 'POST' });
    const data = await res.json();
    showToast(`✅ ${data.message || 'Действие успешно запущен!'}`);
    setTimeout(refreshAllData, 1500);
  } catch (err) {
    showToast(`❌ Ошибка запуска: ${err}`);
  }
}

function refreshAllData() {
  fetchStats();
  fetchLeads();
  fetchLogs();
  fetchQueue();
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.innerText = msg;
  toast.style.display = 'block';
  setTimeout(() => { toast.style.display = 'none'; }, 3500);
}
