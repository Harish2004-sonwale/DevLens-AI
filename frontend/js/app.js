/**
 * DevLens AI — Feature modules
 * Understand. Improve. Transform. Test.
 */

let lastDebugIssues = '';
let lastAnalyzeRecs = [];
let lastAnalyzeScore = null;

function bindDetect(btn, editor, langSel) {
  btn.addEventListener('click', async () => {
    const code = editor.value.trim();
    if (!code) { showToast('Paste some code first', 'info'); return; }
    setLoading(btn, true);
    try {
      const data = await apiDetectLanguage(code);
      if (data.detected_language && langSel.querySelector(`option[value="${data.detected_language}"]`)) {
        langSel.value = data.detected_language;
      }
      showToast(`Detected: ${data.display_name} (${Math.round((data.confidence || 0) * 100)}%)`, 'success');
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setLoading(btn, false);
    }
  });
}

function initConvert() {
  const runBtn = document.getElementById('btn-convert');
  const detectBtn = document.getElementById('btn-auto-detect');
  const swapBtn = document.getElementById('btn-swap-langs');
  const copyBtn = document.getElementById('btn-copy-converted');
  const dlBtn = document.getElementById('btn-dl-converted');
  const srcSel = document.getElementById('sel-src-lang');
  const tgtSel = document.getElementById('sel-tgt-lang');
  const srcEditor = document.getElementById('src-code');
  const outArea = document.getElementById('converted-code');
  const placeholder = document.getElementById('convert-placeholder');
  const preserveCb = document.getElementById('cb-preserve-comments');

  swapBtn.addEventListener('click', () => {
    const tmp = srcSel.value;
    srcSel.value = tgtSel.value;
    tgtSel.value = tmp;
  });

  document.getElementById('btn-convert-reset').addEventListener('click', () => {
    srcEditor.value = '';
    outArea.textContent = '';
    outArea.style.display = 'none';
    placeholder.style.display = 'flex';
    hideResult('convert-result');
    clearDiff('convert-diff');
    showAlert('convert-alert', '');
  });

  bindDetect(detectBtn, srcEditor, srcSel);

  runBtn.addEventListener('click', async () => {
    const code = srcEditor.value.trim();
    if (!code) { showToast('Paste some code to convert', 'info'); return; }
    setLoading(runBtn, true);
    hideResult('convert-result');
    showAlert('convert-alert', '');
    placeholder.style.display = 'flex';
    outArea.style.display = 'none';

    try {
      const data = await apiConvert(code, srcSel.value, tgtSel.value, preserveCb.checked);
      outArea.textContent = data.converted_code;
      outArea.style.display = 'block';
      placeholder.style.display = 'none';
      document.getElementById('convert-explanation').textContent = data.explanation || '—';
      document.getElementById('convert-quality').textContent = data.quality_score != null ? `${Math.round(data.quality_score)}/100` : '—';
      const warnList = document.getElementById('convert-warnings');
      const warnSec = document.getElementById('convert-warnings-sec');
      if (data.warnings && data.warnings.length) {
        warnList.innerHTML = data.warnings.map((w) => `<li>${escHtml(w)}</li>`).join('');
        warnSec.style.display = 'block';
      } else {
        warnSec.style.display = 'none';
      }
      const ms = data.execution_time_ms;
      document.getElementById('convert-time').textContent = ms ? `${ms.toFixed(0)} ms` : '—';
      const meta = getLangMeta(tgtSel.value);
      renderDiff('convert-diff', code, data.converted_code, {
        filename: `converted${meta.ext}`,
        onApply: (text) => { srcEditor.value = text; },
      });
      showResult('convert-result');
      showToast('Conversion complete', 'success');
      loadDashboardActivity();
    } catch (e) {
      showAlert('convert-alert', e.message);
      showToast(e.message, 'error');
    } finally {
      setLoading(runBtn, false);
    }
  });

  copyBtn.addEventListener('click', () => copyToClipboard(outArea.textContent, copyBtn));
  dlBtn.addEventListener('click', () => {
    downloadText(outArea.textContent, `converted${getLangMeta(tgtSel.value).ext}`);
  });
}

