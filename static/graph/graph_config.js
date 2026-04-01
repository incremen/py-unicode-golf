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
};

// ── Layout constants ──────────────────────────────────────────────────────────

const BFS_DEPTH         = 1;
const MAX_CLICK_HISTORY = 4;

// ── Mutable graph state ───────────────────────────────────────────────────────

const enabledStrategies = new Set(Object.keys(STRATEGY_COLORS));
const expandedNodes     = new Set();
const nodeIncomingEdges = new Map(); // nodeId -> [edgeId, ...]
const clickHistory      = [];        // oldest-first list of clicked nodeIds
const placedByExpansion = new Map(); // expandedNodeId -> Set of nodeIds it placed
const evictionStack     = [];        // nodes evicted due to MAX_CLICK_HISTORY, for back nav
let   currentFocus      = '0';
