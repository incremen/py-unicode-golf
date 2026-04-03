let guitar        = null;
let audioCtx      = null;
let loadingPromise = null;
let muted         = false;

function ensureAudio() {
  if (guitar) return Promise.resolve();
  if (loadingPromise) return loadingPromise;
  audioCtx      = new AudioContext();
  loadingPromise = Soundfont.instrument(audioCtx, 'acoustic_guitar_nylon')
    .then(inst => { guitar = inst; });
  return loadingPromise;
}

function playStrategyNote(strategy) {
  if (muted) return;
  const chord = STRATEGY_NOTES[strategy];
  if (!chord) return;
  const gain = parseFloat(document.getElementById('volume-slider').value);
  ensureAudio().then(() => {
    const now = audioCtx.currentTime;
    chord.forEach((note, i) => {
      guitar.play(note, now + i * 0.07, { gain });
    });
  }).catch(() => {});
}

document.getElementById('mute-btn').addEventListener('click', () => {
  muted = !muted;
  const btn = document.getElementById('mute-btn');
  btn.textContent = muted ? '🔇' : '🔊';
  btn.classList.toggle('muted', muted);
});