function renderBugList(data) {
  const list = document.getElementById('bug-list');
  list.innerHTML = '';
  document.getElementById('dbg-total').textContent = data.total_issues ?? 0;
  document.getElementById('dbg-critical').textContent = data.critical_count ?? 0;
  document.getElementById('dbg-high').textContent = data.high_count ?? 0;
  document.getElementById('dbg-medium').textContent = data.medium_count ?? 0;
  document.getElementById('dbg-low').textContent = data.low_count ?? 0;
  document.getElementById('dbg-summary').textContent = data.summary || '—';

  if (!data.bugs || data.bugs.length === 0) {
    list.innerHTML = `<div class="empty-state"><div class="empty-icon">✅</div><p class="empty-text">No bugs found. Code looks clean.</p></div>`;
    document.getElementById('debug-fix-actions').hidden = true;
    return;
  }

  document.getElementById('debug-fix-actions').hidden = false;
  data.bugs.forEach((bug, i) => {
    const sev = (bug.severity || 'medium').toLowerCase();
    const lineNote = bug.line_number
      ? `<span class="bug-line">Line ${bug.line_number}</span>`
      : `<span class="bug-line">Line not specified</span>`;
    list.innerHTML += `
      <div class="bug-item">
        <div class="bug-header">
          <span class="severity-badge severity-${escHtml(sev)}">${escHtml(sev)}</span>
          <span class="bug-issue">${escHtml(bug.issue)}</span>
          ${lineNote}
          <span class="bug-toggle">▼</span>
        </div>
        <div class="bug-body" id="bug-body-${i}">
          <p><strong>Explanation:</strong> ${escHtml(bug.explanation)}</p>
          ${bug.recommendation ? `<p><strong>Recommendation:</strong> ${escHtml(bug.recommendation)}</p>` : ''}
          ${bug.suggested_fix ? `<p><strong>Suggested fix:</strong></p><pre class="code-fix">${escHtml(bug.suggested_fix)}</pre>` : ''}
        </div>
      </div>`;
  });
  lastDebugIssues = (data.bugs || []).map((b) => `- [${b.severity}] ${b.issue}: ${b.explanation}`).join('\n');
}

function initDebug() {
  const runBtn = document.getElementById('btn-debug');
  const srcEditor = document.getElementById('dbg-code');
  const langSel = document.getElementById('sel-dbg-lang');
  const detectBtn = document.getElementById('btn-dbg-detect');
  const fixBtn = document.getElementById('btn-debug-fix');
  const reBtn = document.getElementById('btn-debug-reanalyze');

  bindDetect(detectBtn, srcEditor, langSel);

  document.getElementById('btn-debug-reset').addEventListener('click', () => {
    srcEditor.value = '';
    hideResult('debug-result');
    clearDiff('debug-diff');
    showAlert('debug-alert', '');
    reBtn.hidden = true;
  });

  runBtn.addEventListener('click', async () => {
    const code = srcEditor.value.trim();
    if (!code) { showToast('Paste some code to debug', 'info'); return; }
    setLoading(runBtn, true);
    hideResult('debug-result');
    showAlert('debug-alert', '');
    clearDiff('debug-diff');
    reBtn.hidden = true;
    try {
      const data = await apiDebug(code, langSel.value);
      renderBugList(data);
      showResult('debug-result');
      showToast(`Found ${data.total_issues} issue(s)`, data.critical_count > 0 ? 'error' : 'success');
      loadDashboardActivity();
    } catch (e) {
      showAlert('debug-alert', e.message);
      showToast(e.message, 'error');
    } finally {
      setLoading(runBtn, false);
    }
  });

  fixBtn.addEventListener('click', async () => {
    const code = srcEditor.value.trim();
    if (!code) return;
    setLoading(fixBtn, true);
    showAlert('debug-alert', '');
    try {
      const data = await apiDebugFix(code, langSel.value, lastDebugIssues);
      renderDiff('debug-diff', code, data.fixed_code, {
        filename: `fixed${getLangMeta(langSel.value).ext}`,
        onApply: (text) => { srcEditor.value = text; },
      });
      srcEditor.dataset.fixedCode = data.fixed_code;
      reBtn.hidden = false;
      showToast(data.fix_summary || 'Fixes generated', 'success');
      loadDashboardActivity();
    } catch (e) {
      showAlert('debug-alert', e.message);
      showToast(e.message, 'error');
    } finally {
      setLoading(fixBtn, false);
    }
  });

  reBtn.addEventListener('click', async () => {
    const fixed = srcEditor.dataset.fixedCode || srcEditor.value.trim();
    if (!fixed) return;
    setLoading(reBtn, true);
    try {
      srcEditor.value = fixed;
      const data = await apiDebug(fixed, langSel.value);
      renderBugList(data);
      showToast('Re-analysis complete', 'success');
    } catch (e) {
      showAlert('debug-alert', e.message);
      showToast(e.message, 'error');
    } finally {
      setLoading(reBtn, false);
    }
  });
}

