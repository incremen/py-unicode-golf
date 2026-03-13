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
    `${syntaxHighlight(before)}<span class="${className}">${syntaxHighlight(middle)}</span>${syntaxHighlight(after)}`;
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
      return `${syntaxHighlight(before)}<span class="highlight">${syntaxHighlight(mid)}</span>${syntaxHighlight(after)}`;
    }
    return `${syntaxHighlight(before)}<span class="fade-in">${syntaxHighlight(step.result)}</span>${syntaxHighlight(after)}`;
  }
  return syntaxHighlight(step.expr);
}

const WRAPPER_OPEN = syntaxHighlight('eval(bytes(next(zip(');
const WRAPPER_CLOSE = syntaxHighlight('))))');
const SYN_COMMA = '<span class="syn-paren">,</span>';

function renderStringUnfold(tracks, splitAt) {
  // Show the expression with newlines inserted up to splitAt index
  let html = WRAPPER_OPEN;
  for (let i = 0; i < tracks.length; i++) {
    if (i > 0) html += SYN_COMMA;
    if (i < splitAt) html += '\n  ';
    html += syntaxHighlight(tracks[i].expr);
  }
  if (splitAt > 0) html += '\n';
  html += WRAPPER_CLOSE;
  resultExpr.innerHTML = html;
}

function renderStringState(tracks, positions, mode) {
  let html = WRAPPER_OPEN + '\n';
  for (let i = 0; i < tracks.length; i++) {
    const comma = i < tracks.length - 1 ? SYN_COMMA : '';
    html += '  ' + getTrackExpr(tracks[i], positions[i], mode) + comma + '\n';
  }
  html += WRAPPER_CLOSE;
  resultExpr.innerHTML = html;
}

async function animateStringTracks(data) {
  resultExpr.style.cursor = 'default';
  const tracks = data.tracks;
  const maxSteps = Math.max(...tracks.map(t => t.steps.filter(s => !s.final).length));
  const positions = tracks.map(() => 0);
  let level = 0;
  const totalSteps = maxSteps + 4; // parallel steps + 4 end steps

  // ── Intro: unfold one line at a time ──
  renderStringUnfold(tracks, 0);
  if (!await waitAndCheck(400)) return;
  for (let i = 1; i <= tracks.length; i++) {
    if (vizCancelled) return;
    renderStringUnfold(tracks, i);
    if (!await waitAndCheck(Math.max(60, 300 - i * 15))) return;
  }
  if (!await waitAndCheck(300)) return;

  // ── Main: parallel step-by-step ──
  logoStart(maxSteps, maxSteps * STRING_STEP_DELAY / 1000);

  while (true) {
    if (vizCancelled) break;

    const allDone = positions.every((pos, i) => {
      const step = tracks[i].steps[pos];
      return !step || step.final;
    });
    if (allDone) break;

    level++;

    renderStringState(tracks, positions, 'highlight');
    stepCounter.textContent = `${level}/${totalSteps}`;
    stepCounter.classList.add('active', 'bump');
    setTimeout(() => stepCounter.classList.remove('bump'), 150);
    if (!await waitAndCheck(STRING_STEP_DELAY / 2)) break;

    renderStringState(tracks, positions, 'replace');
    if (!await waitAndCheck(STRING_STEP_DELAY / 2)) break;

    for (let i = 0; i < tracks.length; i++) {
      const step = tracks[i].steps[positions[i]];
      if (step && !step.final) positions[i]++;
    }
  }

  if (!vizCancelled) {
    stepCounter.classList.remove('active', 'bump');
    stepCounter.textContent = '';

    // Build resolved expressions from byte values
    const resolvedExprs = tracks.map(t => `reversed(range(${t.byte + 1}))`);

    // ── Outro: fold back into one line ──
    if (!await waitAndCheck(400)) return;
    for (let i = tracks.length; i >= 0; i--) {
      if (vizCancelled) return;
      let html = WRAPPER_OPEN;
      for (let j = 0; j < resolvedExprs.length; j++) {
        if (j > 0) html += SYN_COMMA;
        if (j < i) html += '\n  ';
        html += syntaxHighlight(resolvedExprs[j]);
      }
      if (i > 0) html += '\n';
      html += WRAPPER_CLOSE;
      resultExpr.innerHTML = html;
      if (!await waitAndCheck(Math.max(60, 200 - (tracks.length - i) * 15))) return;
    }

    // ── Final: client-side conceptual steps with highlight → replace ──
    const revExprs = tracks.map(t => `reversed(range(${t.byte + 1}))`);
    const byteVals = tracks.map(t => t.byte);
    const reprText = JSON.stringify(data.text).slice(1, -1);

    // Each step: [before, highlighted_part, after, replacement]
    const endSteps = [
      // zip(reversed(range(N)),...) → zip(39,70,...)
      ['eval(bytes(next(', `zip(${revExprs.join(',')})`, ')))', `zip(${byteVals.join(',')})`],
      // next(zip(39,70,...)) → (39,70,...)
      ['eval(bytes(', `next(zip(${byteVals.join(',')}))`, '))', `(${byteVals.join(',')})`],
      // bytes((39,70,...)) → b'FF'
      ['eval(', `bytes((${byteVals.join(',')}))`, ')', `b'${reprText}'`],
      // eval(b'FF') → 'FF'
      ['', `eval(b'${reprText}')`, '', `'${reprText}'`],
    ];

    const totalEnd = endSteps.length;
    for (let i = 0; i < totalEnd; i++) {
      if (vizCancelled) return;
      const [before, mid, after, result] = endSteps[i];
      stepCounter.textContent = `${maxSteps + i + 1}/${totalSteps}`;
      stepCounter.classList.add('active', 'bump');
      setTimeout(() => stepCounter.classList.remove('bump'), 150);
      // Highlight
      resultExpr.innerHTML =
        syntaxHighlight(before) +
        `<span class="highlight">${syntaxHighlight(mid)}</span>` +
        syntaxHighlight(after);
      if (!await waitAndCheck(800)) return;
      // Replace
      resultExpr.innerHTML =
        syntaxHighlight(before) +
        `<span class="fade-in">${syntaxHighlight(result)}</span>` +
        syntaxHighlight(after);
      if (!await waitAndCheck(600)) return;
    }
    stepCounter.classList.remove('active', 'bump');
    stepCounter.textContent = '';
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
