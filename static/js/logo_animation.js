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

function setLogoTransition(seconds) {
  el().style.setProperty('--logo-transition', seconds + 's');
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
const VIZ_OPACITY_PER_STEP = 0.03;
const VIZ_ROTATE_PER_STEP = -0.4;
const VIZ_HUE_PER_STEP = -2.2;
const VIZ_OVERSHOOT = 0.03;

let logoCombo = 0;
let logoTotalSteps = 1;
let logoBaseRotation = 0;

function vizTarget() {
  // Hue follows a sine wave: 0 at start, peak at middle, 0 at end
  const progress = logoCombo / logoTotalSteps;
  const hue = Math.sin(progress * Math.PI) * VIZ_HUE_PER_STEP * logoTotalSteps * 0.5;
  return {
    scale: LOGO_BASE_SCALE + logoCombo * VIZ_SCALE_PER_STEP,
    opacity: LOGO_BASE_OPACITY + logoCombo * VIZ_OPACITY_PER_STEP,
    rotate: logoBaseRotation + logoCombo * VIZ_ROTATE_PER_STEP,
    hue,
  };
}

function logoStep(total) {
  logoCombo++;
  if (total) logoTotalSteps = total;
  clearLogoTimer();
  setLogoTransition(0.15);
  const t = vizTarget();
  setLogo(t.scale + VIZ_OVERSHOOT, t.opacity + VIZ_OVERSHOOT, t.rotate - 0.5, t.hue);
  logoSettleTimer = setTimeout(() => setLogo(t.scale, t.opacity, t.rotate, t.hue), 150);
}

function logoReset() {
  clearLogoTimer();
  logoBaseRotation += logoCombo * VIZ_ROTATE_PER_STEP;
  const shrinkDuration = Math.min(0.6, 0.15 + logoCombo * 0.02);
  setLogoTransition(shrinkDuration);
  logoCombo = 0;
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
