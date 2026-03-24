const codeInput = document.getElementById('codeInput');
const codeByteCount = document.getElementById('codeByteCount');
const codeResult = document.getElementById('codeResult');
const codeResultMeta = document.getElementById('codeResultMeta');
const codeResultExpr = document.getElementById('codeResultExpr');
const codeResultCopied = document.getElementById('codeResultCopied');
const codeExamplesContainer = document.getElementById('codeExamples');

let lastCodeExpr = '';
let activeExample = null;

async function loadExample(name) {
  const res = await fetch(`/static/examples/${name}.py`);
  codeInput.value = await res.text();
  activeExample = name;
  document.querySelectorAll('.code-example-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.name === name);
  });
  updateByteCount();
  codeResult.classList.remove('visible');
}

async function initExamples() {
  const res = await fetch('/static/examples/manifest.json');
  const examples = await res.json();
  codeExamplesContainer.innerHTML = '';
  for (const { name, label } of examples) {
    const btn = document.createElement('button');
    btn.className = 'code-example-btn';
    btn.dataset.name = name;
    btn.textContent = label;
    btn.addEventListener('click', () => loadExample(name));
    codeExamplesContainer.appendChild(btn);
  }
}

initExamples();

function updateByteCount() {
  const bytes = new TextEncoder().encode(codeInput.value).length;
  codeByteCount.textContent = bytes ? `${bytes} bytes` : '';
}

codeInput.addEventListener('input', () => {
  activeExample = null;
  document.querySelectorAll('.code-example-btn').forEach(b => b.classList.remove('active'));
  updateByteCount();
});

codeInput.addEventListener('keydown', e => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const start = codeInput.selectionStart;
    const end = codeInput.selectionEnd;
    codeInput.value = codeInput.value.slice(0, start) + '    ' + codeInput.value.slice(end);
    codeInput.selectionStart = codeInput.selectionEnd = start + 4;
  }
});

async function compileCode() {
  const code = codeInput.value.trim();
  if (!code) return;

  const btn = document.querySelector('.code-compile-btn');
  btn.textContent = 'compiling…';
  btn.disabled = true;

  try {
    const res = await fetch(`/api/code?code=${encodeURIComponent(code)}`);
    const data = await res.json();
    if (data.error) {
      codeResultMeta.textContent = `error: ${data.error}`;
      codeResultExpr.innerHTML = '';
      lastCodeExpr = '';
      codeResult.classList.add('visible');
      return;
    }
    lastCodeExpr = data.expr;
    codeResultMeta.textContent = `${data.bytes} bytes → ${data.len.toLocaleString()} chars`;
    codeResultExpr.innerHTML = escapeHtml(data.expr);
    codeResultCopied.textContent = '';
    codeResult.classList.add('visible');
  } catch (e) {
    codeResultMeta.textContent = `error: ${e.message}`;
    codeResult.classList.add('visible');
  } finally {
    btn.textContent = 'compile →';
    btn.disabled = false;
  }
}

function copyCodeExpr() {
  if (!lastCodeExpr) return;
  navigator.clipboard.writeText(lastCodeExpr);
  codeResultCopied.textContent = 'copied';
  setTimeout(() => codeResultCopied.textContent = '', 1500);
}
