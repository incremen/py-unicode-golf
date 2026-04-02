// ── Strategy metadata ─────────────────────────────────────────────────────────

const STRATEGY_COLORS = {
  decrement:        '#c0392b',
  quad_plus_3:      '#2471a3',
  bytearray_4x:     '#d35400',
  quint_plus_5:     '#17a589',
  list_range:       '#e67e22',
  triple:           '#27ae60',
  ascii_exp_2:      '#e91e8c',
  dict_enum_bytes:  '#6c5ce7',
  list_enum_bytes:  '#0984e3',
  zip_range:        '#00897b',
  zip_chain_1:      '#f0a500',
  dict_enum_range:  '#e17055',
  ascii_exp_3:      '#c0392b',
  zip_chain_2:      '#00838f',
  ascii_exp_4:      '#546e7a',
  zip_chain_3:      '#7f8c8d',
  chr:              '#FFD43B',
  anchor:           '#306998',
  trace:            '#aaa',
  triangular:       '#8e44ad',
  enum_list_8x:     '#16a085',
  slice_offset:     '#7f8c8d',
  complex_offset:   '#95a5a6',
  bin_len:          '#2c3e50',
  hex_len:          '#34495e',
  oct_len:          '#7f8c8d',
  ascii_range:      '#c0392b',
  tuple_range:      '#e74c3c',
  zip_chain_4:      '#a29bfe',
  zip_chain_5:      '#fd79a8',
  ascii_exp_1:      '#d63031',
  ascii_exp_5:      '#e17055',
  ascii_exp_6:      '#fdcb6e',
  ascii_exp_7:      '#55efc4',
  ascii_exp_8:      '#74b9ff',
  ascii_exp_9:      '#a29bfe',
  ascii_exp_10:     '#fd79a8',
  ascii_exp_11:     '#b2bec3',
};

// Python expression templates for each strategy, given a source integer n.
const STRATEGY_LABELS = {
  decrement:        n => `max(range(${n}))`,
  triple:           n => `len(str(list(bytes(${n}))))`,
  quad_plus_3:      n => `len(str(bytes(${n})))`,
  quint_plus_5:     n => `len(ascii(str(bytes(${n}))))`,
  bytearray_4x:     n => `len(str(bytearray(${n})))`,
  list_range:       n => `len(str(list(range(${n}))))`,
  zip_range:        n => `len(str(list(zip(range(${n})))))`,
  dict_enum_range:  n => `len(str(dict(enumerate(range(${n})))))`,
  list_enum_bytes:  n => `len(str(list(enumerate(bytes(${n})))))`,
  dict_enum_bytes:  n => `len(str(dict(enumerate(bytes(${n})))))`,
  ascii_exp_2:      n => `len(ascii(ascii(str(bytes(${n})))))`,
  ascii_exp_3:      n => `len(ascii(ascii(ascii(str(bytes(${n}))))))`,
  ascii_exp_4:      n => `len(ascii(ascii(ascii(ascii(str(bytes(${n})))))))`,
  zip_chain_1:      n => `len(str(list(zip(bytes(${n})))))`,
  zip_chain_2:      n => `len(str(list(zip(zip(bytes(${n}))))))`,
  zip_chain_3:      n => `len(str(list(zip(zip(zip(bytes(${n})))))))`,
  chr:              n => `chr(${n})`,
  anchor:           n => String(n),
  trace:            n => String(n),
  triangular:       n => `sum(range(${n}))`,
  enum_list_8x:     n => `len(str(list(enumerate(bytes(${n})))))`,
  slice_offset:     n => `len(str(slice(${n})))`,
  complex_offset:   n => `len(str(complex(${n})))`,
  bin_len:          n => `len(bin(${n}))`,
  hex_len:          n => `len(hex(${n}))`,
  oct_len:          n => `len(oct(${n}))`,
  ascii_range:      n => `len(ascii(range(${n})))`,
  tuple_range:      n => `len(str(tuple(range(${n}))))`,
  zip_chain_4:      n => `len(str(list(zip(zip(zip(zip(bytes(${n}))))))))`,
  zip_chain_5:      n => `len(str(list(zip(zip(zip(zip(zip(bytes(${n}))))))))))`,
  ascii_exp_1:      n => `len(ascii(str(bytes(${n}))))`,
  ascii_exp_5:      n => `len(ascii(ascii(ascii(ascii(ascii(str(bytes(${n}))))))))`,
  ascii_exp_6:      n => `len(ascii(ascii(ascii(ascii(ascii(ascii(str(bytes(${n})))))))))`,
  ascii_exp_7:      n => `len(ascii(ascii(ascii(ascii(ascii(ascii(ascii(str(bytes(${n}))))))))))`,
  ascii_exp_8:      n => `len(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(str(bytes(${n})))))))))))`,
  ascii_exp_9:      n => `len(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(str(bytes(${n}))))))))))))`,
  ascii_exp_10:     n => `len(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(str(bytes(${n})))))))))))))`,
  ascii_exp_11:     n => `len(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(ascii(str(bytes(${n}))))))))))))))`,
};

