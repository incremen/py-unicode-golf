const HIGHLIGHT_DELAY = 600;
const REPLACE_DELAY = 600;
const FINAL_DELAY = 600;
const SPEEDUP = 0.80;
const SPEEDUP_UNTIL = 350;

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
    let speed = 1;

    for (const step of data.steps) {
      while (vizPaused) await sleep(100);

      if (step.final) {
        resultExpr.innerHTML = syntaxHighlight(step.expr);
        await sleep(FINAL_DELAY);
        break;
      }

      const before = step.expr.substring(0, step.highlight.start);
      const highlight = step.expr.substring(step.highlight.start, step.highlight.end);
      const after = step.expr.substring(step.highlight.end);

      resultExpr.innerHTML = `${syntaxHighlight(before)}<span class="highlight">${syntaxHighlight(highlight)}</span>${syntaxHighlight(after)}`;
      await sleep(HIGHLIGHT_DELAY * speed);

      while (vizPaused) await sleep(100);

      resultExpr.innerHTML = `${syntaxHighlight(before)}<span class="fade-in">${syntaxHighlight(step.result)}</span>${syntaxHighlight(after)}`;
      await sleep(REPLACE_DELAY * speed);

      speed = Math.max(SPEEDUP_UNTIL / HIGHLIGHT_DELAY, speed * SPEEDUP);
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

