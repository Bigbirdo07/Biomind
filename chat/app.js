/**
 * BioReason Chat — Core Application Logic
 * Modern, low-friction, privacy-preserving conversational UI
 */

const STORAGE_KEYS = {
  CHATS: 'bioreason_chats_v02',
  ACTIVE_CHAT: 'bioreason_active_chat_id',
  THEME: 'bioreason_theme_pref',
  DEV_MODE: 'bioreason_dev_mode_enabled',
  RESPONSE_MODE: 'bioreason_response_mode'
};

// App State
let appState = {
  chats: [],
  activeChatId: null,
  isGenerating: false,
  attachedFile: null,
  devMode: false,
  responseMode: 'conversational'
};

// DOM Elements
const elements = {
  sidebar: document.getElementById('sidebar'),
  btnCollapseSidebar: document.getElementById('btn-collapse-sidebar'),
  btnExpandSidebar: document.getElementById('btn-expand-sidebar'),
  btnNewChatSidebar: document.getElementById('btn-new-chat-sidebar'),
  btnTopNewChat: document.getElementById('btn-top-new-chat'),
  historyContainer: document.getElementById('history-items-container'),
  emptyState: document.getElementById('empty-state'),
  messagesContainer: document.getElementById('messages-container'),
  chatScrollArea: document.getElementById('chat-scroll-area'),
  chatInput: document.getElementById('chat-input'),
  btnSend: document.getElementById('btn-send'),
  btnStop: document.getElementById('btn-stop'),
  btnAttach: document.getElementById('btn-attach'),
  fileInput: document.getElementById('file-input'),
  attachmentPreview: document.getElementById('attachment-preview'),
  settingsModal: document.getElementById('settings-modal'),
  btnOpenSettingsSidebar: document.getElementById('btn-open-settings-sidebar'),
  btnOpenSettingsTop: document.getElementById('btn-open-settings-top'),
  btnCloseSettings: document.getElementById('btn-close-settings'),
  settingTheme: document.getElementById('setting-theme'),
  settingResponseMode: document.getElementById('setting-response-mode'),
  settingDevMode: document.getElementById('setting-dev-mode'),
  btnClearChats: document.getElementById('btn-clear-chats'),
  devDrawer: document.getElementById('dev-drawer'),
  btnToggleDev: document.getElementById('btn-toggle-dev'),
  btnCloseDev: document.getElementById('btn-close-dev'),
  devLatency: document.getElementById('dev-latency'),
  devTokens: document.getElementById('dev-tokens'),
  devJsonDisplay: document.getElementById('dev-json-display')
};

