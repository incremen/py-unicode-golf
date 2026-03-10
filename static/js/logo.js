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

const VIZ_SCALE_PER_STEP = 0.02;
const VIZ_OPACITY_PER_STEP = 0.03;
const VIZ_OPACITY_DECAY = 0.85;
const VIZ_ROTATE_PER_STEP = -1.8;
const VIZ_HUE_PER_STEP = -2.2;
const VIZ_EASING = 'cubic-bezier(0.4, 0, 0.9, 0.95)';

let logoTotalSteps = 1;
let logoBaseRotation = 0;
let hueDirection = 1;
let vizAnimId = 0;
let vizEndState = { rotate: 0 };

const vizStyle = document.createElement('style');
document.head.appendChild(vizStyle);

function geoSum(step, decay, n) {
  return step * (1 - Math.pow(decay, n)) / (1 - decay);
}

function setLogoAnim(name, duration, easing) {
  const logoAnim = `${name} ${duration}s ${easing} forwards`;
  const bgAnim = `bg${name} ${duration}s ${easing} forwards`;
  el().style.setProperty('--logo-anim', logoAnim);
  el().style.setProperty('--logo-play-state', 'running');
  document.documentElement.style.setProperty('--bg-anim', bgAnim);
  document.documentElement.style.setProperty('--bg-play-state', 'running');
}

function clearLogoAnim() {
  el().style.setProperty('--logo-anim', 'none');
  document.documentElement.style.setProperty('--bg-anim', 'none');
}

function logoStart(total, durationSec) {
  logoTotalSteps = total;
  vizAnimId++;
  clearLogoTimer();

  const fromRotate = logoBaseRotation;
  const toScale = LOGO_BASE_SCALE + VIZ_SCALE_PER_STEP * total;
  const toOpacity = LOGO_BASE_OPACITY + geoSum(VIZ_OPACITY_PER_STEP, VIZ_OPACITY_DECAY, total);
  const toRotate = logoBaseRotation + total * VIZ_ROTATE_PER_STEP;
  const toHue = VIZ_HUE_PER_STEP * total * hueDirection;
  vizEndState = { rotate: toRotate };

  vizStyle.textContent = `
    @keyframes logoViz${vizAnimId} {
      from {
        transform: translate(-50%, -50%) scale(${LOGO_BASE_SCALE}) rotate(${fromRotate}deg);
        opacity: ${LOGO_BASE_OPACITY};
        filter: hue-rotate(0deg);
      }
      to {
        transform: translate(-50%, -50%) scale(${toScale}) rotate(${toRotate}deg);
        opacity: ${toOpacity};
        filter: hue-rotate(${toHue}deg);
      }
    }
    @keyframes bglogoViz${vizAnimId} {
      from { transform: rotate(${fromRotate}deg); filter: hue-rotate(0deg); }
      to { transform: rotate(${toRotate}deg); filter: hue-rotate(${toHue}deg); }
    }
  `;

  setLogoAnim(`logoViz${vizAnimId}`, durationSec, VIZ_EASING);
}

function logoPause() {
  el().style.setProperty('--logo-play-state', 'paused');
  document.documentElement.style.setProperty('--bg-play-state', 'paused');
}

function logoResume() {
  el().style.setProperty('--logo-play-state', 'running');
  document.documentElement.style.setProperty('--bg-play-state', 'running');
}

// Smoothly animate from current state back to base.
// Reads computed styles so it starts exactly where the animation is right now.
function logoSmoothReset(targetRotate, duration) {
  clearLogoTimer();
  logoPause();

  const logoStyle = getComputedStyle(document.body, '::before');
  const bgStyle = getComputedStyle(document.documentElement, '::after');

  logoBaseRotation = targetRotate;
  hueDirection *= -1;
  vizAnimId++;

  vizStyle.textContent = `
    @keyframes logoViz${vizAnimId} {
      from {
        transform: ${logoStyle.transform};
        opacity: ${logoStyle.opacity};
        filter: ${logoStyle.filter};
      }
      to {
        transform: translate(-50%, -50%) scale(${LOGO_BASE_SCALE}) rotate(${targetRotate}deg);
        opacity: ${LOGO_BASE_OPACITY};
        filter: hue-rotate(0deg);
      }
    }
    @keyframes bglogoViz${vizAnimId} {
      from { transform: ${bgStyle.transform}; filter: ${bgStyle.filter}; }
      to { transform: rotate(${targetRotate}deg); filter: hue-rotate(0deg); }
    }
  `;

  setLogoAnim(`logoViz${vizAnimId}`, duration, 'ease-out');

  // After reset animation ends, clean up so transitions work again
  logoSettleTimer = setTimeout(() => {
    setLogo(LOGO_BASE_SCALE, LOGO_BASE_OPACITY, targetRotate, 0);
    clearLogoAnim();
  }, duration * 1000 + 50);
}

function logoCancel() {
  // Extract current rotation from computed transform matrix
  const m = new DOMMatrix(getComputedStyle(document.body, '::before').transform);
  const currentRotate = Math.atan2(m.b, m.a) * 180 / Math.PI;
  logoSmoothReset(currentRotate, 0.5);
}

function logoReset() {
  logoSmoothReset(vizEndState.rotate, 0.6);
}

function logoDelayedReset() {
  clearLogoTimer();
  logoSettleTimer = setTimeout(logoReset, 2000);
}
