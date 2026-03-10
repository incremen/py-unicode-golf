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
  document.documentElement.style.setProperty('--bg-rotate', (rotate || 0) + 'deg');
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


// ── Visualize animation ──────────────────────────────────────────────
// One smooth CSS animation from start to end, pausable via animation-play-state.

const VIZ_SCALE_PER_STEP = 0.025;
const VIZ_SCALE_DECAY = 0.8;
const VIZ_OPACITY_PER_STEP = 0.03;
const VIZ_OPACITY_DECAY = 0.85;
const VIZ_ROTATE_PER_STEP = -1.8;
const VIZ_HUE_PER_STEP = -2.2;
const VIZ_EASING = 'cubic-bezier(0.4, 0, 0.9, 0.95)';

let logoTotalSteps = 1;
let logoBaseRotation = 0;
let hueDirection = 1;
let vizAnimId = 0;

// Dynamic stylesheet for keyframes
const vizStyle = document.createElement('style');
document.head.appendChild(vizStyle);

function geoSum(step, decay, n) {
  return step * (1 - Math.pow(decay, n)) / (1 - decay);
}

function setBgDuration(seconds) {
  document.documentElement.style.setProperty('--bg-duration', seconds + 's');
}

function logoStart(total, durationSec) {
  logoTotalSteps = total;
  vizAnimId++;
  clearLogoTimer();

  const fromScale = LOGO_BASE_SCALE;
  const fromOpacity = LOGO_BASE_OPACITY;
  const fromRotate = logoBaseRotation;
  const toScale = LOGO_BASE_SCALE + geoSum(VIZ_SCALE_PER_STEP, VIZ_SCALE_DECAY, total);
  const toOpacity = LOGO_BASE_OPACITY + geoSum(VIZ_OPACITY_PER_STEP, VIZ_OPACITY_DECAY, total);
  const toRotate = logoBaseRotation + total * VIZ_ROTATE_PER_STEP;
  const toHue = VIZ_HUE_PER_STEP * total * 0.5 * hueDirection;

  vizStyle.textContent = `
    @keyframes logoViz${vizAnimId} {
      from {
        transform: translate(-50%, -50%) scale(${fromScale}) rotate(${fromRotate}deg);
        opacity: ${fromOpacity};
        filter: hue-rotate(0deg);
      }
      to {
        transform: translate(-50%, -50%) scale(${toScale}) rotate(${toRotate}deg);
        opacity: ${toOpacity};
        filter: hue-rotate(${toHue}deg);
      }
    }
    @keyframes bgViz${vizAnimId} {
      from { transform: rotate(${fromRotate}deg); filter: hue-rotate(0deg); }
      to { transform: rotate(${toRotate}deg); filter: hue-rotate(${toHue}deg); }
    }
  `;

  const logoAnim = `logoViz${vizAnimId} ${durationSec}s ${VIZ_EASING} forwards`;
  const bgAnim = `bgViz${vizAnimId} ${durationSec}s ${VIZ_EASING} forwards`;

  el().style.setProperty('--logo-anim', logoAnim);
  el().style.setProperty('--logo-play-state', 'running');
  document.documentElement.style.setProperty('--bg-anim', bgAnim);
  document.documentElement.style.setProperty('--bg-play-state', 'running');
}

function logoPause() {
  el().style.setProperty('--logo-play-state', 'paused');
  document.documentElement.style.setProperty('--bg-play-state', 'paused');
}

function logoResume() {
  el().style.setProperty('--logo-play-state', 'running');
  document.documentElement.style.setProperty('--bg-play-state', 'running');
}

function clearLogoAnim() {
  el().style.setProperty('--logo-anim', 'none');
  document.documentElement.style.setProperty('--bg-anim', 'none');
}

function logoReset() {
  clearLogoTimer();
  clearLogoAnim();
  logoBaseRotation += logoTotalSteps * VIZ_ROTATE_PER_STEP;
  const shrinkDuration = Math.min(0.6, 0.15 + logoTotalSteps * 0.02);
  setBgDuration(shrinkDuration);
  setLogoTransition(shrinkDuration, 'ease-out');
  hueDirection *= -1;
  setLogo(LOGO_BASE_SCALE - 0.02, LOGO_BASE_OPACITY, logoBaseRotation, 0);
  logoSettleTimer = setTimeout(() => {
    setLogoTransition(0.15);
    setLogo(LOGO_BASE_SCALE, LOGO_BASE_OPACITY, logoBaseRotation, 0);
  }, shrinkDuration * 1000);
}

function logoDelayedReset() {
  clearLogoTimer();
  logoSettleTimer = setTimeout(logoReset, 2000);
}
