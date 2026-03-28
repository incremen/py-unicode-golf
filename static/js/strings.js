const strInput      = document.getElementById('strInput');
const strResult     = document.getElementById('strResult');
const strResultMeta = document.getElementById('strResultMeta');
const strResultExpr = document.getElementById('strResultExpr');
const strCopied     = document.getElementById('strCopied');

// Read by visualize.js to know which mode to run
let strMode = false;
let lastStrText = '';

strInput.addEventListener('input', async () => {
  if (vizRunning) stopVisualization();
  const val = strInput.value;
  if (!val) {
    strResult.classList.remove('visible');
    return;
  }
  try {
    const res = await fetch(`/api/string?s=${encodeURIComponent(val)}`);
    const data = await res.json();
    if (data.error) return;
    showStringResult(data);
  } catch (e) { console.error(e); }
});

function showStringResult(data) {
  lastStrText = data.text;
  lastExpr = data.expr;   // shared with visualize.js
  strResultMeta.textContent = `${data.depth} calls \xb7 ${data.len} chars`;
  strResultExpr.innerHTML = syntaxHighlight(data.expr);
  strCopied.textContent = '';
  strResult.classList.add('visible');
}

function copyStrExpr() {
  if (!lastExpr) return;
  navigator.clipboard.writeText(lastExpr);
  strCopied.textContent = 'copied';
  setTimeout(() => strCopied.textContent = '', 1500);
  strResultExpr.classList.remove('copied-flash');
  void strResultExpr.offsetWidth;
  strResultExpr.classList.add('copied-flash');
}

function randomString() {
  logoPop();
  const len = 1 + Math.floor(Math.random() * 10);
  let s = '';
  for (let i = 0; i < len; i++) s += String.fromCodePoint(randomCodePoint());
  strInput.value = s;
  strInput.dispatchEvent(new Event('input'));
}

function enterStringsPanel() {
  strMode = true;
  if (vizRunning) stopVisualization();
  // reset char state
  charInput.value = '';
  charInput.classList.add('wide');
  charInput.size = 11;
  lastData = null;
  lastExpr = '';
  result.classList.remove('visible');
  vizBtn().classList.remove('visible');
}

function leaveStringsPanel() {
  strMode = false;
  lastStrText = '';
  lastExpr = '';
  strInput.value = '';
  strResult.classList.remove('visible');
}