function initOptimize() {
  const runBtn = document.getElementById('btn-optimize');
  const srcEditor = document.getElementById('opt-code');
  const outArea = document.getElementById('optimized-code');
  const placeholder = document.getElementById('opt-placeholder');
  const langSel = document.getElementById('sel-opt-lang');
  const focusSel = document.getElementById('sel-opt-focus');

  bindDetect(document.getElementById('btn-opt-detect'), srcEditor, langSel);

  document.getElementById('btn-opt-reset').addEventListener('click', () => {
    srcEditor.value = '';
    outArea.textContent = '';
    outArea.style.display = 'none';
    placeholder.style.display = 'flex';
    hideResult('optimize-result');
    clearDiff('optimize-diff');
    showAlert('optimize-alert', '');
  });

  runBtn.addEventListener('click', async () => {
    const code = srcEditor.value.trim();
    if (!code) { showToast('Paste some code to optimize', 'info'); return; }
    setLoading(runBtn, true);
    hideResult('optimize-result');
    showAlert('optimize-alert', '');
    try {
      const data = await apiOptimize(code, langSel.value, focusSel.value);
      outArea.textContent = data.optimized_code;
      outArea.style.display = 'block';
      placeholder.style.display = 'none';
      document.getElementById('opt-perf-notes').textContent = data.performance_notes || '—';
      document.getElementById('opt-read-notes').textContent = data.readability_notes || '—';
      document.getElementById('opt-time-cmp').textContent = `${data.before_time_complexity || 'N/A'} → ${data.after_time_complexity || 'N/A'}`;
      document.getElementById('opt-space-cmp').textContent = `${data.before_space_complexity || 'N/A'} → ${data.after_space_complexity || 'N/A'}`;
      document.getElementById('opt-complexity-summary').textContent = data.complexity_summary || '';

      const changeList = document.getElementById('change-list');
      changeList.innerHTML = '';
      (data.changes || []).forEach((c) => {
        const cat = (c.category || 'implementation').toLowerCase();
        changeList.innerHTML += `
          <div class="change-item">
            <span class="change-cat ${escHtml(cat)}">${escHtml(cat)}</span>
            <div class="change-text">
              <div class="change-desc">${escHtml(c.description)}</div>
              <div class="change-reason">${escHtml(c.reason)}</div>
            </div>
          </div>`;
      });
      if (!data.changes || !data.changes.length) {
        changeList.innerHTML = '<p class="empty-text">No changes made.</p>';
      }

      renderDiff('optimize-diff', code, data.optimized_code, {
        filename: `optimized${getLangMeta(langSel.value).ext}`,
        onApply: (text) => { srcEditor.value = text; },
      });
      showResult('optimize-result');
      showToast(`${(data.changes || []).length} optimization(s) applied`, 'success');
      loadDashboardActivity();
    } catch (e) {
      showAlert('optimize-alert', e.message);
      showToast(e.message, 'error');
    } finally {
      setLoading(runBtn, false);
    }
  });

  document.getElementById('btn-copy-optimized').addEventListener('click', (e) => copyToClipboard(outArea.textContent, e.currentTarget));
  document.getElementById('btn-dl-optimized').addEventListener('click', () => {
    downloadText(outArea.textContent, `optimized${getLangMeta(langSel.value).ext}`);
  });
}

