/* ============================================================
   UniMind AI — app.js
   Connects to FastAPI /ask endpoint (no Inngest)
   ============================================================ */

// ── Config ──────────────────────────────────────────────────
const BACKEND_URL = window.location.origin; // Same origin: FastAPI serves both
const TOP_K = 8;

// ── State ────────────────────────────────────────────────────
let isLoading = false;
let hasMessages = false;

// ── DOM ──────────────────────────────────────────────────────
const chatArea  = () => document.getElementById('chat-area');
const msgList   = () => document.getElementById('messages');
const welcome   = () => document.getElementById('welcome');
const inputEl   = () => document.getElementById('chat-input');
const sendBtn   = () => document.getElementById('send-btn');
const toastEl   = () => document.getElementById('toast');
const toastMsg  = () => document.getElementById('toast-msg');

// ── Lightweight Markdown parser ──────────────────────────────
function parseMarkdown(raw) {
  // Escape HTML first, then apply markdown rules
  let s = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Headings
  s = s.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  s = s.replace(/^## (.+)$/gm,  '<h3>$1</h3>');

  // Bold / italic
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Inline code
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Numbered list
  s = s.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
  // Bullet list
  s = s.replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>');
  // Wrap consecutive <li> in <ul>
  s = s.replace(/(<li>[\s\S]*?<\/li>)(\s*<li>[\s\S]*?<\/li>)*/g, m => `<ul>${m}</ul>`);

  // Paragraphs
  s = s.replace(/\n{2,}/g, '</p><p>');
  s = s.replace(/\n/g, '<br>');

  // Wrap any remaining bare text block
  if (!s.startsWith('<')) s = `<p>${s}</p>`;

  // Clean up empty paragraphs
  s = s.replace(/<p>\s*<\/p>/g, '');

  return s;
}

// ── Helpers ──────────────────────────────────────────────────
const sleep = ms => new Promise(r => setTimeout(r, ms));

function showWelcome(show) {
  const w = welcome();
  if (w) w.style.display = show ? 'flex' : 'none';
}

function scrollBottom() {
  const el = chatArea();
  if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
}

function setLoading(val) {
  isLoading = val;
  const btn = sendBtn();
  if (btn) btn.disabled = val;
}

// ── Toast ────────────────────────────────────────────────────
function showToast(msg, duration = 4000) {
  toastMsg().textContent = msg;
  toastEl().classList.add('show');
  setTimeout(() => toastEl().classList.remove('show'), duration);
}

// ── Build AI message bubble ──────────────────────────────────
function buildAiBubble() {
  // Wrapper row
  const row = document.createElement('div');
  row.className = 'max-w-3xl mx-auto flex gap-4 msg-animate';

  // Avatar
  const avatar = document.createElement('div');
  avatar.className = 'w-9 h-9 rounded-xl bg-slate-800 flex-shrink-0 flex items-center justify-center border border-white/5 mt-0.5';
  avatar.innerHTML = '<span class="material-symbols-outlined text-indigo-400 text-[18px]">auto_awesome</span>';

  // Content wrapper
  const content = document.createElement('div');
  content.className = 'flex-1 space-y-3 min-w-0';

  // Bubble
  const bubble = document.createElement('div');
  bubble.className = 'bg-surface-container-high/40 backdrop-blur-sm px-5 py-4 rounded-2xl rounded-tl-none border border-white/5 shadow-xl text-on-surface text-sm md-content';

  content.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(content);
  msgList().appendChild(row);
  scrollBottom();

  return { row, bubble, content };
}

// ── Build User message bubble ────────────────────────────────
function appendUserMessage(text) {
  if (!hasMessages) { showWelcome(false); hasMessages = true; }

  const row = document.createElement('div');
  row.className = 'max-w-3xl mx-auto flex flex-row-reverse gap-4 msg-animate';

  const avatar = document.createElement('div');
  avatar.className = 'w-9 h-9 rounded-xl bg-indigo-500/20 flex-shrink-0 flex items-center justify-center border border-indigo-500/20 mt-0.5';
  avatar.innerHTML = '<span class="material-symbols-outlined text-indigo-300 text-[18px]">person</span>';

  const content = document.createElement('div');
  content.className = 'flex justify-end max-w-[80%]';

  const bubble = document.createElement('div');
  bubble.className = 'bg-gradient-to-br from-primary-container to-secondary-container px-5 py-4 rounded-2xl rounded-tr-none shadow-2xl shadow-indigo-900/30 text-on-primary-container text-sm font-medium leading-relaxed';
  bubble.textContent = text;

  content.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(content);
  msgList().appendChild(row);
  scrollBottom();
}

// ── Typing indicator ─────────────────────────────────────────
function showTyping() {
  if (!hasMessages) { showWelcome(false); hasMessages = true; }

  const row = document.createElement('div');
  row.id = 'typing-indicator';
  row.className = 'max-w-3xl mx-auto flex gap-4 msg-animate';

  const avatar = document.createElement('div');
  avatar.className = 'w-9 h-9 rounded-xl bg-slate-800 flex-shrink-0 flex items-center justify-center border border-white/5';
  avatar.innerHTML = '<span class="material-symbols-outlined text-indigo-400 text-[18px]">auto_awesome</span>';

  const bubble = document.createElement('div');
  bubble.className = 'flex items-center gap-1.5 px-4 py-3 bg-surface-container-high/40 rounded-2xl rounded-tl-none border border-white/5';
  bubble.innerHTML = `
    <span class="typing-dot w-1.5 h-1.5 bg-indigo-400 rounded-full"></span>
    <span class="typing-dot w-1.5 h-1.5 bg-violet-400 rounded-full"></span>
    <span class="typing-dot w-1.5 h-1.5 bg-indigo-300 rounded-full"></span>
  `;

  row.appendChild(avatar);
  row.appendChild(bubble);
  msgList().appendChild(row);
  scrollBottom();
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

// ── Append sources ────────────────────────────────────────────
function appendSources(contentEl, sources) {
  if (!sources || sources.length === 0) return;

  const uniqueSources = [...new Set(sources)];

  const section = document.createElement('div');
  section.className = 'space-y-2 mt-1';

  const label = document.createElement('h4');
  label.className = 'text-[10px] uppercase tracking-widest text-indigo-400 font-bold ml-0.5';
  label.textContent = 'Document Sources';
  section.appendChild(label);

  const grid = document.createElement('div');
  grid.className = 'flex flex-wrap gap-2';

  uniqueSources.forEach(src => {
    const filename = src.split('/').pop().replace(/\.pdf$/i, '').replace(/_/g, ' ');
    const card = document.createElement('div');
    card.className = 'source-card flex items-center gap-2 px-3 py-2 bg-surface-container/60 border border-white/5 rounded-xl cursor-default';
    card.innerHTML = `
      <div class="w-6 h-6 rounded-lg bg-indigo-500/10 flex items-center justify-center shrink-0">
        <span class="material-symbols-outlined text-indigo-400 text-[13px]">description</span>
      </div>
      <div class="min-w-0">
        <p class="text-[11px] font-semibold text-on-surface-variant truncate max-w-[180px]" title="${filename}">${filename}</p>
        <p class="text-[9px] text-slate-600 font-mono">PDF Document</p>
      </div>
    `;
    grid.appendChild(card);
  });

  section.appendChild(grid);
  contentEl.appendChild(section);
}

// ── Stream text into bubble ───────────────────────────────────
async function streamIntoBubble(bubble, text) {
  const CHUNK = 4; // chars per tick
  for (let i = 0; i < text.length; i += CHUNK) {
    const partial = text.slice(0, i + CHUNK);
    bubble.innerHTML = parseMarkdown(partial) + '<span class="cursor text-indigo-400">▌</span>';
    scrollBottom();
    await sleep(10);
  }
  // Final render without cursor
  bubble.innerHTML = parseMarkdown(text);
  scrollBottom();
}

// ── Main send function ────────────────────────────────────────
async function sendMessage() {
  const input = inputEl();
  const text = input.value.trim();
  if (!text || isLoading) return;

  // Reset input
  input.value = '';
  autoGrow(input);
  setLoading(true);

  // Show user message
  appendUserMessage(text);
  showTyping();

  try {
    const res = await fetch(`${BACKEND_URL}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: text, top_k: TOP_K }),
    });

    if (!res.ok) {
      const errText = await res.text().catch(() => `HTTP ${res.status}`);
      throw new Error(`Server returned ${res.status}: ${errText}`);
    }

    const data = await res.json();
    removeTyping();

    const answer  = (data.answer  || '').trim() || 'No answer was returned from the server.';
    const sources = data.sources  || [];

    // Build AI bubble and stream into it
    if (!hasMessages) { showWelcome(false); hasMessages = true; }
    const { bubble, content } = buildAiBubble();
    await streamIntoBubble(bubble, answer);

    // Append sources below bubble
    appendSources(content, sources);
    scrollBottom();

  } catch (err) {
    removeTyping();

    let userMsg = err.message || 'An unexpected error occurred.';
    if (
      userMsg.toLowerCase().includes('failed to fetch') ||
      userMsg.toLowerCase().includes('networkerror') ||
      userMsg.toLowerCase().includes('fetch')
    ) {
      userMsg = '⚠️ Cannot reach the backend. Make sure FastAPI is running.';
    }

    // Show error as an AI message
    if (!hasMessages) { showWelcome(false); hasMessages = true; }
    const { bubble } = buildAiBubble();
    bubble.innerHTML = `<span class="text-red-400 font-medium">${userMsg}</span>`;
    showToast('Connection error — check the FastAPI server');
  }

  setLoading(false);
  inputEl().focus();
}

// ── Quick prompt chips ────────────────────────────────────────
function usePrompt(el) {
  const text = el.textContent.trim();
  const input = inputEl();
  input.value = text;
  autoGrow(input);
  input.focus();
  sendMessage();
}

// ── Clear chat ────────────────────────────────────────────────
function clearChat() {
  msgList().innerHTML = '';
  showWelcome(true);
  hasMessages = false;
  inputEl().focus();
}

// ── Keyboard handler ──────────────────────────────────────────
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ── Auto-grow textarea ────────────────────────────────────────
function autoGrow(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  showWelcome(true);
  inputEl().focus();
});
