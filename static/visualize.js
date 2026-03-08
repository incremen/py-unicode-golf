const HIGHLIGHT_DELAY = 600;
const REPLACE_DELAY = 600;
const FINAL_DELAY = 600;

async function visualize() {
  if (!lastExpr) return;

  try {
    const res = await fetch(`/api/visualize?expr=${encodeURIComponent(lastExpr)}`);
    const data = await res.json();

    if (data.error) {
      console.error(data.error);
      return;
    }

    resultExpr.style.cursor = 'default';

    for (const step of data.steps) {
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

      resultExpr.innerHTML = `${escapeHtml(before)}<span class="fade-in">${escapeHtml(step.result)}</span>${escapeHtml(after)}`;
      await sleep(REPLACE_DELAY);
    }

    resultExpr.style.cursor = 'pointer';
  } catch (e) {
    console.error(e);
    resultExpr.style.cursor = 'pointer';
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