function initExplain() {
  const runBtn = document.getElementById('btn-explain');
  const srcEditor = document.getElementById('expl-code');
  const langSel = document.getElementById('sel-expl-lang');
  bindDetect(document.getElementById('btn-expl-detect'), srcEditor, langSel);

  document.getElementById('btn-expl-reset').addEventListener('click', () => {
    srcEditor.value = '';
    hideResult('explain-result');
    showAlert('explain-alert', '');
  });

  runBtn.addEventListener('click', async () => {
    const code = srcEditor.value.trim();
    if (!code) { showToast('Paste some code to explain', 'info'); return; }
    setLoading(runBtn, true);
    hideResult('explain-result');
    showAlert('explain-alert', '');
    try {
      const data = await apiExplain(code, langSel.value);
      document.getElementById('expl-overview').textContent = data.overview || '—';
      document.getElementById('expl-detail').textContent = data.detailed_explanation || '—';
      document.getElementById('expl-algo').textContent = data.algorithm || '—';
      document.getElementById('expl-time').textContent = data.time_complexity || 'N/A';
      document.getElementById('expl-space').textContent = data.space_complexity || 'N/A';
      document.getElementById('expl-walkthrough').textContent = data.example_walkthrough || 'No walkthrough provided.';
      const listOrNone = (items, empty) => (items && items.length ? items.map((x) => `<li>${escHtml(x)}</li>`).join('') : `<li>${empty}</li>`);
      document.getElementById('expl-functions').innerHTML = listOrNone(data.functions_and_classes, 'None identified');
      document.getElementById('expl-vars').innerHTML = listOrNone(data.important_variables, 'None identified');
      document.getElementById('expl-issues').innerHTML = listOrNone(data.potential_issues, 'No issues identified');
      document.getElementById('expl-concepts').innerHTML = listOrNone(data.concepts_used, 'None listed');
      document.getElementById('expl-edges').innerHTML = listOrNone(data.edge_cases, 'None listed');
      showResult('explain-result');
      showToast('Explanation ready', 'success');
      loadDashboardActivity();
    } catch (e) {
      showAlert('explain-alert', e.message);
      showToast(e.message, 'error');
    } finally {
      setLoading(runBtn, false);
    }
  });
}

function paintAnalysis(data) {
  const score = data.overall_score ?? 0;
  lastAnalyzeScore = score;
  lastAnalyzeRecs = data.recommendations || [];
  animateScoreRing(score);
  const val = document.querySelector('.score-val');
  if (val) val.textContent = Math.round(score);
  document.getElementById('anlz-summary').textContent = data.summary || '—';
  document.getElementById('anlz-model').textContent = data.scoring_model
    ? `AI-generated analysis · ${data.scoring_model}`
    : 'AI-generated analysis · Deterministic weighted overall';

  const barsContainer = document.getElementById('quality-bars');
  barsContainer.innerHTML = '';
  (data.dimensions || []).forEach((dim, i) => {
    const s = dim.score ?? 0;
    const w = dim.weight != null ? ` · ${Math.round(dim.weight * 100)}%` : '';
    barsContainer.innerHTML += `
      <div class="quality-bar">
        <div class="quality-bar-header">
          <span class="bar-name">${escHtml(dim.name)}${w}</span>
          <span class="bar-score">${Math.round(s)}</span>
        </div>
        <div class="bar-track"><div class="bar-fill" id="bar-${i}" style="width:0%"></div></div>
        <div class="bar-desc">${escHtml(dim.description)}</div>
      </div>`;
  });
  setTimeout(() => {
    (data.dimensions || []).forEach((dim, i) => {
      const el = document.getElementById(`bar-${i}`);
      if (el) el.style.width = `${dim.score ?? 0}%`;
    });
  }, 200);

  const recList = document.getElementById('anlz-recs');
  recList.innerHTML = '';
  (data.recommendations || []).forEach((r, i) => {
    recList.innerHTML += `<div class="rec-item"><span class="rec-num">${i + 1}</span><span>${escHtml(r)}</span></div>`;
  });
  if (!data.recommendations || !data.recommendations.length) {
    recList.innerHTML = '<p class="empty-text">No recommendations.</p>';
  }
}

