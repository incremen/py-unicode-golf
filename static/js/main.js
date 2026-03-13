const charInput = document.getElementById('charInput');
const useDb = document.getElementById('useDb');
const dbToggle = document.getElementById('dbToggle');
const result = document.getElementById('result');
const resultChar = document.getElementById('resultChar');
const resultMeta = document.getElementById('resultMeta');
const resultExpr = document.getElementById('resultExpr');
const copiedMsg = document.getElementById('copiedMsg');
const shareBtn = document.getElementById('shareBtn');
const modeBtn = document.getElementById('modeBtn');

let lastExpr = '';
let lastData = null;
let stringMode = false;

charInput.size = 9;

function toggleMode() {
  if (vizRunning) stopVisualization();
  stringMode = !stringMode;
  modeBtn.textContent = stringMode ? 'char mode' : 'string mode';
  modeBtn.classList.toggle('active', stringMode);
  dbToggle.style.display = stringMode ? 'none' : '';
  charInput.value = '';
  lastExpr = '';
  lastData = null;
  result.classList.remove('visible');
  shareBtn.classList.remove('visible');
  history.replaceState(null, '', window.location.pathname);
  if (stringMode) {
    charInput.removeAttribute('maxlength');
    charInput.classList.add('wide');
    charInput.size = 20;
    charInput.placeholder = 'type a string';
  } else {
    charInput.maxLength = 2;
    charInput.classList.add('wide');
    charInput.size = 11;
    charInput.placeholder = 'type here';
  }
  charInput.focus();
}

charInput.addEventListener('input', async () => {
  if (vizRunning) stopVisualization();
  const val = charInput.value;

  if (!val) {
    if (stringMode) { charInput.size = 20; } else { charInput.classList.add('wide'); charInput.size = 11; }
    result.classList.remove('visible');
    shareBtn.classList.remove('visible');
    return;
  }

  if (stringMode) {
    charInput.size = Math.max(10, val.length + 2);
    try {
      const res = await fetch(`/api/string?s=${encodeURIComponent(val)}`);
      const data = await res.json();
      if (data.error) return;
      showStringResult(data);
    } catch (e) { console.error(e); }
  } else {
    const c = [...val].pop();
    charInput.value = c;
    charInput.classList.remove('wide');
    charInput.size = 1;
    try {
      const res = await fetch(`/api/char?c=${encodeURIComponent(c)}`);
      const data = await res.json();
      if (data.error) return;
      lastData = data;
      showResult(data);
    } catch (e) {
      console.error(e);
      resultChar.textContent = 'error';
      resultMeta.textContent = e.message;
      resultExpr.textContent = '';
      result.classList.add('visible');
    }
  }
});

useDb.addEventListener('change', () => { if (lastData && !stringMode) showResult(lastData); });

function copyExpr() {
  navigator.clipboard.writeText(lastExpr);
  copiedMsg.textContent = 'copied';
  setTimeout(() => copiedMsg.textContent = '', 1500);
}

function randomChar() {
  if (vizRunning) stopVisualization();
  logoPop();
  if (stringMode) {
    const len = 1 + Math.floor(Math.random() * 50);
    let s = '';
    for (let i = 0; i < len; i++) s += String.fromCodePoint(randomCodePoint());
    charInput.value = s;
    charInput.size = Math.max(10, s.length + 2);
    charInput.dispatchEvent(new Event('input'));
  } else {
    const cached = prefetchQueue.shift();
    if (cached) {
      charInput.value = cached.char;
      charInput.classList.remove('wide');
      charInput.size = 1;
      lastData = cached.data;
      showResult(cached.data);
      fillPrefetchQueue();
    } else {
      const cp = randomCodePoint();
      charInput.value = String.fromCodePoint(cp);
      charInput.dispatchEvent(new Event('input'));
    }
  }
}

function showResult(data) {
  const useOptimized = useDb.checked && data.db;
  const src = useOptimized ? data.db : data.formula;
  const label = useOptimized ? 'db' : 'algorithm';
  const hex = 'U+' + data.code_point.toString(16).toUpperCase().padStart(4, '0');
  const name = data.name ? `  \xb7  ${data.name}` : '';
  resultChar.textContent = `'${data.char}' \u2014 ${hex}${name}`;
  resultMeta.textContent = `${src.depth} calls \xb7 ${src.len} chars \xb7 ${label}`;
  resultExpr.innerHTML = syntaxHighlight(src.expr);
  lastExpr = src.expr;
  copiedMsg.textContent = '';
  result.classList.add('visible');
  shareBtn.classList.add('visible');
  shareBtn.classList.remove('copied');
  shareBtn.innerHTML = `share <span class="share-char">${escapeHtml(data.char)}</span>`;
  history.replaceState(null, '', `?c=${encodeURIComponent(data.char)}`);
}

function showStringResult(data) {
  resultChar.textContent = `"${data.text}"`;
  resultMeta.textContent = `${data.depth} calls \xb7 ${data.len} chars`;
  resultExpr.innerHTML = syntaxHighlight(data.expr);
  lastExpr = data.expr;
  copiedMsg.textContent = '';
  result.classList.add('visible');
  shareBtn.classList.add('visible');
  shareBtn.classList.remove('copied');
  shareBtn.innerHTML = `share <span class="share-char">${escapeHtml(data.text)}</span>`;
  history.replaceState(null, '', `?s=${encodeURIComponent(data.text)}`);
}

let shareResetTimer = null;
function shareChar() {
  const url = window.location.href;
  navigator.clipboard.writeText(url);
  clearTimeout(shareResetTimer);
  shareBtn.classList.add('copied');
  shareBtn.textContent = 'copied!';
}

// Auto-load from URL params
(function loadFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const c = params.get('c');
  const s = params.get('s');
  if (s) {
    setTimeout(() => {
      stringMode = true;
      modeBtn.textContent = 'char mode';
      modeBtn.classList.add('active');
      dbToggle.style.display = 'none';
      charInput.removeAttribute('maxlength');
      charInput.placeholder = 'type a string';
      charInput.value = s;
      charInput.classList.add('wide');
      charInput.size = Math.max(10, s.length + 2);
      fetch(`/api/string?s=${encodeURIComponent(s)}`)
        .then(r => r.json())
        .then(data => { if (!data.error) showStringResult(data); });
    }, 0);
  } else if (c) {
    setTimeout(() => {
      charInput.value = c;
      charInput.classList.remove('wide');
      charInput.size = 1;
      fetch(`/api/char?c=${encodeURIComponent(c)}`)
        .then(r => r.json())
        .then(data => { if (!data.error) { lastData = data; showResult(data); } });
    }, 0);
  }
})();

try { charInput.focus(); } catch (e) { /* ignore */ }
