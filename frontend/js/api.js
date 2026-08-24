/**
 * DevLens AI — API Client
 * AI-Powered Developer Intelligence Platform
 * Understand. Improve. Transform. Test.
 */

const API_BASE = '/api';

/**
 * Generic request helper with sanitized error messaging.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const res = await fetch(url, config);
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      let message = 'An unexpected error occurred.';
      if (data.error && typeof data.error === 'string') {
        message = data.error;
      } else if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
      }
      if (res.status === 429) {
        message = 'Rate limit exceeded. Please wait and try again.';
      }
      if (res.status === 408 || /timeout/i.test(message)) {
        message = 'The request timed out. Try a smaller snippet or retry.';
      }
      throw new Error(message);
    }

    return data;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Could not connect to the DevLens AI backend. Ensure the server is running.');
    }
    throw err;
  }
}

/* ── Public API Methods ──────────────────────────────────── */

async function apiConvert(source_code, source_language, target_language, preserve_comments = true) {
  return request('/convert', {
    method: 'POST',
    body: JSON.stringify({
      source_code,
      source_language,
      target_language,
      preserve_comments,
    }),
  });
}

async function apiDetectLanguage(source_code) {
  return request('/detect-language', {
    method: 'POST',
    body: JSON.stringify({ source_code }),
  });
}

async function apiDebug(source_code, language) {
  return request('/debug', {
    method: 'POST',
    body: JSON.stringify({ source_code, language }),
  });
}

async function apiDebugFix(source_code, language, issues_summary = '') {
  return request('/debug/fix', {
    method: 'POST',
    body: JSON.stringify({ source_code, language, issues_summary }),
  });
}

async function apiOptimize(source_code, language, focus = 'balanced') {
  return request('/optimize', {
    method: 'POST',
    body: JSON.stringify({ source_code, language, focus }),
  });
}

async function apiExplain(source_code, language) {
  return request('/explain', {
    method: 'POST',
    body: JSON.stringify({ source_code, language }),
  });
}

async function apiAnalyze(source_code, language) {
  return request('/analyze', {
    method: 'POST',
    body: JSON.stringify({ source_code, language }),
  });
}

async function apiAnalyzeImprove(source_code, language, recommendations = []) {
  return request('/analyze/improve', {
    method: 'POST',
    body: JSON.stringify({ source_code, language, recommendations }),
  });
}

async function apiGenerateTests(source_code, language, framework = null) {
  return request('/generate-tests', {
    method: 'POST',
    body: JSON.stringify({ source_code, language, framework }),
  });
}

async function apiGetHistory(limit = 20, offset = 0, operation = null, status = null, q = null) {
  const params = new URLSearchParams({ limit, offset });
  if (operation) params.set('operation', operation);
  if (status) params.set('status', status);
  if (q) params.set('q', q);
  return request(`/history?${params.toString()}`);
}

async function apiGetHistoryItem(id) {
  return request(`/history/${id}`);
}

async function apiDeleteHistoryItem(id) {
  return request(`/history/${id}`, { method: 'DELETE' });
}

async function apiClearHistory() {
  return request('/history', { method: 'DELETE' });
}

async function apiHealth() {
  return request('/health');
}

// Window attachment for script-tag compatibility
if (typeof window !== 'undefined') {
  window.apiConvert = apiConvert;
  window.apiDetectLanguage = apiDetectLanguage;
  window.apiDebug = apiDebug;
  window.apiDebugFix = apiDebugFix;
  window.apiOptimize = apiOptimize;
  window.apiExplain = apiExplain;
  window.apiAnalyze = apiAnalyze;
  window.apiAnalyzeImprove = apiAnalyzeImprove;
  window.apiGenerateTests = apiGenerateTests;
  window.apiGetHistory = apiGetHistory;
  window.apiGetHistoryItem = apiGetHistoryItem;
  window.apiDeleteHistoryItem = apiDeleteHistoryItem;
  window.apiClearHistory = apiClearHistory;
  window.apiHealth = apiHealth;
}
