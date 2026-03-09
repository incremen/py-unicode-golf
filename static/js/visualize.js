const HIGHLIGHT_DELAY = 600;
const REPLACE_DELAY = 600;
const FINAL_DELAY = 600;
const SPEEDUP = 0.80;
const SPEEDUP_UNTIL = 310;

let vizPaused = false;
let vizRunning = false;
let vizCancelled = false;

function stopVisualization() {
  vizCancelled = true;
  vizPaused = false;
  vizRunning = false;
  document.getElementById('visualizeBtn').textContent = 'visualize';
  resultExpr.style.cursor = 'pointer';
}

async function visualize() {
  if (!lastExpr) return;

  if (vizRunning) {
    vizPaused = !vizPaused;
    document.getElementById('visualizeBtn').textContent = vizPaused ? 'resume' : 'pause';
    return;
  }

  vizRunning = true;
  vizPaused = false;
  vizCancelled = false;
  document.getElementById('visualizeBtn').textContent = 'pause';

  try {
    const res = await fetch(`/api/visualize?expr=${encodeURIComponent(lastExpr)}`);
    const data = await res.json();

    if (data.error || vizCancelled) {
      if (data.error) console.error(data.error);
      stopVisualization();
      return;
    }

    resultExpr.style.cursor = 'default';
    let speed = 1;

    for (const step of data.steps) {
      if (vizCancelled) break;
      while (vizPaused && !vizCancelled) await sleep(100);
      if (vizCancelled) break;

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

      if (vizCancelled) break;
      while (vizPaused && !vizCancelled) await sleep(100);
      if (vizCancelled) break;

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
  vizCancelled = false;
  document.getElementById('visualizeBtn').textContent = 'visualize';
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