function initAnalyze() {
  const runBtn = document.getElementById('btn-analyze');
  const srcEditor = document.getElementById('anlz-code');
  const langSel = document.getElementById('sel-anlz-lang');
  const improveBtn = document.getElementById('btn-analyze-improve');
  bindDetect(document.getElementById('btn-anlz-detect'), srcEditor, langSel);

  document.getElementById('btn-anlz-reset').addEventListener('click', () => {
    srcEditor.value = '';
    hideResult('analyze-result');
    clearDiff('analyze-diff');
    showAlert('analyze-alert', '');
    document.getElementById('analyze-reanalyze-card').hidden = true;
  });

  runBtn.addEventListener('click', async () => {
    const code = srcEditor.value.trim();
    if (!code) { showToast('Paste some code to analyze', 'info'); return; }
    setLoading(runBtn, true);
    hideResult('analyze-result');
    showAlert('analyze-alert', '');
    clearDiff('analyze-diff');
    document.getElementById('analyze-reanalyze-card').hidden = true;
    try {
      const data = await apiAnalyze(code, langSel.value);
      paintAnalysis(data);
      showResult('analyze-result');
      showToast(`Quality score: ${Math.round(data.overall_score)}/100`, 'success');
      loadDashboardActivity();
    } catch (e) {
      showAlert('analyze-alert', e.message);
      showToast(e.message, 'error');
    } finally {
      setLoading(runBtn, false);
    }
  });

  improveBtn.addEventListener('click', async () => {
    const code = srcEditor.value.trim();
    if (!code) return;
    setLoading(improveBtn, true);
    showAlert('analyze-alert', '');
    try {
      const improved = await apiAnalyzeImprove(code, langSel.value, lastAnalyzeRecs);
      renderDiff('analyze-diff', code, improved.improved_code, {
        filename: `improved${getLangMeta(langSel.value).ext}`,
        onApply: (text) => { srcEditor.value = text; },
      });
      const before = lastAnalyzeScore;
      const reanalyzed = await apiAnalyze(improved.improved_code, langSel.value);
      paintAnalysis(reanalyzed);
      const card = document.getElementById('analyze-reanalyze-card');
      card.hidden = false;
      document.getElementById('anlz-before').textContent = before != null ? `${Math.round(before)}/100` : '—';
      document.getElementById('anlz-after').textContent = `${Math.round(reanalyzed.overall_score)}/100`;
      document.getElementById('anlz-after-summary').textContent = reanalyzed.summary || '';
      showToast('Improved code re-analyzed', 'success');
      loadDashboardActivity();
    } catch (e) {
      showAlert('analyze-alert', e.message);
      showToast(e.message, 'error');
    } finally {
      setLoading(improveBtn, false);
    }
  });
}

function syncFrameworks() {
  const lang = document.getElementById('sel-test-lang').value;
  const fwSel = document.getElementById('sel-test-fw');
  const options = FRAMEWORKS[lang] || ['standard'];
  fwSel.innerHTML = options.map((fw) => `<option value="${fw}">${fw}</option>`).join('');
}

function testBadgeLabel(type) {
  const map = {
    normal: 'Normal',
    edge: 'Edge',
    exception: 'Exception',
    security: 'Security',
    regression: 'Regression',
  };
  return map[type] || type;
}

