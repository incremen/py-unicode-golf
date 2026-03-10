// ── Shared ──────────────────────────────────────────────────────────

const LOGO_BASE_SCALE = 1;
const LOGO_BASE_OPACITY = 0.2;

let logoSettleTimer = null;
const el = () => document.body;

function setLogo(scale, opacity, rotate, hue) {
  el().style.setProperty('--logo-scale', scale);
  el().style.setProperty('--logo-opacity', opacity);
  el().style.setProperty('--logo-rotate', (rotate || 0) + 'deg');
  el().style.setProperty('--logo-hue', (hue || 0) + 'deg');
  document.documentElement.style.setProperty('--bg-hue', (hue || 0) + 'deg');
  document.documentElement.style.setProperty('--bg-angle', (90 + (rotate || 0)) + 'deg');
  document.documentElement.style.setProperty('--bg-angle-inv', (270 + (rotate || 0)) + 'deg');
}

function setLogoTransition(seconds, easing) {
  el().style.setProperty('--logo-transition', seconds + 's');
  el().style.setProperty('--logo-easing', easing || 'ease-out');
}

function clearLogoTimer() {
  clearTimeout(logoSettleTimer);
}


// ── Tab button animation ────────────────────────────────────────────
// Simple pop: scale up slightly, then back down.

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


// ── Visualize combo animation ───────────────────────────────────────
// Each step: grow + rotate + overshoot, then settle.
// End: hold for 2s, then shrink back (faster if bigger).

const VIZ_SCALE_PER_STEP = 0.025;
const VIZ_SCALE_DECAY = 0.97;
const VIZ_OPACITY_PER_STEP = 0.03;
const VIZ_OPACITY_DECAY = 0.85;
const VIZ_ROTATE_PER_STEP = -1.5;
const VIZ_HUE_PER_STEP = -2.2;

let logoCombo = 0;
let logoTotalSteps = 1;
let logoBaseRotation = 0;
let hueDirection = 1;

function vizTarget() {
  const progress = logoCombo / logoTotalSteps;
  const hue = Math.sin(progress * Math.PI) * VIZ_HUE_PER_STEP * logoTotalSteps * 0.5 * hueDirection;
  return {
    // Geometric series: step * (1 + 0.95 + 0.95^2 + ...) = step * (1 - decay^n) / (1 - decay)
    scale: LOGO_BASE_SCALE + VIZ_SCALE_PER_STEP * (1 - Math.pow(VIZ_SCALE_DECAY, logoCombo)) / (1 - VIZ_SCALE_DECAY),
    opacity: LOGO_BASE_OPACITY + VIZ_OPACITY_PER_STEP * (1 - Math.pow(VIZ_OPACITY_DECAY, logoCombo)) / (1 - VIZ_OPACITY_DECAY),
    rotate: logoBaseRotation + logoCombo * VIZ_ROTATE_PER_STEP,
    hue,
  };
}

function logoStep(total) {
  logoCombo++;
  if (total) logoTotalSteps = total;
  clearLogoTimer();
  setLogoTransition(0.3);
  const t = vizTarget();
  setLogo(t.scale, t.opacity, t.rotate, t.hue);
}

function logoReset() {
  clearLogoTimer();
  logoBaseRotation += logoCombo * VIZ_ROTATE_PER_STEP;
  const shrinkDuration = Math.min(0.6, 0.15 + logoCombo * 0.02);
  setLogoTransition(shrinkDuration, 'ease-out');
  logoCombo = 0;
  hueDirection *= -1;
  setLogo(LOGO_BASE_SCALE - 0.02, LOGO_BASE_OPACITY, logoBaseRotation, 0);
  logoSettleTimer = setTimeout(() => {
    setLogoTransition(0.15);
    setLogo(LOGO_BASE_SCALE, LOGO_BASE_OPACITY, logoBaseRotation, 0);
  }, shrinkDuration * 1000);
}

function logoDelayedReset() {
  clearLogoTimer();
  const t = vizTarget();
  setLogo(t.scale, t.opacity, t.rotate);
  logoSettleTimer = setTimeout(logoReset, 2000);
}
