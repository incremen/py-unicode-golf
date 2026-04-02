// ── Audio engine ──────────────────────────────────────────────────────────────

let audioCtx = null;

function ensureAudio() {
  if (!audioCtx) audioCtx = new AudioContext();
  if (audioCtx.state === 'suspended') audioCtx.resume();
}

// Plays a single note with a quick attack and exponential decay.
function playNote(frequency, duration = 0.35, type = 'triangle') {
  ensureAudio();

  const osc  = audioCtx.createOscillator();
  const gain = audioCtx.createGain();

  osc.connect(gain);
  gain.connect(audioCtx.destination);

  osc.type = type;
  osc.frequency.setValueAtTime(frequency, audioCtx.currentTime);

  gain.gain.setValueAtTime(0, audioCtx.currentTime);
  gain.gain.linearRampToValueAtTime(0.22, audioCtx.currentTime + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);

  osc.start(audioCtx.currentTime);
  osc.stop(audioCtx.currentTime + duration + 0.05);
}

function playStrategyNote(strategy) {
  const freq = STRATEGY_NOTES[strategy];
  if (freq) playNote(freq);
}
