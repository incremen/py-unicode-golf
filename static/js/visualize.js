const HIGHLIGHT_DELAY = 600;
const REPLACE_DELAY = 600;
const FINAL_DELAY = 600;
const SPEEDUP = 0.80;
const SPEEDUP_UNTIL = 310;

let vizPaused = false;
let vizRunning = false;
let vizCancelled = false;

const vizBtn = () => document.getElementById('visualizeBtn');
const stepCounter = document.getElementById('stepCounter');

function stopVisualization() {
  vizCancelled = true;
  vizPaused = false;
  vizRunning = false;
  vizBtn().textContent = 'visualize';
  stepCounter.textContent = '';
  stepCounter.classList.remove('active', 'bump');
  resultExpr.style.cursor = 'pointer';
  logoReset();
}

async function waitAndCheck(ms) {
  await sleep(ms);
  if (vizCancelled) return false;
  while (vizPaused && !vizCancelled) await sleep(100);
  return !vizCancelled;
}

function renderStep(before, middle, after, className) {
  resultExpr.innerHTML =
    `${syntaxHighlight(before)}<span class="${className}">${syntaxHighlight(middle)}</span>${syntaxHighlight(after)}`;
}

async function fetchSteps(expr) {
  const res = await fetch(`/api/visualize?expr=${encodeURIComponent(expr)}`);
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data.steps;
}

function estimateDuration(totalSteps) {
  let speed = 1;
  let ms = 0;
  for (let i = 0; i < totalSteps; i++) {
    ms += (HIGHLIGHT_DELAY + REPLACE_DELAY) * speed;
    speed = Math.max(SPEEDUP_UNTIL / HIGHLIGHT_DELAY, speed * SPEEDUP);
  }
  return ms / 1000;
}

async function animateSteps(steps) {
  resultExpr.style.cursor = 'default';
  const total = steps.filter(s => !s.final).length;
  logoStart(total, estimateDuration(total));
  let current = 0;
  let speed = 1;

  for (const step of steps) {
    if (vizCancelled) break;

    if (step.final) {
      stepCounter.classList.remove('active', 'bump');
      stepCounter.textContent = '';
      resultExpr.innerHTML = syntaxHighlight(step.expr);
      await sleep(FINAL_DELAY);
      break;
    }

    current++;

    const before = step.expr.substring(0, step.highlight.start);
    const highlighted = step.expr.substring(step.highlight.start, step.highlight.end);
    const after = step.expr.substring(step.highlight.end);

    renderStep(before, highlighted, after, 'highlight');
    if (!await waitAndCheck(HIGHLIGHT_DELAY * speed)) break;

    renderStep(before, step.result, after, 'fade-in');
    stepCounter.textContent = `${current}/${total}`;
    stepCounter.classList.add('active');
    stepCounter.classList.add('bump');
    setTimeout(() => stepCounter.classList.remove('bump'), 150);
    if (!await waitAndCheck(REPLACE_DELAY * speed)) break;

    speed = Math.max(SPEEDUP_UNTIL / HIGHLIGHT_DELAY, speed * SPEEDUP);
  }
}

async function visualize() {
  if (!lastExpr) return;

  if (vizRunning) {
    vizPaused = !vizPaused;
    vizBtn().textContent = vizPaused ? 'resume' : 'pause';
    if (vizPaused) logoPause(); else logoResume();
    return;
  }

  vizRunning = true;
  vizPaused = false;
  vizCancelled = false;
  vizBtn().textContent = 'pause';

  try {
    const steps = await fetchSteps(lastExpr);
    if (!vizCancelled) await animateSteps(steps);
  } catch (e) {
    console.error(e);
  }

  logoDelayedReset();
  stopVisualization();
}

