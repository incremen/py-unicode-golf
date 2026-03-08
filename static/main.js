const charInput = document.getElementById('charInput');
const useDb = document.getElementById('useDb');
const result = document.getElementById('result');
const resultChar = document.getElementById('resultChar');
const resultMeta = document.getElementById('resultMeta');
const resultExpr = document.getElementById('resultExpr');
const copiedMsg = document.getElementById('copiedMsg');

let lastExpr = '';
let lastData = null;

charInput.size = 9; // fit the placeholder

charInput.addEventListener('input', async () => {
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

function showMain(btn, id) {
  const wasActive = document.getElementById(id).classList.contains('active');
  document.querySelectorAll('.main-panel').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.main-tab').forEach(el => el.classList.remove('active'));
  if (!wasActive) {
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
  }
}

function randomChar() {
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

function loadStrategies() {
  document.getElementById('strategiesList').innerHTML = STRATEGY_BREAKDOWN.map(st =>
    `<span class="strategy-tag tip">${st.name} <span class="count">${st.count.toLocaleString()}</span>` +
    `<span class="tiptext">${st.count.toLocaleString()} numbers use ${st.name} (avg depth ${st.avg_depth})</span></span>`
  ).join('');
}

function loadHistory() {
  document.getElementById('historyBody').innerHTML = OPTIMIZATION_HISTORY.map(e => `
    <tr>
      <td>${e.label}</td>
      <td class="num">${e.avg_depth}</td>
      <td class="num">${e.max_depth}</td>
      <td class="num">${e.avg_len.toLocaleString()}</td>
    </tr>
  `).join('');
}

function loadDbStats() {
  document.getElementById('dTotal').textContent = DB_STATS.total.toLocaleString();
  document.getElementById('dAvgDepth').textContent = DB_STATS.avg_depth;
  document.getElementById('dMaxDepth').textContent = DB_STATS.max_depth;
  document.getElementById('dAvgLen').textContent = DB_STATS.avg_len;
}

function loadFormulaStats() {
  document.getElementById('fAvgDepth').textContent = FORMULA_STATS.avg_depth;
  document.getElementById('fMaxDepth').textContent = FORMULA_STATS.max_depth;
  document.getElementById('fAvgLen').textContent = FORMULA_STATS.avg_len;
  document.getElementById('fMaxLen').textContent = FORMULA_STATS.max_len;
}

function showResult(data) {
  const useOptimized = useDb.checked && data.db;
  const src = useOptimized ? data.db : data.formula;
  const label = useOptimized ? 'db' : 'algorithm';
  resultChar.textContent = `'${data.char}' \u2014 U+${data.code_point.toString(16).toUpperCase().padStart(4, '0')}`;
  resultMeta.textContent = `${src.depth} calls \xb7 ${src.len} chars \xb7 ${label}`;
  resultExpr.textContent = src.expr;
  lastExpr = src.expr;
  copiedMsg.textContent = '';
  result.classList.add('visible');
}

loadHistory();
loadStrategies();
loadDbStats();
loadFormulaStats();
try { charInput.focus(); } catch (e) { /* ignore */ }
