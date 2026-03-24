const EXAMPLES = {
  calculator: `import tkinter as tk
root = tk.Tk()
root.title("Calculator")
expr = tk.StringVar()
tk.Entry(root, textvariable=expr, font=("Helvetica", 20), justify="right", bd=8).grid(row=0, column=0, columnspan=4)
def press(val):
    expr.set(expr.get() + val)
def clear():
    expr.set("")
def evaluate():
    try: expr.set(str(eval(expr.get())))
    except: expr.set("Error")
btns = ["7","8","9","/","4","5","6","*","1","2","3","-","0",".","=","+"]
for i,b in enumerate(btns):
    cmd = evaluate if b=="=" else lambda v=b: press(v)
    tk.Button(root, text=b, font=("Helvetica", 16), width=4, height=2, command=cmd).grid(row=1+i//4, column=i%4)
tk.Button(root, text="C", font=("Helvetica", 16), width=4, height=2, command=clear).grid(row=5, column=0, columnspan=4)
root.mainloop()`,

  gui: `import tkinter as tk
root = tk.Tk()
root.title("py-unicode-golf")
tk.Label(root, text="Payload Executed.", font=("Helvetica", 24)).pack(padx=50, pady=50)
root.mainloop()`,

  redirect: `import webbrowser
webbrowser.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ')`,

  image: `import os, webbrowser
html = '<img src="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==">'
with open('img.html', 'w') as f:
    f.write(html)
webbrowser.open('file://' + os.path.realpath('img.html'))`,
};

const codeInput = document.getElementById('codeInput');
const codeByteCount = document.getElementById('codeByteCount');
const codeResult = document.getElementById('codeResult');
const codeResultMeta = document.getElementById('codeResultMeta');
const codeResultExpr = document.getElementById('codeResultExpr');
const codeResultCopied = document.getElementById('codeResultCopied');

let lastCodeExpr = '';
let activeExample = null;

function loadExample(name) {
  codeInput.value = EXAMPLES[name];
  activeExample = name;
  document.querySelectorAll('.code-example-btn').forEach(b => {
    b.classList.toggle('active', b.getAttribute('onclick') === `loadExample('${name}')`);
  });
  updateByteCount();
  codeResult.classList.remove('visible');
}

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
