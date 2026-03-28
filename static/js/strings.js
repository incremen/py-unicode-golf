// strMode is read by visualize.js and main.js
let strMode = false;
let lastStrText = '';

function enterStringsPanel() {
  if (strMode) return;
  strMode = true;
  if (vizRunning) stopVisualization();
  charInput.value = '';
  lastExpr = '';
  lastData = null;
  result.classList.remove('visible');
  vizBtn().classList.remove('visible');
  charInput.removeAttribute('maxlength');
  charInput.classList.add('wide');
  charInput.size = 20;
  charInput.placeholder = 'type a string';
  charInput.focus();
}

function leaveStringsPanel() {
  if (!strMode) return;
  strMode = false;
  lastStrText = '';
  charInput.value = '';
  lastExpr = '';
  result.classList.remove('visible');
  vizBtn().classList.remove('visible');
  charInput.maxLength = 2;
  charInput.classList.add('wide');
  charInput.size = 11;
  charInput.placeholder = 'type here';
}

function showStringResult(data) {
  lastStrText = data.text;
  lastExpr = data.expr;
  resultChar.textContent = `"${data.text}"`;
  resultMeta.textContent = `${data.depth} calls \xb7 ${data.len} chars`;
  resultExpr.innerHTML = syntaxHighlight(data.expr);
  copiedMsg.textContent = '';
  result.classList.add('visible');
  vizBtn().classList.add('visible');
  vizBtn().classList.remove('hide-arrow');
}

function randomString() {
  logoPop();
  const len = 1 + Math.floor(Math.random() * 10);
  let s = '';
  for (let i = 0; i < len; i++) s += String.fromCodePoint(randomCodePoint());
  charInput.value = s;
  charInput.size = Math.min(40, Math.max(10, s.length + 2));
  charInput.dispatchEvent(new Event('input'));
}