// ── Strategy notes (Hz, pentatonic spread across ~2 octaves) ─────────────────
// Families share one note; unrelated strategies each get a distinct pitch.

// Chords as Tone.js note name arrays — play them directly with poly.triggerAttack()
const STRATEGY_NOTES = {
  decrement:        ['A3', 'C4', 'E4'],        // Am
  triple:           ['G3', 'B3', 'D4'],        // G major
  bytearray_4x:     ['E3', 'G#3', 'B3'],       // E major
  quad_plus_3:      ['C4', 'E4', 'G4'],        // C major
  quint_plus_5:     ['D4', 'F#4', 'A4'],       // D major
  triangular:       ['F4', 'A4', 'C5'],        // F major
  list_range:       ['C4', 'F4', 'A4'],        // Fsus (Fmaj over C)
  tuple_range:      ['G4', 'C5', 'E5'],        // Csus
  zip_range:        ['E4', 'A4', 'B4'],        // Asus2
  dict_enum_range:  ['B3', 'D4', 'F#4'],       // Bm
  dict_enum_bytes:  ['D3', 'F3', 'A3'],        // Dm
  list_enum_bytes:  ['F3', 'Ab3', 'C4'],       // Fm
  enum_list_8x:     ['G3', 'Bb3', 'D4'],       // Gm
  bin_len:          ['C3', 'G3', 'C4'],        // C power
  hex_len:          ['A2', 'E3', 'A3'],        // A power
  oct_len:          ['D3', 'A3', 'D4'],        // D power
  ascii_range:      ['G4', 'A4', 'D5'],        // Gsus2

  ascii_exp_1:      ['A4', 'C#5', 'E5'],       // A major — all ascii_exp share
  ascii_exp_2:      ['A4', 'C#5', 'E5'],
  ascii_exp_3:      ['A4', 'C#5', 'E5'],
  ascii_exp_4:      ['A4', 'C#5', 'E5'],
  ascii_exp_5:      ['A4', 'C#5', 'E5'],
  ascii_exp_6:      ['A4', 'C#5', 'E5'],
  ascii_exp_7:      ['A4', 'C#5', 'E5'],
  ascii_exp_8:      ['A4', 'C#5', 'E5'],
  ascii_exp_9:      ['A4', 'C#5', 'E5'],
  ascii_exp_10:     ['A4', 'C#5', 'E5'],
  ascii_exp_11:     ['A4', 'C#5', 'E5'],

  zip_chain_1:      ['Eb4', 'G4', 'Bb4'],      // Eb major — all zip_chain share
  zip_chain_2:      ['Eb4', 'G4', 'Bb4'],
  zip_chain_3:      ['Eb4', 'G4', 'Bb4'],
  zip_chain_4:      ['Eb4', 'G4', 'Bb4'],
  zip_chain_5:      ['Eb4', 'G4', 'Bb4'],

  slice_offset:     ['C4', 'F4', 'G4'],        // Fsus4
  complex_offset:   ['D4', 'G4', 'A4'],        // Gsus2

  chr:              ['C5', 'E5', 'G5', 'C6'],  // C major + octave — triumphant
  anchor:           ['C2', 'G2', 'C3'],        // C power bass
  trace:            ['C4', 'E4', 'G4'],        // C major
};

// ── Layout constants ──────────────────────────────────────────────────────────

const BFS_DEPTH         = 1;
const MAX_CLICK_HISTORY = 4;
const TRACE_STEP_MS     = 1500; // total dwell time per trace step
const TRACE_ANIM_MS     = 500;  // duration of the traveling dot animation

// ── Mutable graph state ───────────────────────────────────────────────────────

const enabledStrategies = new Set(Object.keys(STRATEGY_COLORS));
const expandedNodes     = new Set();
const nodeIncomingEdges = new Map(); // nodeId -> [edgeId, ...]
const clickHistory      = [];        // oldest-first list of clicked nodeIds
const placedByExpansion = new Map(); // expandedNodeId -> Set of nodeIds it placed
const evictionStack     = [];        // nodes evicted due to MAX_CLICK_HISTORY, for back nav
let   currentFocus      = '0';
