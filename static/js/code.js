const codeInput       = document.getElementById('codeInput');
const codeByteCount   = document.getElementById('codeByteCount');
const codeResult      = document.getElementById('codeResult');
const codeResultMeta  = document.getElementById('codeResultMeta');
const codeResultExpr  = document.getElementById('codeResultExpr');
const codeResultCopied = document.getElementById('codeResultCopied');
const codeExamples    = document.getElementById('codeExamples');
const compileBtn      = document.querySelector('.code-compile-btn');

let lastCodeExpr = '';

async function loadExample(name) {
  const res = await fetch(`/static/examples/${name}.py`);
  codeInput.value = await res.text();
  document.querySelectorAll('.code-example-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.name === name);
  });
  updateByteCount();
  codeResult.classList.remove('visible');
}

async function initExamples() {
  const res = await fetch('/static/examples/manifest.json');
  const examples = await res.json();
  for (const { name, label } of examples) {
    const btn = document.createElement('button');
    btn.className = 'code-example-btn';
    btn.dataset.name = name;
    btn.textContent = label;
    btn.addEventListener('click', () => loadExample(name));
    codeExamples.appendChild(btn);
  }
}

initExamples();

function updateByteCount() {
  const bytes = new TextEncoder().encode(codeInput.value).length;
  codeByteCount.textContent = bytes ? `${bytes} bytes` : '';
}

codeInput.addEventListener('input', () => {
  document.querySelectorAll('.code-example-btn').forEach(b => b.classList.remove('active'));
  updateByteCount();
});

codeInput.addEventListener('keydown', e => {
  if (e.key !== 'Tab') return;
  e.preventDefault();
  const start = codeInput.selectionStart;
  const end = codeInput.selectionEnd;
  codeInput.value = codeInput.value.slice(0, start) + '    ' + codeInput.value.slice(end);
  codeInput.selectionStart = codeInput.selectionEnd = start + 4;
});

async function compileCode() {
  const code = codeInput.value.trim();
  if (!code) return;

  compileBtn.textContent = 'compiling…';
  compileBtn.disabled = true;

  try {
    const res = await fetch(`/api/code?code=${encodeURIComponent(code)}`);
    const data = await res.json();
    if (data.error) {
      codeResultMeta.textContent = `error: ${data.error}`;
      codeResultExpr.innerHTML = '';
      lastCodeExpr = '';
    } else {
      lastCodeExpr = data.expr;
      codeResultMeta.textContent = `${data.bytes} bytes → ${data.len.toLocaleString()} chars`;
      codeResultExpr.innerHTML = syntaxHighlight(data.expr);
      codeResultCopied.textContent = '';
    }
    codeResult.classList.add('visible');
    expandTopWrap();
  } catch (e) {
    codeResultMeta.textContent = `error: ${e.message}`;
    codeResult.classList.add('visible');
    expandTopWrap();
  } finally {
    compileBtn.textContent = 'compile →';
    compileBtn.disabled = false;
  }
}

function copyCodeExpr() {
  if (!lastCodeExpr) return;
  flashCopy(lastCodeExpr, codeResultCopied, codeResultExpr);
}