function initTests() {
  const runBtn = document.getElementById('btn-gen-tests');
  const srcEditor = document.getElementById('test-code');
  const langSel = document.getElementById('sel-test-lang');
  const fwSel = document.getElementById('sel-test-fw');
  const fullTestOut = document.getElementById('full-test-out');
  syncFrameworks();
  langSel.addEventListener('change', syncFrameworks);
  bindDetect(document.getElementById('btn-test-detect'), srcEditor, langSel);
  langSel.addEventListener('change', syncFrameworks);

  document.getElementById('btn-test-reset').addEventListener('click', () => {
    srcEditor.value = '';
    hideResult('tests-result');
    showAlert('tests-alert', '');
  });

  runBtn.addEventListener('click', async () => {
    const code = srcEditor.value.trim();
    if (!code) { showToast('Paste some code to generate tests for', 'info'); return; }
    setLoading(runBtn, true);
    hideResult('tests-result');
    showAlert('tests-alert', '');
    try {
      const data = await apiGenerateTests(code, langSel.value, fwSel.value);
      document.getElementById('test-framework').textContent = data.test_framework || fwSel.value;
      document.getElementById('test-total').textContent = data.total_count ?? (data.test_cases || []).length;
      document.getElementById('badge-normal').textContent = `Normal ${data.normal_count ?? 0}`;
      document.getElementById('badge-edge').textContent = `Edge ${data.edge_count ?? 0}`;
      document.getElementById('badge-exception').textContent = `Exception ${data.exception_count ?? 0}`;
      document.getElementById('badge-security').textContent = `Security ${data.security_count ?? 0}`;
      document.getElementById('badge-regression').textContent = `Regression ${data.regression_count ?? 0}`;
      fullTestOut.textContent = data.test_code || '';

      const list = document.getElementById('test-list');
      list.innerHTML = '';
      (data.test_cases || []).forEach((tc) => {
        const type = (tc.test_type || (tc.is_edge_case ? 'edge' : 'normal')).toLowerCase();
        list.innerHTML += `
          <div class="test-item">
            <div class="test-header">
              <span class="test-badge ${escHtml(type)}">${escHtml(testBadgeLabel(type))}</span>
              <span class="test-name">${escHtml(tc.name)}</span>
              <span class="test-toggle">▼</span>
            </div>
            <div class="test-body">
              <p>${escHtml(tc.description)}</p>
              ${tc.expected_output ? `<p><strong>Expected:</strong> ${escHtml(tc.expected_output)}</p>` : ''}
              <pre class="test-code-block">${escHtml(tc.test_code)}</pre>
            </div>
          </div>`;
      });
      showResult('tests-result');
      showToast(`${(data.test_cases || []).length} test cases generated`, 'success');
      loadDashboardActivity();
    } catch (e) {
      showAlert('tests-alert', e.message);
      showToast(e.message, 'error');
    } finally {
      setLoading(runBtn, false);
    }
  });

  document.getElementById('btn-copy-tests').addEventListener('click', (e) => copyToClipboard(fullTestOut.textContent, e.currentTarget));
  document.getElementById('btn-dl-tests').addEventListener('click', () => {
    downloadText(fullTestOut.textContent, `tests${getLangMeta(langSel.value).ext}`);
  });
}

async function loadDashboardActivity() {
  const feed = document.getElementById('dash-activity');
  const ops = document.getElementById('dash-ops');
  if (!feed) return;
  try {
    const data = await apiGetHistory(8, 0);
    if (ops) ops.textContent = data.total ?? 0;
    if (!data.items || !data.items.length) {
      feed.innerHTML = `<div class="empty-state"><div class="empty-icon">📜</div><p class="empty-text">No activity yet. Run a tool to populate history.</p></div>`;
      return;
    }
    feed.innerHTML = data.items.map((item) => `
      <button class="activity-item" type="button" data-history-id="${item.id}">
        <span class="op-badge ${operationBadgeClass(item.operation)}">${escHtml(operationLabel(item.operation))}</span>
        <span class="activity-langs">${escHtml(item.source_language)}${item.target_language ? ' → ' + escHtml(item.target_language) : ''}</span>
        <span class="activity-time">${escHtml(formatTimestamp(item.created_at))}</span>
      </button>
    `).join('');
    feed.querySelectorAll('[data-history-id]').forEach((btn) => {
      btn.addEventListener('click', () => reopenHistoryItem(Number(btn.dataset.historyId)));
    });
  } catch (_) {
    /* dashboard should stay usable offline */
  }
}