// Markdown Parser Helper
function formatMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks with syntax highlighting wrapper
  html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<div class="code-block-wrapper">
      <button class="btn-copy-code" onclick="copyCode(this)">Copy code</button>
      <pre><code class="language-${lang || 'plaintext'}">${code.trim()}</code></pre>
    </div>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');

  // Bold and Italics
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // LaTeX inline math formatting ($...$)
  html = html.replace(/\$([^$]+)\$/g, '<span style="font-family: serif; font-style: italic;">$1</span>');

  // Lists
  html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
  html = html.replace(/^\s*\d+\.\s+(.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');

  // Paragraphs
  html = html.split('\n\n').map(p => {
    if (p.startsWith('<h') || p.startsWith('<div') || p.startsWith('<ul>') || p.startsWith('<pre')) return p;
    return `<p>${p.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  return html;
}

// Global copy helper
window.copyCode = function(button) {
  const code = button.parentElement.querySelector('code').textContent;
  navigator.clipboard.writeText(code).then(() => {
    button.textContent = 'Copied!';
    setTimeout(() => { button.textContent = 'Copy code'; }, 2000);
  });
};

window.copyMessageText = function(btn) {
  const row = btn.closest('.message-row');
  const text = row.querySelector('.assistant-body').textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>`;
    setTimeout(() => {
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
    }, 2000);
  });
};

window.toggleAudit = function(btn) {
  btn.classList.toggle('active');
  const card = btn.nextElementSibling;
  card.classList.toggle('open');
};

// Storage Operations
function loadState() {
  const savedChats = localStorage.getItem(STORAGE_KEYS.CHATS);
  appState.chats = savedChats ? JSON.parse(savedChats) : [];
  appState.activeChatId = localStorage.getItem(STORAGE_KEYS.ACTIVE_CHAT);
  
  const theme = localStorage.getItem(STORAGE_KEYS.THEME) || 'dark';
  applyTheme(theme);
  elements.settingTheme.value = theme;

  const devMode = localStorage.getItem(STORAGE_KEYS.DEV_MODE) === 'true';
  appState.devMode = devMode;
  elements.settingDevMode.checked = devMode;
  elements.btnToggleDev.style.display = devMode ? 'flex' : 'none';

  const respMode = localStorage.getItem(STORAGE_KEYS.RESPONSE_MODE) || 'conversational';
  appState.responseMode = respMode;
  elements.settingResponseMode.value = respMode;

  if (appState.chats.length === 0) {
    createNewChat();
  } else if (!appState.activeChatId || !appState.chats.find(c => c.id === appState.activeChatId)) {
    appState.activeChatId = appState.chats[0].id;
  }

  renderSidebarHistory();
  renderActiveChat();
}

function saveChats() {
  localStorage.setItem(STORAGE_KEYS.CHATS, JSON.stringify(appState.chats));
  localStorage.setItem(STORAGE_KEYS.ACTIVE_CHAT, appState.activeChatId);
}

function createNewChat() {
  const newChat = {
    id: 'chat_' + Date.now(),
    title: 'New Conversation',
    createdAt: new Date().toISOString(),
    messages: []
  };
  appState.chats.unshift(newChat);
  appState.activeChatId = newChat.id;
  saveChats();
  renderSidebarHistory();
  renderActiveChat();
  elements.chatInput.focus();
}

function deleteChat(chatId, event) {
  if (event) event.stopPropagation();
  appState.chats = appState.chats.filter(c => c.id !== chatId);
  if (appState.chats.length === 0) {
    createNewChat();
  } else if (appState.activeChatId === chatId) {
    appState.activeChatId = appState.chats[0].id;
  }
  saveChats();
  renderSidebarHistory();
  renderActiveChat();
}

function selectChat(chatId) {
  if (appState.activeChatId === chatId) return;
  appState.activeChatId = chatId;
  saveChats();
  renderSidebarHistory();
  renderActiveChat();
}

function applyTheme(theme) {
  if (theme === 'system') {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  } else {
    document.documentElement.setAttribute('data-theme', theme);
  }
  localStorage.setItem(STORAGE_KEYS.THEME, theme);
}

// UI Rendering
function renderSidebarHistory() {
  elements.historyContainer.innerHTML = '';
  appState.chats.forEach(chat => {
    const item = document.createElement('div');
    item.className = 'history-item' + (chat.id === appState.activeChatId ? ' active' : '');
    item.onclick = () => selectChat(chat.id);

    const title = document.createElement('span');
    title.className = 'history-title';
    title.textContent = chat.title || 'New Conversation';

    const actions = document.createElement('div');
    actions.className = 'history-actions';

    const btnDel = document.createElement('button');
    btnDel.className = 'btn-history-action';
    btnDel.title = 'Delete chat';
    btnDel.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`;
    btnDel.onclick = (e) => deleteChat(chat.id, e);

    actions.appendChild(btnDel);
    item.appendChild(title);
    item.appendChild(actions);
    elements.historyContainer.appendChild(item);
  });
}

function renderActiveChat() {
  const activeChat = appState.chats.find(c => c.id === appState.activeChatId);
  if (!activeChat || activeChat.messages.length === 0) {
    elements.emptyState.style.display = 'flex';
    elements.messagesContainer.style.display = 'none';
    elements.messagesContainer.innerHTML = '';
  } else {
    elements.emptyState.style.display = 'none';
    elements.messagesContainer.style.display = 'block';
    elements.messagesContainer.innerHTML = '';
    activeChat.messages.forEach(msg => renderMessageRow(msg, false));
    scrollToBottom();
  }
}

// Guided Pipeline HTML Generator
function renderGuidedPipelineHtml(pipeline, msgId) {
  const pId = 'pipe_' + msgId;
  window['pipeline_data_' + pId] = pipeline;

  let shapeHtml = pipeline.foundation.shape_progression.map((s, idx) => {
    return `<span class="shape-step">${s.step}: <strong>${s.shape}</strong></span>` +
      (idx < pipeline.foundation.shape_progression.length - 1 ? `<span class="shape-arrow">→</span>` : '');
  }).join(' ');

  let configFieldsHtml = pipeline.config_fields.map(f => {
    return `<div class="config-field">
      <label class="audit-item-label">${f.label}:</label>
      <input type="text" class="config-input" value="${f.default}" data-key="${f.key}" data-pipe="${pId}" oninput="updatePipelineConfig(this)">
    </div>`;
  }).join('');

  let codeChunksHtml = '';
  let guideCardsHtml = '';
  let fullScriptCode = '';

  pipeline.chunks.forEach((chunk, idx) => {
    let resolvedCode = chunk.code;
    pipeline.config_fields.forEach(f => {
      resolvedCode = resolvedCode.replaceAll(`__${f.key}__`, f.default);
    });

    fullScriptCode += `\n# --- ${chunk.title} ---\n` + resolvedCode + '\n';

    codeChunksHtml += `
      <div class="pipeline-chunk-wrapper ${idx === 0 ? 'active' : ''}" id="${pId}-code-${chunk.id}" onmouseenter="highlightPipelineChunk('${pId}', '${chunk.id}')" onclick="highlightPipelineChunk('${pId}', '${chunk.id}')">
        <div class="chunk-code-box">
          <div class="chunk-code-header">
            <span>${chunk.title}</span>
            <button class="btn-copy-code" style="position: static;" onclick="event.stopPropagation(); copyCode(this)">Copy Chunk</button>
          </div>
          ${chunk.id === 'chunk-1-config' ? `<div style="padding: 10px 12px; background: #101624; border-bottom: 1px solid var(--border-subtle);"><div class="audit-item-label" style="margin-bottom: 4px; color: var(--accent-secondary);">Fill-in-the-Blank Path Configuration:</div><div class="config-pill-grid">${configFieldsHtml}</div></div>` : ''}
          <pre class="chunk-code-body"><code>${resolvedCode}</code></pre>
        </div>
      </div>
    `;

    guideCardsHtml += `
      <div class="guide-chunk-card ${idx === 0 ? 'active' : ''}" id="${pId}-guide-${chunk.id}" onclick="highlightPipelineChunk('${pId}', '${chunk.id}')">
        <div class="guide-chunk-title">
          <span>${chunk.title}</span>
        </div>
        <div class="guide-meta-block">
          <strong>What is this?</strong> <span>${chunk.guide.what}</span>
        </div>
        <div class="guide-meta-block">
          <strong>Why are we doing this?</strong> <span>${chunk.guide.why}</span>
        </div>
        ${chunk.guide.bio_change ? `<div class="guide-meta-block"><strong>Biological Effect:</strong> <span>${chunk.guide.bio_change}</span></div>` : ''}
        ${chunk.guide.data_in ? `<div class="guide-meta-block"><strong>Data In:</strong> <span style="font-family: var(--font-mono);">${chunk.guide.data_in}</span> | <strong>Data Out:</strong> <span style="font-family: var(--font-mono);">${chunk.guide.data_out}</span></div>` : ''}
        ${chunk.guide.scores_vs_loadings ? `<div class="guide-box-callout"><strong>Scores vs. Loadings:</strong> ${chunk.guide.scores_vs_loadings}</div>` : ''}
        ${chunk.guide.modify ? `<div class="guide-box-callout"><strong>Safe User Customization:</strong> ${chunk.guide.modify}</div>` : ''}
        ${chunk.guide.warning ? `<div class="guide-box-callout warning"><strong>⚠️ Statistical Alert:</strong> ${chunk.guide.warning}</div>` : ''}
        ${chunk.guide.troubleshooting ? `
          <div class="guide-box-callout troubleshooting">
            <strong>Contextual Troubleshooting:</strong>
            <div>${chunk.guide.troubleshooting}</div>
          </div>` : ''}
      </div>
    `;
  });

  return `
    <div class="guided-pipeline-container" id="${pId}-container">
      <div class="pipeline-header">
        <div class="pipeline-title-row">
          <div style="font-weight: 700; font-size: 15px; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
            <span>${pipeline.title}</span>
            <span class="pipeline-badge">Guided Pipeline</span>
          </div>
          <button class="btn-copy-code" style="position: static;" onclick="downloadFullScript('${pId}')">Download Full .py</button>
        </div>
        
        <!-- Controls Bar -->
        <div class="pipeline-controls-bar">
          <div class="view-mode-tabs">
            <button class="tab-btn active" onclick="switchPipelineViewMode(this, 'split', '${pId}')">Split View (Code + Guide)</button>
            <button class="tab-btn" onclick="switchPipelineViewMode(this, 'step', '${pId}')">Step-by-Step</button>
            <button class="tab-btn" onclick="switchPipelineViewMode(this, 'full', '${pId}')">Full Script</button>
          </div>
          <div class="strictness-select-wrap">
            <span>Pedagogical Level:</span>
            <select class="app-select" onchange="switchStrictnessLevel(this.value, '${pId}')">
              <option value="standard">Standard</option>
              <option value="strict">Strict (Audit Warnings)</option>
              <option value="teaching" selected>Teaching (Bio to Code)</option>
            </select>
          </div>
        </div>

        <!-- Layer 1: Foundation Box -->
        <div class="pipeline-foundation-card">
          <div class="foundation-grid">
            <div class="foundation-item">
              <span class="foundation-label">Experimental Unit</span>
              <span class="foundation-val">${pipeline.foundation.experimental_unit}</span>
            </div>
            <div class="foundation-item">
              <span class="foundation-label">Observation Level</span>
              <span class="foundation-val">${pipeline.foundation.observation_unit}</span>
            </div>
            <div class="foundation-item">
              <span class="foundation-label">Assay & Design Matrix</span>
              <span class="foundation-val" style="font-size: 12px;">${pipeline.foundation.measurement_unit}</span>
            </div>
          </div>
          <div class="shape-tracker-row">
            <span class="foundation-label" style="margin-right: 6px;">Matrix Dimension Flow:</span>
            ${shapeHtml}
          </div>
        </div>
      </div>

      <!-- Layer 2 & 3: Two-Pane View -->
      <div class="pipeline-split-view" id="${pId}-split-view">
        <div class="code-pane" id="${pId}-code-pane">
          ${codeChunksHtml}
        </div>
        <div class="guide-pane" id="${pId}-guide-pane">
          ${guideCardsHtml}
        </div>
      </div>

      <!-- Step-by-Step Navigation Bar (Hidden in standard split) -->
      <div class="step-nav-bar" id="${pId}-step-nav" style="display: none;">
        <button class="btn-sidebar-toggle" style="border: 1px solid var(--border-subtle); padding: 6px 12px;" onclick="stepPipelineStage(-1, '${pId}')">← Previous Stage</button>
        <span id="${pId}-step-indicator" style="font-size: 13px; font-weight: 600; color: var(--accent-secondary);">Stage 1 of ${pipeline.chunks.length}</span>
        <button class="btn-sidebar-toggle" style="border: 1px solid var(--border-subtle); padding: 6px 12px; background: var(--bg-surface-hover);" onclick="stepPipelineStage(1, '${pId}')">Next Stage →</button>
      </div>

      <!-- Full Script View (Hidden by default) -->
      <div class="full-script-view" id="${pId}-full-script">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="font-size: 12px; color: var(--text-muted);">Consolidated executable script with checkpoints:</span>
          <button class="btn-copy-code" style="position: static;" onclick="copyCode(this)">Copy Full Script</button>
        </div>
        <pre><code class="language-python" id="${pId}-full-code-text">${fullScriptCode}</code></pre>
      </div>
    </div>
  `;
}

// Global Interactivity Handlers for Guided Pipeline
window.highlightPipelineChunk = function(pId, chunkId) {
  const container = document.getElementById(`${pId}-container`);
  if (!container) return;

  container.querySelectorAll('.pipeline-chunk-wrapper').forEach(el => el.classList.remove('active'));
  container.querySelectorAll('.guide-chunk-card').forEach(el => el.classList.remove('active'));

  const codeEl = document.getElementById(`${pId}-code-${chunkId}`);
  const guideEl = document.getElementById(`${pId}-guide-${chunkId}`);

  if (codeEl) codeEl.classList.add('active');
  if (guideEl) {
    guideEl.classList.add('active');
    guideEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};

window.switchPipelineViewMode = function(btn, mode, pId) {
  const container = document.getElementById(`${pId}-container`);
  if (!container) return;

  container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const splitView = document.getElementById(`${pId}-split-view`);
  const stepNav = document.getElementById(`${pId}-step-nav`);
  const fullScript = document.getElementById(`${pId}-full-script`);

  if (mode === 'split') {
    splitView.style.display = 'grid';
    stepNav.style.display = 'none';
    fullScript.style.display = 'none';
    container.querySelectorAll('.pipeline-chunk-wrapper').forEach(el => el.style.display = 'block');
    container.querySelectorAll('.guide-chunk-card').forEach(el => el.style.display = 'block');
  } else if (mode === 'step') {
    splitView.style.display = 'grid';
    stepNav.style.display = 'flex';
    fullScript.style.display = 'none';
    window[`${pId}_current_stage`] = 0;
    renderCurrentStage(pId, 0);
  } else if (mode === 'full') {
    splitView.style.display = 'none';
    stepNav.style.display = 'none';
    fullScript.style.display = 'block';
  }
};

function renderCurrentStage(pId, stageIdx) {
  const pipeline = window['pipeline_data_' + pId];
  if (!pipeline) return;

  const total = pipeline.chunks.length;
  const chunk = pipeline.chunks[stageIdx];

  const container = document.getElementById(`${pId}-container`);
  container.querySelectorAll('.pipeline-chunk-wrapper').forEach(el => el.style.display = 'none');
  container.querySelectorAll('.guide-chunk-card').forEach(el => el.style.display = 'none');

  const codeEl = document.getElementById(`${pId}-code-${chunk.id}`);
  const guideEl = document.getElementById(`${pId}-guide-${chunk.id}`);

  if (codeEl) { codeEl.style.display = 'block'; codeEl.classList.add('active'); }
  if (guideEl) { guideEl.style.display = 'block'; guideEl.classList.add('active'); }

  const indicator = document.getElementById(`${pId}-step-indicator`);
  if (indicator) indicator.textContent = `Stage ${stageIdx + 1} of ${total}: ${chunk.title}`;
}

window.stepPipelineStage = function(delta, pId) {
  const pipeline = window['pipeline_data_' + pId];
  if (!pipeline) return;

  let current = window[`${pId}_current_stage`] || 0;
  current = Math.max(0, Math.min(pipeline.chunks.length - 1, current + delta));
  window[`${pId}_current_stage`] = current;
  renderCurrentStage(pId, current);
};

window.updatePipelineConfig = function(input) {
  const key = input.getAttribute('data-key');
  const pId = input.getAttribute('data-pipe');
  const val = input.value.trim();

  const codeTextEl = document.querySelector(`#${pId}-code-chunk-1-config code`);
  if (codeTextEl) {
    let text = codeTextEl.textContent;
    // Replace variable assignment line
    const regex = new RegExp(`(${key}\\s*=\\s*)[^\\n#]+`, 'g');
    if (key === 'N_PCS') {
      text = text.replace(regex, `$1${val || 20}`);
    } else {
      text = text.replace(regex, `$1"${val}"`);
    }
    codeTextEl.textContent = text;
  }

  // Notify backend of pipeline parameter change
  fetch('/api/pipeline/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      activeChatId: appState.activeChatId,
      key: key,
      value: val
    })
  }).catch(() => {});
};

