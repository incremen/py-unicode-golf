const charInput = document.getElementById('charInput');
const useDb = document.getElementById('useDb');
const result = document.getElementById('result');
const resultChar = document.getElementById('resultChar');
const resultMeta = document.getElementById('resultMeta');
const resultExpr = document.getElementById('resultExpr');
const copiedMsg = document.getElementById('copiedMsg');
const shareBtn = document.getElementById('shareBtn');

let lastExpr = '';
let lastData = null;

charInput.size = 9; // fit the placeholder

charInput.addEventListener('input', async () => {
  if (vizRunning) stopVisualization();
  const char = charInput.value;
  // when empty, show the wider placeholder state; collapse to single-char size when there's input
  if (!char || char.length === 0) { charInput.classList.add('wide'); charInput.size = 11; result.classList.remove('visible'); return; }
  const c = [...char].pop();
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
});

useDb.addEventListener('change', () => { if (lastData) showResult(lastData); });

function copyExpr() {
  navigator.clipboard.writeText(lastExpr);
  copiedMsg.textContent = 'copied';
  setTimeout(() => copiedMsg.textContent = '', 1500);
}

function randomChar() {
  if (vizRunning) stopVisualization();
  logoPop();
  const cached = prefetchQueue.shift();
  if (cached) {
    charInput.value = cached.char;
    charInput.classList.remove('wide');
    charInput.size = 1;
    lastData = cached.data;
    showResult(cached.data);
    fillPrefetchQueue();
  } else {
    // fallback: fetch live
    const cp = randomCodePoint();
    charInput.value = String.fromCodePoint(cp);
    charInput.dispatchEvent(new Event('input'));
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

let shareResetTimer = null;
function shareChar() {
  const url = window.location.href;
  navigator.clipboard.writeText(url);
  clearTimeout(shareResetTimer);
  shareBtn.classList.add('copied');
  shareBtn.textContent = 'copied!';
}

// Auto-load character from ?c= URL param
(function loadFromUrl() {
  const c = new URLSearchParams(window.location.search).get('c');
  if (!c) return;
  setTimeout(() => {
    charInput.value = c;
    charInput.classList.remove('wide');
    charInput.size = 1;
    fetch(`/api/char?c=${encodeURIComponent(c)}`)
      .then(r => r.json())
      .then(data => {
        if (data.error) return;
        lastData = data;
        showResult(data);
      });
  }, 0);
})();

try { charInput.focus(); } catch (e) { /* ignore */ }
