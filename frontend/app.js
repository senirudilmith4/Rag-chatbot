  const BACKEND_URL = 'http://127.0.0.1:8000';
  const TOP_K = 8;

  // ── State ───────────────────────────────────────────
  let isLoading = false;
  let hasMessages = false;

  // ── DOM refs ─────────────────────────────────────────
  const chatArea   = document.getElementById('chat-area');
  const messages   = document.getElementById('messages');
  const welcome    = document.getElementById('welcome');
  const inputEl    = document.getElementById('user-input');
  const sendBtn    = document.getElementById('send-btn');
  const toast      = document.getElementById('toast');
  const charCount  = document.getElementById('char-count');

  // ── Markdown parser (lightweight) ───────────────────
  function parseMarkdown(md) {
    return md
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/### (.+)/g, '<h3>$1</h3>')
      .replace(/## (.+)/g, '<h3>$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^\d+\. (.+)/gm, '<li>$1</li>')
      .replace(/^[-*] (.+)/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\n?)+/g, s => `<ul>${s}</ul>`)
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^(?!<)(.+)$/gm, '<p>$1</p>')
      .replace(/<p><\/p>/g, '');
  }

  // ── Show/hide welcome ────────────────────────────────
  function showMessages() {
    if (!hasMessages) {
      welcome.style.display = 'none';
      hasMessages = true;
    }
  }

  // ── Append a message bubble ──────────────────────────
  function appendMessage(role, content, sources) {
    showMessages();
    const msgEl = document.createElement('div');
    msgEl.className = `msg ${role}`;

    const avatar = document.createElement('div');
    avatar.className = `avatar ${role === 'assistant' ? 'ai' : 'user-av'}`;
    avatar.textContent = role === 'assistant' ? '✦' : '👤';

    const bubble = document.createElement('div');
    bubble.className = `bubble ${role === 'assistant' ? 'ai' : 'user'}`;

    if (role === 'assistant') {
      bubble.innerHTML = parseMarkdown(content);
      // Attach sources
      if (sources && sources.length > 0) {
        const strip = document.createElement('div');
        strip.className = 'sources-strip';
        const unique = [...new Set(sources.map(s => s.split('/').pop().replace(/\.pdf$/i, '')))];
        unique.forEach(src => {
          const pill = document.createElement('div');
          pill.className = 'source-pill';
          pill.innerHTML = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> ${src}`;
          strip.appendChild(pill);
        });
        bubble.appendChild(strip);
      }
    } else {
      bubble.textContent = content;
    }

    msgEl.appendChild(avatar);
    msgEl.appendChild(bubble);
    messages.appendChild(msgEl);
    scrollToBottom();
    return bubble;
  }

  // ── Typing indicator ─────────────────────────────────
  function showTyping() {
    showMessages();
    const msgEl = document.createElement('div');
    msgEl.className = 'msg assistant';
    msgEl.id = 'typing-msg';

    const avatar = document.createElement('div');
    avatar.className = 'avatar ai';
    avatar.textContent = '✦';

    const bubble = document.createElement('div');
    bubble.className = 'bubble ai typing-indicator';
    bubble.innerHTML = `
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>`;

    msgEl.appendChild(avatar);
    msgEl.appendChild(bubble);
    messages.appendChild(msgEl);
    scrollToBottom();
  }

  function removeTyping() {
    const el = document.getElementById('typing-msg');
    if (el) el.remove();
  }

  // ── Scroll helper ────────────────────────────────────
  function scrollToBottom() {
    chatArea.scrollTo({ top: chatArea.scrollHeight, behavior: 'smooth' });
  }

  // ── Toast ────────────────────────────────────────────
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3500);
  }

  // ── Send message ─────────────────────────────────────
  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isLoading) return;

    isLoading = true;
    sendBtn.disabled = true;
    inputEl.value = '';
    autoResize(inputEl);
    charCount.textContent = '';

    appendMessage('user', text, null);
    showTyping();

    try {
      const res = await fetch(`${BACKEND_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, top_k: TOP_K }),
      });

      if (!res.ok) {
        const err = await res.text();
        throw new Error(`Server error ${res.status}: ${err}`);
      }

      const data = await res.json();
      removeTyping();

      const answer = data.answer || 'No answer returned from the backend.';
      const sources = data.sources || [];

      // Stream the text character by character for effect
      await streamBubble(answer, sources);

    } catch (err) {
      removeTyping();
      let msg = err.message || 'Unknown error';
      if (msg.includes('fetch') || msg.includes('NetworkError') || msg.includes('Failed to fetch')) {
        msg = '⚠️ Cannot reach the backend. Make sure your FastAPI server is running on port 8000.';
      }
      appendMessage('assistant', msg, null);
      showToast('Connection error — check backend');
    }

    isLoading = false;
    sendBtn.disabled = false;
    inputEl.focus();
  }

  // ── Streaming effect ─────────────────────────────────
  async function streamBubble(text, sources) {
    showMessages();
    const msgEl = document.createElement('div');
    msgEl.className = 'msg assistant';

    const avatar = document.createElement('div');
    avatar.className = 'avatar ai';
    avatar.textContent = '✦';

    const bubble = document.createElement('div');
    bubble.className = 'bubble ai';

    msgEl.appendChild(avatar);
    msgEl.appendChild(bubble);
    messages.appendChild(msgEl);

    // Stream char by char
    const CHUNK = 3; // chars per tick for speed
    for (let i = 0; i < text.length; i += CHUNK) {
      bubble.innerHTML = parseMarkdown(text.slice(0, i + CHUNK)) + '<span style="opacity:0.5">▌</span>';
      scrollToBottom();
      await sleep(12);
    }

    // Final render without cursor
    bubble.innerHTML = parseMarkdown(text);

    // Sources
    if (sources && sources.length > 0) {
      const strip = document.createElement('div');
      strip.className = 'sources-strip';
      const unique = [...new Set(sources.map(s => s.split('/').pop().replace(/\.pdf$/i, '')))];
      unique.forEach(src => {
        const pill = document.createElement('div');
        pill.className = 'source-pill';
        pill.innerHTML = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> ${src}`;
        strip.appendChild(pill);
      });
      bubble.appendChild(strip);
    }

    scrollToBottom();
  }

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  // ── Quick prompts ────────────────────────────────────
  function usePrompt(btn) {
    const text = btn.textContent.trim();
    inputEl.value = text;
    autoResize(inputEl);
    inputEl.focus();
    sendMessage();
  }

  // ── Clear chat ───────────────────────────────────────
  function clearChat() {
    messages.innerHTML = '';
    welcome.style.display = 'block';
    hasMessages = false;
    inputEl.focus();
  }

  // ── Keyboard handler ─────────────────────────────────
  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  // ── Auto resize textarea ─────────────────────────────
  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 140) + 'px';
    const len = el.value.length;
    charCount.textContent = len > 0 ? `${len} chars` : '';
  }

  // ── Init ─────────────────────────────────────────────
  inputEl.focus();