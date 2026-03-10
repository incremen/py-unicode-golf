// ── CSS property helpers ─────────────────────────────────────────────

const LOGO_BASE_SCALE = 1;
const LOGO_BASE_OPACITY = 0.2;

let logoSettleTimer = null;
let logoBaseRotation = 0;

function setLogo(scale, opacity, rotate, hue) {
  const body = document.body.style;
  const root = document.documentElement.style;
  body.setProperty('--logo-scale', scale);
  body.setProperty('--logo-opacity', opacity);
  body.setProperty('--logo-rotate', (rotate || 0) + 'deg');
  body.setProperty('--logo-hue', (hue || 0) + 'deg');
  root.setProperty('--bg-hue', (hue || 0) + 'deg');
  root.setProperty('--bg-rotate', (rotate || 0) + 'deg');
}

function setLogoTransition(seconds, easing) {
  document.body.style.setProperty('--logo-transition', seconds + 's');
  document.body.style.setProperty('--logo-easing', easing || 'ease-out');
}

function clearLogoTimer() {
  clearTimeout(logoSettleTimer);
}


// ── Tab button pop ──────────────────────────────────────────────────

function logoPop() {
  if (vizRunning) return;
  clearLogoTimer();
  setLogoTransition(0.15);
  setLogo(LOGO_BASE_SCALE + 0.05, LOGO_BASE_OPACITY + 0.15, logoBaseRotation);
  logoSettleTimer = setTimeout(() => {
    setLogoTransition(0.5);
    setLogo(LOGO_BASE_SCALE, LOGO_BASE_OPACITY, logoBaseRotation);
  }, 200);
}


// ── Visualization animation (CSS keyframes) ─────────────────────────
// Uses dynamic @keyframes so animation-play-state works for pause/resume.
// logoStart()       — begin animation to target state
// logoPause/Resume  — freeze/unfreeze via animation-play-state
// logoCancel        — cancelled mid-viz: smooth return to base
// logoReset         — natural end: smooth return to base
// Both cancel/reset use logoSmoothReset which reads getComputedStyle
// to start the return animation from wherever the current frame is.

const VIZ_SCALE_PER_STEP = 0.02;
const VIZ_OPACITY_PER_STEP = 0.03;
const VIZ_OPACITY_DECAY = 0.85;
const VIZ_ROTATE_PER_STEP = -1.8;
const VIZ_HUE_PER_STEP = -2.2;
const VIZ_EASING = 'cubic-bezier(0.4, 0, 0.9, 0.95)';

let hueDirection = 1;
let vizAnimId = 0;
let vizEndRotate = 0;

const vizStyle = document.createElement('style');
document.head.appendChild(vizStyle);

function geoSum(perStep, decay, n) {
  return perStep * (1 - Math.pow(decay, n)) / (1 - decay);
}

// ── Animation plumbing ──────────────────────────────────────────────

function setAnim(name, duration, easing) {
  const body = document.body.style;
  const root = document.documentElement.style;
  body.setProperty('--logo-anim', `${name} ${duration}s ${easing} forwards`);
  body.setProperty('--logo-play-state', 'running');
  root.setProperty('--bg-anim', `bg${name} ${duration}s ${easing} forwards`);
  root.setProperty('--bg-play-state', 'running');
}

function clearAnim() {
  document.body.style.setProperty('--logo-anim', 'none');
  document.documentElement.style.setProperty('--bg-anim', 'none');
}

function writeKeyframes(id, logoFrom, logoTo, bgFrom, bgTo) {
  vizStyle.textContent = `
    @keyframes viz${id} {
      from { transform: ${logoFrom.transform}; opacity: ${logoFrom.opacity}; filter: ${logoFrom.filter}; }
      to   { transform: ${logoTo.transform}; opacity: ${logoTo.opacity}; filter: ${logoTo.filter}; }
    }
    @keyframes bgviz${id} {
      from { transform: ${bgFrom.transform}; filter: ${bgFrom.filter}; }
      to   { transform: ${bgTo.transform}; filter: ${bgTo.filter}; }
    }`;
}

// ── Public API ──────────────────────────────────────────────────────

function logoStart(total, durationSec) {
  vizAnimId++;
  clearLogoTimer();

  const fromRotate = logoBaseRotation;
  const toScale = LOGO_BASE_SCALE + VIZ_SCALE_PER_STEP * total;
  const toOpacity = LOGO_BASE_OPACITY + geoSum(VIZ_OPACITY_PER_STEP, VIZ_OPACITY_DECAY, total);
  const toRotate = logoBaseRotation + total * VIZ_ROTATE_PER_STEP;
  const toHue = VIZ_HUE_PER_STEP * total * hueDirection;
  vizEndRotate = toRotate;

  writeKeyframes(vizAnimId,
    { transform: `translate(-50%,-50%) scale(${LOGO_BASE_SCALE}) rotate(${fromRotate}deg)`,
      opacity: LOGO_BASE_OPACITY, filter: 'hue-rotate(0deg)' },
    { transform: `translate(-50%,-50%) scale(${toScale}) rotate(${toRotate}deg)`,
      opacity: toOpacity, filter: `hue-rotate(${toHue}deg)` },
    { transform: `rotate(${fromRotate}deg)`, filter: 'hue-rotate(0deg)' },
    { transform: `rotate(${toRotate}deg)`, filter: `hue-rotate(${toHue}deg)` },
  );

  setAnim(`viz${vizAnimId}`, durationSec, VIZ_EASING);
}

function logoPause() {
  document.body.style.setProperty('--logo-play-state', 'paused');
  document.documentElement.style.setProperty('--bg-play-state', 'paused');
}

function logoResume() {
  document.body.style.setProperty('--logo-play-state', 'running');
  document.documentElement.style.setProperty('--bg-play-state', 'running');
}

function logoSmoothReset(targetRotate, duration) {
  clearLogoTimer();
  logoPause();

  const logoNow = getComputedStyle(document.body, '::before');
  const bgNow = getComputedStyle(document.documentElement, '::after');

  logoBaseRotation = targetRotate;
  hueDirection *= -1;
  vizAnimId++;

  writeKeyframes(vizAnimId,
    { transform: logoNow.transform, opacity: logoNow.opacity, filter: logoNow.filter },
    { transform: `translate(-50%,-50%) scale(${LOGO_BASE_SCALE}) rotate(${targetRotate}deg)`,
      opacity: LOGO_BASE_OPACITY, filter: 'hue-rotate(0deg)' },
    { transform: bgNow.transform, filter: bgNow.filter },
    { transform: `rotate(${targetRotate}deg)`, filter: 'hue-rotate(0deg)' },
  );

  setAnim(`viz${vizAnimId}`, duration, 'ease-out');

  logoSettleTimer = setTimeout(() => {
    setLogo(LOGO_BASE_SCALE, LOGO_BASE_OPACITY, targetRotate, 0);
    clearAnim();
  }, duration * 1000 + 50);
}

function logoCancel() {
  const m = new DOMMatrix(getComputedStyle(document.body, '::before').transform);
  logoSmoothReset(Math.atan2(m.b, m.a) * 180 / Math.PI, 0.5);
}

function logoReset() {
  logoSmoothReset(vizEndRotate, 0.6);
}

function logoDelayedReset() {
  clearLogoTimer();
  logoSettleTimer = setTimeout(logoReset, 2000);
}