async function loadHistory() {
  const body = document.getElementById('history-body');
  const op = document.getElementById('history-filter').value;
  const q = document.getElementById('history-search').value.trim();
  showAlert('history-alert', '');
  try {
    const data = await apiGetHistory(50, 0, op === 'all' ? null : op, null, q || null);
    if (!data.items || !data.items.length) {
      body.innerHTML = `<tr><td colspan="7"><div class="empty-state"><p class="empty-text">No matching history.</p></div></td></tr>`;
      return;
    }
    body.innerHTML = data.items.map((item) => `
      <tr>
        <td>${item.id}</td>
        <td><span class="op-badge ${operationBadgeClass(item.operation)}">${escHtml(operationLabel(item.operation))}</span></td>
        <td>${escHtml(item.source_language)}${item.target_language ? ' → ' + escHtml(item.target_language) : ''}</td>
        <td>${escHtml(item.status)}</td>
        <td>${item.quality_score != null ? Math.round(item.quality_score) : '—'}</td>
        <td>${escHtml(formatTimestamp(item.created_at))}</td>
        <td>
          <button class="btn btn-secondary btn-sm" data-reopen="${item.id}">Reopen in Tool</button>
          <button class="btn btn-ghost btn-sm" data-del="${item.id}">Delete</button>
        </td>
      </tr>
    `).join('');
    body.querySelectorAll('[data-reopen]').forEach((btn) => {
      btn.addEventListener('click', () => reopenHistoryItem(Number(btn.dataset.reopen)));
    });
    body.querySelectorAll('[data-del]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        try {
          await apiDeleteHistoryItem(Number(btn.dataset.del));
          loadHistory();
          loadDashboardActivity();
        } catch (e) {
          showAlert('history-alert', e.message);
        }
      });
    });
  } catch (e) {
    showAlert('history-alert', e.message);
  }
}

async function reopenHistoryItem(id) {
  try {
    const data = await apiGetHistoryItem(id);
    const item = data.item;
    const page = operationPage(item.operation);
    navigateTo(page);
    const map = {
      convert: { editor: 'src-code', lang: 'sel-src-lang', extra: () => {
        if (item.target_language) document.getElementById('sel-tgt-lang').value = item.target_language;
      }},
      debug: { editor: 'dbg-code', lang: 'sel-dbg-lang' },
      optimize: { editor: 'opt-code', lang: 'sel-opt-lang' },
      explain: { editor: 'expl-code', lang: 'sel-expl-lang' },
      analyze: { editor: 'anlz-code', lang: 'sel-anlz-lang' },
      tests: { editor: 'test-code', lang: 'sel-test-lang', extra: syncFrameworks },
    };
    const cfg = map[page];
    if (!cfg) return;
    document.getElementById(cfg.editor).value = item.source_code || '';
    if (item.source_language) document.getElementById(cfg.lang).value = item.source_language;
    if (cfg.extra) cfg.extra();
    showToast(`Restored ${operationLabel(item.operation)} #${item.id}`, 'success');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function initHistory() {
  document.getElementById('btn-history-refresh').addEventListener('click', loadHistory);
  document.getElementById('history-filter').addEventListener('change', loadHistory);
  let searchTimer;
  document.getElementById('history-search').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadHistory, 250);
  });
  document.getElementById('btn-history-clear').addEventListener('click', async () => {
    if (!confirm('Clear all history records?')) return;
    try {
      await apiClearHistory();
      loadHistory();
      loadDashboardActivity();
      showToast('History cleared', 'success');
    } catch (e) {
      showAlert('history-alert', e.message);
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initConvert();
  initDebug();
  initOptimize();
  initExplain();
  initAnalyze();
  initTests();
  initHistory();
  initCollapsibles('.bug-item', '.bug-header', '.bug-body');
  initCollapsibles('.test-item', '.test-header', '.test-body');
  checkHealth();
  loadDashboardActivity();
  setInterval(checkHealth, 30_000);
});
