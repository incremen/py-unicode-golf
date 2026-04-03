let guitar        = null;
let audioCtx      = null;
let loadingPromise = null;

function ensureAudio() {
  if (guitar) return Promise.resolve();
  if (loadingPromise) return loadingPromise;
  audioCtx      = new AudioContext();
  loadingPromise = Soundfont.instrument(audioCtx, 'acoustic_guitar_nylon')
    .then(inst => { guitar = inst; });
  return loadingPromise;
}

function playStrategyNote(strategy) {
  const chord = STRATEGY_NOTES[strategy];
  if (!chord) return;
  ensureAudio().then(() => {
    const now = audioCtx.currentTime;
    chord.forEach((note, i) => {
      guitar.play(note, now + i * 0.07, { gain: 1.5 });
    });
  }).catch(() => {});
}
