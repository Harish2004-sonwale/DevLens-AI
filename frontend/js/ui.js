/**
 * DevLens AI — UI utility helpers
 * AI-Powered Developer Intelligence Platform
 */

const toastContainer = document.getElementById('toast-container');

function showToast(message, type = 'info', duration = 3500) {
  const icons = { success: '✅', error: '❌', info: '💡' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || '💡'}</span>
    <span class="toast-msg">${escHtml(message)}</span>
  `;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOutRight 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function showAlert(id, message, kind = 'error') {
  const el = document.getElementById(id);
  if (!el) return;
  if (!message) {
    el.hidden = true;
    el.textContent = '';
    el.className = 'alert';
    return;
  }
  el.hidden = false;
  el.className = `alert alert-${kind}`;
  el.textContent = message;
}

async function copyToClipboard(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
    if (btn) {
      btn.classList.add('copied');
      const original = btn.textContent;
      btn.textContent = 'Copied';
      setTimeout(() => {
        btn.classList.remove('copied');
        btn.textContent = original || 'Copy';
      }, 2000);
    }
    showToast('Copied to clipboard', 'success', 2000);
  } catch (_) {
    showToast('Copy failed', 'error');
  }
}

function setLoading(btn, loading) {
  if (!btn) return;
  if (loading) {
    btn.classList.add('loading');
    btn.disabled = true;
  } else {
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

function showResult(sectionId) {
  const el = document.getElementById(sectionId);
  if (el) {
    el.classList.add('visible');
    setTimeout(() => el.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 80);
  }
}

function hideResult(sectionId) {
  const el = document.getElementById(sectionId);
  if (el) el.classList.remove('visible');
}

function animateScoreRing(score) {
  const ring = document.querySelector('.ring-fill');
  const numEl = document.querySelector('.score-ring-number');
  if (!ring) return;
  const circumference = 283;
  const offset = circumference - (score / 100) * circumference;
  setTimeout(() => {
    ring.style.strokeDashoffset = offset;
    if (numEl) {
      let current = 0;
      const step = Math.max(score / 60, 0.5);
      const interval = setInterval(() => {
        current = Math.min(current + step, score);
        const val = numEl.querySelector('.score-val');
        if (val) val.textContent = Math.round(current);
        if (current >= score) clearInterval(interval);
      }, 16);
    }
  }, 100);
}

const LANG_META = {
  python:     { display: 'Python',     icon: '🐍', ext: '.py' },
  java:       { display: 'Java',       icon: '☕', ext: '.java' },
  c:          { display: 'C',          icon: 'C', ext: '.c' },
  cpp:        { display: 'C++',        icon: 'C++', ext: '.cpp' },
  javascript: { display: 'JavaScript', icon: 'JS', ext: '.js' },
  typescript: { display: 'TypeScript', icon: 'TS', ext: '.ts' },
  csharp:     { display: 'C#',         icon: 'C#', ext: '.cs' },
  go:         { display: 'Go',         icon: 'Go', ext: '.go' },
};

const FRAMEWORKS = {
  python: ['pytest', 'unittest'],
  java: ['JUnit'],
  javascript: ['Jest'],
  typescript: ['Jest'],
  cpp: ['GoogleTest'],
  c: ['Unity'],
  csharp: ['xUnit', 'NUnit'],
  go: ['testing'],
};

function getLangMeta(key) {
  return LANG_META[key] || { display: key, icon: '', ext: '.txt' };
}

function downloadText(text, filename) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type: 'text/plain' }));
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function navigateTo(page) {
  const tabs = document.querySelectorAll('.nav-tab');
  const pages = document.querySelectorAll('.page');
  tabs.forEach((t) => {
    const on = t.dataset.page === page;
    t.classList.toggle('active', on);
    t.setAttribute('aria-selected', on ? 'true' : 'false');
  });
  pages.forEach((p) => p.classList.toggle('active', p.id === `page-${page}`));
  if (page === 'history' && typeof loadHistory === 'function') loadHistory();
  if (page === 'dashboard' && typeof loadDashboardActivity === 'function') loadDashboardActivity();
}

function initTabs() {
  document.querySelectorAll('.nav-tab').forEach((tab) => {
    tab.addEventListener('click', () => navigateTo(tab.dataset.page));
  });
  document.querySelectorAll('[data-nav]').forEach((el) => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      navigateTo(el.dataset.nav);
    });
  });
}

function initCollapsibles(containerSelector, headerSelector, bodySelector) {
  document.addEventListener('click', (e) => {
    const header = e.target.closest(headerSelector);
    if (!header) return;
    const item = header.closest(containerSelector);
    if (!item) return;
    const body = item.querySelector(bodySelector);
    if (!body) return;
    const toggle = header.querySelector('.bug-toggle, .test-toggle');
    body.classList.toggle('open');
    if (toggle) toggle.textContent = body.classList.contains('open') ? '▲' : '▼';
  });
}

async function checkHealth() {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  try {
    const data = await apiHealth();
    const ok = data.status === 'ok' && data.gemini_configured;
    dot.className = 'status-dot' + (ok ? '' : ' offline');
    text.textContent = ok ? 'Online' : 'No API Key';
  } catch (_) {
    dot.className = 'status-dot offline';
    text.textContent = 'Offline';
  }
}

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function diffLines(original, modified) {
  const a = String(original || '').split('\n');
  const b = String(modified || '').split('\n');
  const n = a.length;
  const m = b.length;
  const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const left = [];
  const right = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      left.push({ type: 'same', num: i + 1, text: a[i] });
      right.push({ type: 'same', num: j + 1, text: b[j] });
      i += 1;
      j += 1;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      left.push({ type: 'removed', num: i + 1, text: a[i] });
      right.push({ type: 'empty', num: '', text: '' });
      i += 1;
    } else {
      left.push({ type: 'empty', num: '', text: '' });
      right.push({ type: 'added', num: j + 1, text: b[j] });
      j += 1;
    }
  }
  while (i < n) {
    left.push({ type: 'removed', num: i + 1, text: a[i] });
    right.push({ type: 'empty', num: '', text: '' });
    i += 1;
  }
  while (j < m) {
    left.push({ type: 'empty', num: '', text: '' });
    right.push({ type: 'added', num: j + 1, text: b[j] });
    j += 1;
  }
  return { left, right };
}

function renderLine(line) {
  const cls = line.type === 'added' ? 'added' : line.type === 'removed' ? 'removed' : '';
  return `<div class="diff-line ${cls}"><span class="diff-line-num">${line.num || ''}</span><span class="diff-line-code">${escHtml(line.text)}</span></div>`;
}

function renderDiff(containerId, original, modified, options = {}) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const { left, right } = diffLines(original, modified);
  container.innerHTML = `
    <div class="diff-container">
      <div class="diff-header">
        <span class="diff-title">Before / After</span>
        <div class="editor-actions">
          <button class="btn btn-ghost btn-sm" data-diff="copy">Copy</button>
          <button class="btn btn-ghost btn-sm" data-diff="download">Download</button>
          <button class="btn btn-secondary btn-sm" data-diff="apply">Apply Changes</button>
        </div>
      </div>
      <div class="diff-grid">
        <div class="diff-col">
          <div class="diff-col-title">Original</div>
          ${left.map(renderLine).join('')}
        </div>
        <div class="diff-col">
          <div class="diff-col-title">Modified</div>
          ${right.map(renderLine).join('')}
        </div>
      </div>
    </div>
  `;
  const copyBtn = container.querySelector('[data-diff="copy"]');
  const dlBtn = container.querySelector('[data-diff="download"]');
  const applyBtn = container.querySelector('[data-diff="apply"]');
  if (copyBtn) copyBtn.addEventListener('click', () => copyToClipboard(modified, copyBtn));
  if (dlBtn) {
    dlBtn.addEventListener('click', () => {
      downloadText(modified, options.filename || 'modified.txt');
    });
  }
  if (applyBtn) {
    applyBtn.addEventListener('click', () => {
      if (typeof options.onApply === 'function') options.onApply(modified);
      showToast('Changes applied to editor', 'success');
    });
  }
}

function clearDiff(containerId) {
  const container = document.getElementById(containerId);
  if (container) container.innerHTML = '';
}

function formatTimestamp(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString();
  } catch (_) {
    return iso;
  }
}

function operationLabel(op) {
  const map = {
    translate: 'Convert',
    convert: 'Convert',
    debug: 'Debug',
    debug_fix: 'Debug Fix',
    optimize: 'Optimize',
    explain: 'Explain',
    analyze: 'Analyze',
    analyze_improve: 'Improve',
    generate_tests: 'Tests',
  };
  return map[op] || op;
}

function operationPage(op) {
  const map = {
    translate: 'convert',
    convert: 'convert',
    debug: 'debug',
    debug_fix: 'debug',
    optimize: 'optimize',
    explain: 'explain',
    analyze: 'analyze',
    analyze_improve: 'analyze',
    generate_tests: 'tests',
  };
  return map[op] || 'dashboard';
}

function operationBadgeClass(op) {
  if (op === 'translate' || op === 'convert') return 'convert';
  if (op === 'debug' || op === 'debug_fix') return 'debug';
  if (op === 'generate_tests') return 'tests';
  if (op === 'analyze_improve') return 'analyze';
  return op || 'convert';
}
