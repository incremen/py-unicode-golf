let plucks = null;

function ensureAudio() {
  if (plucks) return;
  Tone.start();
  // One PluckSynth per voice (PluckSynth is monophonic, can't use PolySynth)
  plucks = Array.from({ length: 4 }, () =>
    new Tone.PluckSynth({ attackNoise: 1.5, dampening: 4000, resonance: 0.96 })
      .toDestination()
  );
  plucks.forEach(p => { p.volume.value = -8; });
}

function playStrategyNote(strategy) {
  try {
    const chord = STRATEGY_NOTES[strategy];
    if (!chord) return;
    ensureAudio();
    const now = Tone.now();
    chord.forEach((note, i) => {
      if (plucks[i]) plucks[i].triggerAttack(note, now + i * 0.07);
    });
  } catch (e) {
    // never let audio errors block the animation
  }
}
