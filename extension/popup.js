// PhishNet X — Popup Script with Dark/Light Mode

const $ = id => document.getElementById(id);
let isDark = true;

// ── Theme toggle ───────────────────────────────
function applyTheme(dark) {
  document.body.classList.toggle('dark', dark);
  document.body.classList.toggle('light', !dark);
  $('theme-btn').textContent = dark ? '🌙' : '☀️';
  $('theme-label').textContent = dark ? 'Dark Mode' : 'Light Mode';
}

$('theme-btn').addEventListener('click', () => {
  isDark = !isDark;
  applyTheme(isDark);
  chrome.storage.local.set({ theme: isDark ? 'dark' : 'light' });
});

// Load saved theme
chrome.storage.local.get(['theme'], result => {
  isDark = result.theme !== 'light';
  applyTheme(isDark);
});

// ── Tab navigation ─────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    $(`view-${tab}`).classList.add('active');
  });
});

// ── State ──────────────────────────────────────
let currentResult = null;
let currentUrl = null;
let currentTabId = null;

function showState(name) {
  ['state-scanning','state-unknown','state-empty','result-card'].forEach(id => {
    const el = $(id); if (el) el.style.display = 'none';
  });
  const t = $(name); if (t) t.style.display = '';
}

function renderGauge(score) {
  const fill = $('gauge-fill'); const scoreEl = $('gauge-score');
  if (!fill || !scoreEl) return;
  const offset = 201 - (score / 100) * 201;
  fill.style.strokeDashoffset = offset;
  const color = score >= 70 ? '#ef4444' : score >= 40 ? '#f59e0b' : '#22c55e';
  fill.style.stroke = color;
  scoreEl.textContent = score;
  scoreEl.style.color = color;
}

function renderResult(result) {
  if (!result) { showState('state-empty'); return; }
  const { status, risk_score, reasons, url } = result;
  if (status === 'scanning') { showState('state-scanning'); if ($('scanning-url')) $('scanning-url').textContent = url || ''; return; }
  if (status === 'unknown')  { showState('state-unknown'); return; }
  showState('result-card');
  const badge = $('status-badge'); const icon = $('status-icon'); const text = $('status-text');
  badge.className = `status-badge ${status}`;
  const labels = { safe:{icon:'✅',text:'Safe'}, suspicious:{icon:'⚠️',text:'Suspicious'}, phishing:{icon:'🚨',text:'Phishing!'} };
  const lbl = labels[status] || { icon:'❓', text:'Unknown' };
  icon.textContent = lbl.icon; text.textContent = lbl.text;
  renderGauge(risk_score || 0);
  const urlEl = $('url-display');
  if (urlEl) {
    try { const p = new URL(url); urlEl.textContent = p.hostname + p.pathname.slice(0,40); } catch { urlEl.textContent = (url||'').slice(0,60); }
    urlEl.title = url;
  }
  const list = $('reasons-list');
  if (list && reasons) {
    const color = status==='phishing'?'#ef4444':status==='suspicious'?'#f59e0b':'#22c55e';
    list.innerHTML = reasons.map(r => `<li><span class="reason-dot" style="background:${color}"></span><span>${r}</span></li>`).join('');
  }
  const rec = $('recommendation');
  if (rec) {
    if (status === 'phishing')   { rec.style.display=''; rec.className='recommendation phishing'; rec.textContent='⛔ Do NOT enter passwords, credit cards, or any personal data on this site.'; }
    else if (status==='suspicious'){ rec.style.display=''; rec.className='recommendation suspicious'; rec.textContent='⚠️ Proceed with caution. Avoid entering sensitive information.'; }
    else { rec.style.display='none'; }
  }
  const footer = $('footer-status');
  if (footer) { const t = new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}); footer.textContent = `Scanned ${t}`; }
}

// ── Init ───────────────────────────────────────
async function init() {
  try {
    const [tab] = await chrome.tabs.query({ active:true, currentWindow:true });
    if (!tab) { showState('state-empty'); return; }
    currentTabId = tab.id; currentUrl = tab.url;
    if (!currentUrl || currentUrl.startsWith('chrome://') || currentUrl.startsWith('about:')) { showState('state-empty'); return; }
    chrome.runtime.sendMessage({ type:'GET_RESULT', tabId:currentTabId }, response => {
      if (chrome.runtime.lastError) { showState('state-empty'); return; }
      if (response?.result) { currentResult = response.result; renderResult(response.result); }
      else {
        showState('state-scanning');
        if ($('scanning-url')) $('scanning-url').textContent = currentUrl;
        chrome.runtime.sendMessage({ type:'SCAN_URL', url:currentUrl, tabId:currentTabId }, res => {
          if (res?.result) { currentResult = res.result; renderResult(res.result); }
          else showState('state-unknown');
        });
      }
    });
  } catch(err) { showState('state-empty'); }
}

$('refresh-btn')?.addEventListener('click', () => {
  if (!currentUrl || !currentTabId) return;
  showState('state-scanning');
  if ($('scanning-url')) $('scanning-url').textContent = currentUrl;
  chrome.runtime.sendMessage({ type:'SCAN_URL', url:currentUrl, tabId:currentTabId }, res => {
    if (res?.result) { currentResult = res.result; renderResult(res.result); }
    else showState('state-unknown');
  });
});

$('retry-btn')?.addEventListener('click', () => $('refresh-btn')?.click());

// ── Chat ───────────────────────────────────────
const chatMessages = $('chat-messages'); const chatInput = $('chat-input'); const sendBtn = $('send-btn');

function appendMessage(content, role) {
  const div = document.createElement('div'); div.className = `chat-msg ${role}`;
  div.innerHTML = `<div class="msg-bubble">${escapeHtml(content)}</div>`;
  chatMessages.appendChild(div); chatMessages.scrollTop = chatMessages.scrollHeight;
}
function showTyping() {
  const div = document.createElement('div'); div.className='chat-msg assistant typing-indicator'; div.id='typing-indicator';
  div.innerHTML=`<div class="msg-bubble"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>`;
  chatMessages.appendChild(div); chatMessages.scrollTop=chatMessages.scrollHeight;
}
function hideTyping() { $('typing-indicator')?.remove(); }
function escapeHtml(str) {
  return (str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>').replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>');
}
async function sendChat() {
  const msg = chatInput.value.trim(); if (!msg) return;
  chatInput.value = ''; sendBtn.disabled = true;
  appendMessage(msg, 'user'); showTyping();
  const context = currentResult ? { url:currentResult.url, risk_score:currentResult.risk_score, status:currentResult.status, reasons:currentResult.reasons } : null;
  chrome.runtime.sendMessage({ type:'CHAT', userMessage:msg, context }, response => {
    hideTyping(); sendBtn.disabled = false;
    appendMessage(response?.reply || 'Sorry, no response.', 'assistant');
  });
}
sendBtn?.addEventListener('click', sendChat);
chatInput?.addEventListener('keydown', e => { if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } });

init();
