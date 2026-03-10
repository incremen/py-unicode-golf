const LOGO_BASE_SCALE = 1;
const LOGO_BASE_OPACITY = 0.2;
const LOGO_SCALE_PER_STEP = 0.025;
const LOGO_OPACITY_PER_STEP = 0.03;
const LOGO_OVERSHOOT = 0.03;

let logoCombo = 0;
let logoSettleTimer = null;

function setLogo(scale, opacity) {
  document.body.style.setProperty('--logo-scale', scale);
  document.body.style.setProperty('--logo-opacity', opacity);
}

function logoTarget() {
  return {
    scale: LOGO_BASE_SCALE + logoCombo * LOGO_SCALE_PER_STEP,
    opacity: LOGO_BASE_OPACITY + logoCombo * LOGO_OPACITY_PER_STEP,
  };
}

function logoStep() {
  logoCombo++;
  clearTimeout(logoSettleTimer);
  const t = logoTarget();
  // Overshoot
  setLogo(t.scale + LOGO_OVERSHOOT, t.opacity + LOGO_OVERSHOOT);
  // Settle back to real target
  logoSettleTimer = setTimeout(() => setLogo(t.scale, t.opacity), 150);
}

function logoReset() {
  clearTimeout(logoSettleTimer);
  logoCombo = 0;
  // Undershoot slightly then settle
  setLogo(LOGO_BASE_SCALE - 0.02, LOGO_BASE_OPACITY);
  logoSettleTimer = setTimeout(() => setLogo(LOGO_BASE_SCALE, LOGO_BASE_OPACITY), 200);
}

function logoPop() {
  if (vizRunning) return;
  clearTimeout(logoSettleTimer);
  setLogo(LOGO_BASE_SCALE + 0.05, LOGO_BASE_OPACITY + 0.15);
  logoSettleTimer = setTimeout(logoReset, 600);
}
