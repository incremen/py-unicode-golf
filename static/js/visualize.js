const HIGHLIGHT_DELAY = 600;
const REPLACE_DELAY = 600;
const FINAL_DELAY = 600;
const SPEEDUP = 0.80;
const SPEEDUP_UNTIL = 310;
const STRING_STEP_DELAY = 1200;

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
  logoCancel();
}

async function waitAndCheck(ms) {
  await sleep(ms);
  if (vizCancelled) return false;
  while (vizPaused && !vizCancelled) await sleep(100);
  return !vizCancelled;
}

function renderStep(before, middle, after, className) {
  resultExpr.innerHTML =
    `${escapeHtml(before)}<span class="${className}">${syntaxHighlight(middle)}</span>${escapeHtml(after)}`;
}

function estimateDuration(total) {
  let speed = 1, ms = 0;
  for (let i = 0; i < total; i++) {
    ms += (HIGHLIGHT_DELAY + REPLACE_DELAY) * speed;
    speed = Math.max(SPEEDUP_UNTIL / HIGHLIGHT_DELAY, speed * SPEEDUP);
  }
  return ms / 1000;
}

// ── Single-char visualization (original) ────────────────────────────

async function animateSteps(steps) {
  resultExpr.style.cursor = 'default';
  const total = steps.filter(s => !s.final).length;
  logoStart(total, estimateDuration(total));
  let current = 0, speed = 1;

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
    stepCounter.classList.add('active', 'bump');
    setTimeout(() => stepCounter.classList.remove('bump'), 150);
    if (!await waitAndCheck(REPLACE_DELAY * speed)) break;

    speed = Math.max(SPEEDUP_UNTIL / HIGHLIGHT_DELAY, speed * SPEEDUP);
  }
}

// ── String visualization (parallel per-character) ───────────────────

function getTrackExpr(track, pos, mode) {
  const step = track.steps[pos];
  const done = !step || step.final;

  if (done) {
    const finalStep = track.steps[track.steps.length - 1];
    return syntaxHighlight(finalStep.expr);
  }
  if (step.highlight) {
    const before = step.expr.substring(0, step.highlight.start);
    const mid = step.expr.substring(step.highlight.start, step.highlight.end);
    const after = step.expr.substring(step.highlight.end);
    if (mode === 'highlight') {
      return `${escapeHtml(before)}<span class="highlight">${syntaxHighlight(mid)}</span>${escapeHtml(after)}`;
    }
    return `${escapeHtml(before)}<span class="fade-in">${syntaxHighlight(step.result)}</span>${escapeHtml(after)}`;
  }
  return escapeHtml(step.expr);
}

function renderStringState(tracks, positions, mode) {
  let rows = '<div class="string-viz-header">' +
    syntaxHighlight('eval') + '(' +
    syntaxHighlight('bytes') + '(' +
    syntaxHighlight('map') + '(' +
    syntaxHighlight('ord') + ', ' +
    syntaxHighlight('next') + '(' +
    syntaxHighlight('zip') + '(</div>';
  rows += '<div class="string-viz-tracks">';

  for (let i = 0; i < tracks.length; i++) {
    const step = tracks[i].steps[positions[i]];
    const done = !step || step.final;
    const label = escapeHtml(tracks[i].label);
    const comma = i < tracks.length - 1 ? '<span class="string-viz-comma">,</span>' : '';

    rows += `<div class="string-viz-row${done ? ' done' : ''}">`;
    rows += `<span class="string-viz-label">${label}</span>`;
    rows += `<span class="string-viz-expr">${getTrackExpr(tracks[i], positions[i], mode)}${comma}</span>`;
    rows += '</div>';
  }

  rows += '</div>';
  rows += '<div class="string-viz-footer">)))))) </div>';
  resultExpr.innerHTML = rows;
}

async function animateStringTracks(data) {
  resultExpr.style.cursor = 'default';
  const tracks = data.tracks;
  const maxSteps = Math.max(...tracks.map(t => t.steps.filter(s => !s.final).length));
  const positions = tracks.map(() => 0);
  let level = 0;

  logoStart(maxSteps, maxSteps * STRING_STEP_DELAY / 1000);

  while (true) {
    if (vizCancelled) break;

    const allDone = positions.every((pos, i) => {
      const step = tracks[i].steps[pos];
      return !step || step.final;
    });
    if (allDone) break;

    level++;

    // Phase 1: highlight
    renderStringState(tracks, positions, 'highlight');
    stepCounter.textContent = `${level}`;
    stepCounter.classList.add('active', 'bump');
    setTimeout(() => stepCounter.classList.remove('bump'), 150);
    if (!await waitAndCheck(STRING_STEP_DELAY / 2)) break;

    // Phase 2: replace
    renderStringState(tracks, positions, 'replace');
    if (!await waitAndCheck(STRING_STEP_DELAY / 2)) break;

    // Advance all non-final tracks
    for (let i = 0; i < tracks.length; i++) {
      const step = tracks[i].steps[positions[i]];
      if (step && !step.final) positions[i]++;
    }
  }

  if (!vizCancelled) {
    // Assemble final full expression
    const finalExprs = tracks.map(t => {
      const last = t.steps[t.steps.length - 1];
      return last.expr;
    });
    const fullExpr = `eval(bytes(map(ord,next(zip(${finalExprs.join(',')})))))`;
    resultExpr.innerHTML = syntaxHighlight(fullExpr);
    stepCounter.classList.remove('active', 'bump');
    stepCounter.textContent = '';
    await sleep(FINAL_DELAY);
  }
}

// ── Main entry point ────────────────────────────────────────────────

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
    if (stringMode) {
      const text = charInput.value;
      const res = await fetch(`/api/visualize_string?s=${encodeURIComponent(text)}`);
      const data = await res.json();
      if (!data.error && !vizCancelled) await animateStringTracks(data);
    } else {
      const steps = await fetchSteps(lastExpr);
      if (!vizCancelled) await animateSteps(steps);
    }
  } catch (e) {
    console.error(e);
  }

  logoDelayedReset();
  stopVisualization();
}

async function fetchSteps(expr) {
  const res = await fetch(`/api/visualize?expr=${encodeURIComponent(expr)}`);
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data.steps;
}
