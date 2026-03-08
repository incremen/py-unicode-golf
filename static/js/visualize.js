const HIGHLIGHT_DELAY = 600;
const REPLACE_DELAY = 600;
const FINAL_DELAY = 600;

let vizPaused = false;
let vizRunning = false;

async function visualize() {
  if (!lastExpr) return;

  // Toggle pause if already running
  if (vizRunning) {
    vizPaused = !vizPaused;
    document.getElementById('visualizeBtn').textContent = vizPaused ? 'resume' : 'pause';
    return;
  }

  vizRunning = true;
  vizPaused = false;
  document.getElementById('visualizeBtn').textContent = 'pause';

  try {
    const res = await fetch(`/api/visualize?expr=${encodeURIComponent(lastExpr)}`);
    const data = await res.json();

    if (data.error) {
      console.error(data.error);
      vizRunning = false;
      document.getElementById('visualizeBtn').textContent = 'visualize';
      return;
    }

    resultExpr.style.cursor = 'default';

    for (const step of data.steps) {
      while (vizPaused) await sleep(100);

      if (step.final) {
        resultExpr.innerHTML = escapeHtml(step.expr);
        await sleep(FINAL_DELAY);
        break;
      }

      const before = step.expr.substring(0, step.highlight.start);
      const highlight = step.expr.substring(step.highlight.start, step.highlight.end);
      const after = step.expr.substring(step.highlight.end);

      resultExpr.innerHTML = `${escapeHtml(before)}<span class="highlight">${escapeHtml(highlight)}</span>${escapeHtml(after)}`;
      await sleep(HIGHLIGHT_DELAY);

      while (vizPaused) await sleep(100);

      resultExpr.innerHTML = `${escapeHtml(before)}<span class="fade-in">${escapeHtml(step.result)}</span>${escapeHtml(after)}`;
      await sleep(REPLACE_DELAY);
    }

    resultExpr.style.cursor = 'pointer';
  } catch (e) {
    console.error(e);
    resultExpr.style.cursor = 'pointer';
  }

  vizRunning = false;
  vizPaused = false;
  document.getElementById('visualizeBtn').textContent = 'visualize';
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
