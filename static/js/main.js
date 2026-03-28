const charInput = document.getElementById('charInput');
const useDb = document.getElementById('useDb');
const dbToggle = document.getElementById('dbToggle');
const result = document.getElementById('result');
const resultChar = document.getElementById('resultChar');
const resultMeta = document.getElementById('resultMeta');
const resultExpr = document.getElementById('resultExpr');
const copiedMsg = document.getElementById('copiedMsg');

let lastExpr = '';
let lastData = null;

charInput.size = 9;

charInput.addEventListener('input', async () => {
  if (vizRunning) stopVisualization();
  const val = charInput.value;

  if (!val) {
    if (strMode) { charInput.size = 20; } else { charInput.classList.add('wide'); charInput.size = 11; }
    result.classList.remove('visible');
    vizBtn().classList.remove('visible');
    return;
  }

  if (strMode) {
    charInput.size = Math.min(40, Math.max(10, val.length + 2));
    try {
      const res = await fetch(`/api/string?s=${encodeURIComponent(val)}`);
      const data = await res.json();
      if (data.error) return;
      showStringResult(data);
    } catch (e) { console.error(e); }
    return;
  }

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
});

useDb.addEventListener('change', () => { if (lastData) showResult(lastData); });

function copyExpr() {
  navigator.clipboard.writeText(lastExpr);
  copiedMsg.textContent = 'copied';
  setTimeout(() => copiedMsg.textContent = '', 1500);
  resultExpr.classList.remove('copied-flash');
  void resultExpr.offsetWidth;
  resultExpr.classList.add('copied-flash');
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
  vizBtn().classList.add('visible');
  vizBtn().classList.remove('hide-arrow');
}

try { charInput.focus(); } catch (e) { /* ignore */ }