window.downloadFullScript = function(pId) {
  const codeEl = document.getElementById(`${pId}-full-code-text`);
  if (!codeEl) return;
  const text = codeEl.textContent;
  const blob = new Blob([text], { type: 'text/x-python' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'bioreason_pipeline.py';
  a.click();
};

window.switchStrictnessLevel = function(level, pId) {
  const container = document.getElementById(`${pId}-container`);
  if (!container) return;
  const warnings = container.querySelectorAll('.guide-box-callout.warning');
  if (level === 'strict') {
    warnings.forEach(w => w.style.boxShadow = '0 0 8px rgba(245, 158, 11, 0.4)');
  } else {
    warnings.forEach(w => w.style.boxShadow = 'none');
  }
};

function renderMessageRow(msg, isStreaming = false) {
  const row = document.createElement('div');
  row.className = `message-row ${msg.role}`;
  row.id = msg.id;

  if (msg.role === 'user') {
    const bubble = document.createElement('div');
    bubble.className = 'user-bubble';
    
    if (msg.attachmentName) {
      const badge = document.createElement('div');
      badge.className = 'attachment-pill';
      badge.style.marginBottom = '6px';
      badge.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg> <span>${msg.attachmentName}</span>`;
      bubble.appendChild(badge);
    }
    
    const textSpan = document.createElement('div');
    textSpan.textContent = msg.content;
    bubble.appendChild(textSpan);
    row.appendChild(bubble);
  } else {
    // Assistant message
    const avatar = document.createElement('div');
    avatar.className = 'assistant-avatar';
    avatar.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`;
    row.appendChild(avatar);

    const body = document.createElement('div');
    body.className = 'assistant-body';

    if (msg.guided_pipeline) {
      body.innerHTML = renderGuidedPipelineHtml(msg.guided_pipeline, msg.id);
    } else {
      body.innerHTML = formatMarkdown(msg.content);
    }
    row.appendChild(body);

    // Collapsible Scientific Audit Card
    if (msg.audit) {
      const auditWrapper = document.createElement('div');
      auditWrapper.className = 'scientific-audit-wrapper';
      auditWrapper.innerHTML = `
        <button class="btn-audit-toggle" onclick="toggleAudit(this)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          <span>Scientific Audit &amp; Rigor Trace</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chevron"><path d="M6 9l6 6 6-6"/></svg>
        </button>
        <div class="audit-card">
          <div class="audit-grid">
            <div class="audit-item">
              <span class="audit-item-label">Experimental Unit</span>
              <span class="audit-item-val">${msg.audit.experimental_unit || 'Unspecified'}</span>
            </div>
            <div class="audit-item">
              <span class="audit-item-label">Sample Size &amp; Power</span>
              <span class="audit-item-val">${msg.audit.sample_size_check || 'Nominal'}</span>
            </div>
            <div class="audit-item">
              <span class="audit-item-label">Primary Issue / Flaw</span>
              <span class="audit-item-val" style="color: var(--accent-critique); font-weight: 600;">${msg.audit.primary_issue || 'None detected'}</span>
            </div>
            <div class="audit-item">
              <span class="audit-item-label">Recommended Remediation</span>
              <span class="audit-item-val">${msg.audit.recommended_remediation || 'Workflow scientifically sound.'}</span>
            </div>
          </div>
        </div>
      `;
      row.appendChild(auditWrapper);
    }

    // Message Actions Bar
    const actions = document.createElement('div');
    actions.className = 'message-actions';
    actions.innerHTML = `
      <button class="btn-action-icon" title="Copy response" onclick="copyMessageText(this)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      </button>
      <button class="btn-action-icon" title="Helpful" onclick="this.classList.toggle('active')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
      </button>
      <button class="btn-action-icon" title="Not helpful" onclick="this.classList.toggle('active')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"/></svg>
      </button>
    `;
    row.appendChild(actions);
  }

  elements.messagesContainer.appendChild(row);
}

function scrollToBottom() {
  elements.chatScrollArea.scrollTop = elements.chatScrollArea.scrollHeight;
}

// Generation & Dispatch
let streamInterval = null;

async function handleSend() {
  const text = elements.chatInput.value.trim();
  if (!text || appState.isGenerating) return;

  const activeChat = appState.chats.find(c => c.id === appState.activeChatId);
  if (!activeChat) return;

  // Auto-title on first message
  if (activeChat.messages.length === 0) {
    activeChat.title = text.slice(0, 32) + (text.length > 32 ? '...' : '');
    renderSidebarHistory();
  }

  // 1. Append User Message
  const userMsg = {
    id: 'msg_' + Date.now(),
    role: 'user',
    content: text,
    attachmentName: appState.attachedFile ? appState.attachedFile.name : null,
    timestamp: new Date().toISOString()
  };
  activeChat.messages.push(userMsg);
  saveChats();

  // Clear inputs
  elements.chatInput.value = '';
  elements.chatInput.style.height = 'auto';
  elements.btnSend.disabled = true;
  clearAttachment();
  renderActiveChat();

  // 2. Start Backend API Call & Streaming
  appState.isGenerating = true;
  elements.btnSend.style.display = 'none';
  elements.btnStop.style.display = 'flex';

  const assistantMsgId = 'msg_' + (Date.now() + 1);
  const startTime = Date.now();

  // Create empty assistant row with typing indicator
  const assistantRow = document.createElement('div');
  assistantRow.className = 'message-row assistant';
  assistantRow.id = `msg-${assistantMsgId}`;
  assistantRow.innerHTML = `
    <div class="assistant-body">
      <div class="typing-indicator">
        <span>BioReason is reasoning</span>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  elements.messagesContainer.appendChild(assistantRow);
  scrollToBottom();

  try {
    const payload = {
      activeChatId: appState.activeChatId,
      messages: activeChat.messages,
      devMode: appState.devMode
    };

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok || data.status === 'error') {
      const details = data.diagnostics ? `\n\n${JSON.stringify(data.diagnostics, null, 2)}` : '';
      throw new Error(`${data.message || `Server returned HTTP ${response.status}: ${response.statusText}`}${details}`);
    }
    const targetResponse = data.message || '';
    let currentLength = 0;
    const chunkSize = 16;

    streamInterval = setInterval(() => {
      currentLength += chunkSize;
      if (currentLength >= targetResponse.length) {
        currentLength = targetResponse.length;
        clearInterval(streamInterval);
        streamInterval = null;

        const latencyMs = Date.now() - startTime;
        const finalMsg = {
          id: assistantMsgId,
          role: 'assistant',
          content: targetResponse,
          guided_pipeline: data.guided_pipeline || null,
          audit: data.audit || null,
          source_trace: data.source_trace || 'MODEL_GENERATED',
          timestamp: new Date().toISOString(),
          latency: latencyMs
        };
        activeChat.messages.push(finalMsg);
        saveChats();

        appState.isGenerating = false;
        elements.btnSend.style.display = 'flex';
        elements.btnStop.style.display = 'none';
        elements.btnSend.disabled = false;

        // Update developer mode telemetry
        if (elements.devLatency) elements.devLatency.textContent = `${latencyMs} ms`;
        if (elements.devTokens) elements.devTokens.textContent = `${Math.round(text.length / 4)} / ${Math.round(targetResponse.length / 4)}`;
        if (elements.devJsonDisplay) {
          elements.devJsonDisplay.textContent = JSON.stringify({
            model: (data.provenance && data.provenance.model) || "BR-VERIFIED-SFT-002",
            checkpoint: data.model_checkpoint || (data.provenance && data.provenance.checkpoint) || "BR-VERIFIED-SFT-002 (final_adapter)",
            source_trace: data.source_trace || "MODEL_GENERATED",
            pipeline_state: data.pipeline_state,
            provenance: data.provenance || null,
            latency_ms: latencyMs,
            diagnostics: data.diagnostics || {}
          }, null, 2);
        }

        renderActiveChat();
      } else {
        const partialText = targetResponse.slice(0, currentLength);
        assistantRow.querySelector('.assistant-body').innerHTML = formatMarkdown(partialText);
        scrollToBottom();
      }
    }, 20);

  } catch (err) {
    // Show explicit error fallback
    if (streamInterval) {
      clearInterval(streamInterval);
      streamInterval = null;
    }
    appState.isGenerating = false;
    elements.btnSend.style.display = 'flex';
    elements.btnStop.style.display = 'none';
    elements.btnSend.disabled = false;

    const errMsg = {
      id: assistantMsgId,
      role: 'assistant',
      content: `**BIOREASON_INFERENCE_FAILED**: ${err.message}\n\n*Developer Diagnostics*: Ensure BioReason server is running on port 8088.`,
      source_trace: 'ERROR',
      timestamp: new Date().toISOString(),
      latency: Date.now() - startTime
    };
    activeChat.messages.push(errMsg);
    saveChats();
    renderActiveChat();
  }
}

function handleStopGeneration() {
  if (streamInterval) {
    clearInterval(streamInterval);
    streamInterval = null;
  }
  appState.isGenerating = false;
  elements.btnSend.style.display = 'flex';
  elements.btnStop.style.display = 'none';
  elements.btnSend.disabled = elements.chatInput.value.trim().length === 0;
  saveChats();
  renderActiveChat();
}

function handleAttachment(file) {
  if (!file) return;
  appState.attachedFile = file;
  elements.attachmentPreview.style.display = 'flex';
  elements.attachmentPreview.innerHTML = `
    <div class="attachment-pill">
      <span>📄 ${file.name}</span>
      <button class="btn-remove-attachment" onclick="clearAttachment()">✕</button>
    </div>
  `;
}

window.clearAttachment = function() {
  appState.attachedFile = null;
  elements.attachmentPreview.style.display = 'none';
  elements.attachmentPreview.innerHTML = '';
  elements.fileInput.value = '';
};

// Event Listeners Initialization
function setupEventListeners() {
  // Input auto-resize & key bindings
  elements.chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    elements.btnSend.disabled = (this.value.trim().length === 0);
  });

  elements.chatInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  elements.btnSend.addEventListener('click', handleSend);
  elements.btnStop.addEventListener('click', handleStopGeneration);

  // New Chat buttons
  elements.btnNewChatSidebar.addEventListener('click', createNewChat);
  elements.btnTopNewChat.addEventListener('click', createNewChat);

  // Sidebar toggles
  elements.btnCollapseSidebar.addEventListener('click', () => {
    elements.sidebar.classList.add('collapsed');
    elements.btnExpandSidebar.style.display = 'flex';
  });

  elements.btnExpandSidebar.addEventListener('click', () => {
    elements.sidebar.classList.remove('collapsed');
    elements.btnExpandSidebar.style.display = 'none';
  });

  // Prompt chips
  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', function() {
      const prompt = this.getAttribute('data-prompt');
      elements.chatInput.value = prompt;
      elements.chatInput.style.height = 'auto';
      elements.chatInput.style.height = (elements.chatInput.scrollHeight) + 'px';
      elements.btnSend.disabled = false;
      handleSend();
    });
  });

  // Attachments
  elements.btnAttach.addEventListener('click', () => elements.fileInput.click());
  elements.fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleAttachment(e.target.files[0]);
    }
  });

  // Settings Modal
  const openSettings = () => elements.settingsModal.classList.add('open');
  const closeSettings = () => elements.settingsModal.classList.remove('open');
  elements.btnOpenSettingsSidebar.addEventListener('click', openSettings);
  elements.btnOpenSettingsTop.addEventListener('click', openSettings);
  elements.btnCloseSettings.addEventListener('click', closeSettings);
  elements.settingsModal.addEventListener('click', (e) => {
    if (e.target === elements.settingsModal) closeSettings();
  });

  elements.settingTheme.addEventListener('change', (e) => applyTheme(e.target.value));

  elements.settingResponseMode.addEventListener('change', (e) => {
    appState.responseMode = e.target.value;
    localStorage.setItem(STORAGE_KEYS.RESPONSE_MODE, e.target.value);
    renderActiveChat();
  });

  elements.settingDevMode.addEventListener('change', (e) => {
    appState.devMode = e.target.checked;
    localStorage.setItem(STORAGE_KEYS.DEV_MODE, e.target.checked);
    elements.btnToggleDev.style.display = e.target.checked ? 'flex' : 'none';
    if (!e.target.checked) elements.devDrawer.classList.remove('open');
  });

  elements.btnClearChats.addEventListener('click', () => {
    if (confirm('Clear all conversation history? This cannot be undone.')) {
      appState.chats = [];
      localStorage.removeItem(STORAGE_KEYS.CHATS);
      localStorage.removeItem(STORAGE_KEYS.ACTIVE_CHAT);
      createNewChat();
      closeSettings();
    }
  });

  // Developer Drawer
  elements.btnToggleDev.addEventListener('click', () => {
    elements.devDrawer.classList.toggle('open');
  });
  elements.btnCloseDev.addEventListener('click', () => {
    elements.devDrawer.classList.remove('open');
  });
}

// Bootstrapping
window.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadState();
});
