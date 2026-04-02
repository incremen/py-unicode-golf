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

const STRATEGY_NOTES = {
  decrement:        261.63,  // C4  — step-down feel
  triple:           392.00,  // G4  — the core 3× multiplier
  bytearray_4x:     329.63,  // E4
  quad_plus_3:      440.00,  // A4
  quint_plus_5:     493.88,  // B4
  triangular:       587.33,  // D5  — big jump up
  list_range:       523.25,  // C5
  tuple_range:      554.37,  // C#5
  zip_range:        659.25,  // E5
  dict_enum_range:  698.46,  // F5
  list_enum_bytes:  739.99,  // F#5
  dict_enum_bytes:  783.99,  // G5
  enum_list_8x:     830.61,  // Ab5
  bin_len:          293.66,  // D4
  hex_len:          349.23,  // F4
  oct_len:          415.30,  // Ab4
  ascii_range:      466.16,  // Bb4

  // Families — one shared note each
  ascii_exp_1:      880.00,  // A5 — high sparkle (all ascii_exp same)
  ascii_exp_2:      880.00,
  ascii_exp_3:      880.00,
  ascii_exp_4:      880.00,
  ascii_exp_5:      880.00,
  ascii_exp_6:      880.00,
  ascii_exp_7:      880.00,
  ascii_exp_8:      880.00,
  ascii_exp_9:      880.00,
  ascii_exp_10:     880.00,
  ascii_exp_11:     880.00,

  zip_chain_1:      622.25,  // Eb5 — shimmery (all zip_chain same)
  zip_chain_2:      622.25,
  zip_chain_3:      622.25,
  zip_chain_4:      622.25,
  zip_chain_5:      622.25,

  chr:             1046.50,  // C6  — triumphant arrival
  anchor:           130.81,  // C3  — deep bass thud from s
  trace:            523.25,  // C5
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
