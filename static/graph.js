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
  chr:              '#888888',
};

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

// Layout Constants
const BFS_DEPTH         = 1;
const MAX_CLICK_HISTORY = 4;

const TOP_5_STRATEGIES = new Set([
  'decrement', 'quad_plus_3', 'bytearray_4x', 'quint_plus_5', 'list_range',
]);

// const enabledStrategies = new Set(TOP_5_STRATEGIES);
const enabledStrategies = new Set(Object.keys(STRATEGY_COLORS));

const expandedNodes     = new Set();
const nodeIncomingEdges = new Map(); // nodeId -> [edgeId, ...]
const clickHistory      = [];        // oldest-first list of clicked nodeIds
const placedByExpansion = new Map(); // expandedNodeId -> Set of nodeIds it placed
const evictionStack     = [];        // nodes evicted due to MAX_CLICK_HISTORY, for back nav
let   currentFocus      = '0';       // most recently clicked node

// ── Initialization ───────────────────────────────────────────────────────────

const cy = cytoscape({
  container: document.getElementById('cy'),
  userZoomingEnabled: true,
  userPanningEnabled: true,
  style: CYTOSCAPE_STYLES,
});

/**
 * Main entry point for the application.
 */
function init() {
  buildStrategyChecklist();
  placeNode(0, 0, 0);
  cy.getElementById('0').addClass('focused');
  clickHistory.push('0');
  expandBFS(0).then(() => cy.center(cy.getElementById('0')));
}

// ── Graph Construction ───────────────────────────────────────────────────────

function placeNode(nodeId, x = 0, y = 0) {
  const id = String(nodeId);
  if (!cy.getElementById(id).length) {
    cy.add({ data: { id, label: id }, position: { x, y } });
  }
}

function placeNeighborsRings(focusId, neighbors, parentId) {
  const focusEl  = cy.getElementById(String(focusId));
  const focusPos = focusEl.position();
  const unplaced = neighbors.filter(neighbor => !cy.getElementById(String(neighbor.id)).length);

  if (unplaced.length === 0) return;

  const INNER_RADIUS = 110;
  const RING_SPACING = 85;
  const MAX_PER_RING = 7;

  const parentEl = parentId ? cy.getElementById(String(parentId)) : null;
  let blockAngle  = null;
  if (parentEl && parentEl.length) {
    const parentPos = parentEl.position();
    blockAngle = Math.atan2(parentPos.y - focusPos.y, parentPos.x - focusPos.x);
  }

  unplaced.forEach((neighbor, index) => {
    const ringIndex    = Math.floor(index / MAX_PER_RING);
    const indexInRing  = index % MAX_PER_RING;
    const nodesInRing  = Math.min(MAX_PER_RING, unplaced.length - ringIndex * MAX_PER_RING);
    const radius       = INNER_RADIUS + ringIndex * RING_SPACING;

    let angle;
    if (blockAngle !== null) {
      if (nodesInRing === 1) {
        angle = blockAngle + Math.PI;
      } else {
        const sweep      = Math.PI * 1.33;
        const startAngle = blockAngle + Math.PI - sweep / 2;
        const step       = sweep / (nodesInRing - 1);
        const offset     = ringIndex % 2 === 1 ? step / 2 : 0;
        angle = startAngle + indexInRing * step + offset;
      }
    } else {
      if (nodesInRing === 1) {
        angle = 0;
      } else {
        const step   = (Math.PI * 2) / nodesInRing;
        const offset = ringIndex % 2 === 1 ? step / 2 : 0;
        angle = indexInRing * step + offset;
      }
    }

    placeNode(neighbor.id, focusPos.x + radius * Math.cos(angle), focusPos.y + radius * Math.sin(angle));
  });
}

function placeEdge(sourceId, targetId, strategy) {
  const edgeId = `e-${sourceId}-${targetId}-${strategy}`;
  if (!cy.getElementById(edgeId).length) {
    const labelFn = STRATEGY_LABELS[strategy];
    const label   = labelFn ? labelFn(sourceId) : strategy;
    cy.add({
      data: {
        id: edgeId,
        source: String(sourceId),
        target: String(targetId),
        strategy: strategy,
        label,
        color: STRATEGY_COLORS[strategy] || '#888',
      }
    });
    
    // Track all incoming edges per node
    const targetIdStr = String(targetId);
    if (!nodeIncomingEdges.has(targetIdStr)) {
      nodeIncomingEdges.set(targetIdStr, []);
    }
    nodeIncomingEdges.get(targetIdStr).push(edgeId);
  }
}


// ── Visibility & UI ──────────────────────────────────────────────────────────

// An edge is shown if its strategy is enabled AND either:
// - it comes from the current focus node, OR
// - it connects two history nodes (the tail trail)
function refreshEdgeVisibility() {
  const historySet = new Set(clickHistory);
  cy.edges().forEach(edge => {
    const source = edge.data('source');
    const target = edge.data('target');
    const strategyOn = enabledStrategies.has(edge.data('strategy'));
    const fromFocus = source === currentFocus;
    const isTailEdge = historySet.has(source) && historySet.has(target);
    edge.style('display', strategyOn && (fromFocus || isTailEdge) ? 'element' : 'none');
  });
}

// History nodes are always visible. Others are visible only if they have a
// visible incoming edge (i.e. they are a neighbor of the current focus).
function refreshNodeVisibility() {
  cy.nodes().forEach(node => {
    const id = node.id();
    if (clickHistory.includes(id)) {
      node.style('display', 'element');
      return;
    }
    const edges = nodeIncomingEdges.get(id) || [];
    const hasVisibleIncoming = edges.some(edgeId => cy.getElementById(edgeId).style('display') !== 'none');
    node.style('display', hasVisibleIncoming ? 'element' : 'none');
  });
}

function buildStrategyChecklist() {
  const panel = document.getElementById('strategy-panel');
  if (!panel) return;

  Object.keys(STRATEGY_COLORS).forEach(strategy => {
    const isChecked = enabledStrategies.has(strategy);
    const row = document.createElement('label');
    row.className = 'strategy-row';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = isChecked;
    checkbox.addEventListener('change', () => toggleStrategy(strategy, checkbox.checked));

    const colorDot = document.createElement('span');
    colorDot.className = 'strategy-color-dot';
    colorDot.style.background = STRATEGY_COLORS[strategy];

    const textLabel = document.createElement('span');
    textLabel.className = 'strategy-label';
    textLabel.textContent = strategy;

    row.append(checkbox, colorDot, textLabel);
    panel.appendChild(row);
  });
}

function toggleStrategy(strategy, enabled) {
  if (enabled) {
    enabledStrategies.add(strategy);
  } else {
    enabledStrategies.delete(strategy);
  }
  refreshEdgeVisibility();
  refreshNodeVisibility();
}

function updateInfoBar(focusId) {
  const infoBar = document.getElementById('info');
  if (infoBar) {
    infoBar.textContent = `node ${focusId} | ${expandedNodes.size} expanded total`;
  }
}

// ── Traversal Logic ──────────────────────────────────────────────────────────

/**
 * Fetches and renders the 1-hop neighborhood of a node.
 */
function makeChrNeighbor(nodeId) {
  const codepoint  = Number(nodeId);
  const raw        = String.fromCodePoint(codepoint);
  const isPrintable = codepoint >= 32 && codepoint !== 127 && raw.trim() !== '';
  const label      = isPrintable ? raw : `\\x${codepoint.toString(16).padStart(2, '0')}`;
  return { id: `chr-${nodeId}`, label, isChr: true };
}

async function expandNode(nodeId, parentId = null) {
  const id = String(nodeId);
  if (expandedNodes.has(id)) return [];

  expandedNodes.add(id);

  const response = await fetch(`/api/neighbors/${nodeId}`);
  const data     = await response.json();

  cy.getElementById(id).addClass('expanded');

  const chrNeighbor = makeChrNeighbor(nodeId);
  const allNeighbors = [...data.neighbors, chrNeighbor];

  const beforeIds = new Set(cy.nodes().map(node => node.id()));
  placeNeighborsRings(data.focus, allNeighbors, parentId);

  // Add the chr node to the graph with its special class and label
  const chrEl = cy.getElementById(chrNeighbor.id);
  if (chrEl.length) chrEl.addClass('chr-node').data('label', chrNeighbor.label);

  const placed = new Set(cy.nodes().filter(node => !beforeIds.has(node.id())).map(node => node.id()));
  placedByExpansion.set(id, placed);

  data.neighbors.forEach(neighbor => placeEdge(data.focus, neighbor.id, neighbor.strategy));

  // Add chr edge
  const chrEdgeId = `e-${nodeId}-${chrNeighbor.id}-chr`;
  if (!cy.getElementById(chrEdgeId).length) {
    cy.add({ data: { id: chrEdgeId, source: id, target: chrNeighbor.id, strategy: 'chr', label: STRATEGY_LABELS.chr(nodeId), color: STRATEGY_COLORS.chr } });
    if (!nodeIncomingEdges.has(chrNeighbor.id)) nodeIncomingEdges.set(chrNeighbor.id, []);
    nodeIncomingEdges.get(chrNeighbor.id).push(chrEdgeId);
  }

  refreshEdgeVisibility();
  refreshNodeVisibility();

  return data.neighbors.map(neighbor => neighbor.id);
}

function evictOldest() {
  const evicted = clickHistory.shift();
  expandedNodes.delete(evicted);
  // Save position so we can restore the node to the same spot later
  const evictedPos = cy.getElementById(evicted).position();
  evictionStack.push({ id: evicted, pos: { x: evictedPos.x, y: evictedPos.y } });

  const needed = new Set(clickHistory);
  clickHistory.forEach(id => {
    (placedByExpansion.get(id) || new Set()).forEach(nodeId => needed.add(nodeId));
  });

  cy.nodes().forEach(node => {
    if (!needed.has(node.id())) {
      nodeIncomingEdges.delete(node.id());
      node.remove();
    }
  });
  placedByExpansion.delete(evicted);
}

async function goBack() {
  if (clickHistory.length <= 1) return;

  // Remove the most recent node and its placed neighbors
  const removed = clickHistory.pop();
  expandedNodes.delete(removed);
  const placedByRemoved = placedByExpansion.get(removed) || new Set();

  const stillNeeded = new Set(clickHistory);
  clickHistory.forEach(id => {
    (placedByExpansion.get(id) || new Set()).forEach(nodeId => stillNeeded.add(nodeId));
  });

  placedByRemoved.forEach(nodeId => {
    if (!stillNeeded.has(nodeId)) {
      nodeIncomingEdges.delete(nodeId);
      cy.getElementById(nodeId).remove();
    }
  });
  placedByExpansion.delete(removed);

  // Restore the previously evicted node at the front of history
  if (evictionStack.length > 0) {
    const { id: restored, pos } = evictionStack.pop();
    clickHistory.unshift(restored);
    // Re-add the node to the graph at its original position before expanding
    placeNode(restored, pos.x, pos.y);
    await expandNode(restored, null);
  }

  currentFocus = clickHistory[clickHistory.length - 1];
  cy.nodes().removeClass('focused');
  cy.getElementById(currentFocus).addClass('focused');

  refreshEdgeVisibility();
  refreshNodeVisibility();
  updateBackButton();

  const visibleEles = cy.elements().filter(ele => ele.style('display') !== 'none');
  if (visibleEles.length > 0) {
    cy.animate({ fit: { eles: visibleEles, padding: 80 }, duration: 400, easing: 'ease-out-cubic' });
  }
  updateInfoBar(currentFocus);
}

function updateBackButton() {
  document.getElementById('back-btn').disabled = clickHistory.length <= 1;
}

/**
 * Expands a node and its descendants up to a certain depth.
 */
async function expandBFS(startNodeId, depth = BFS_DEPTH) {
  const id = String(startNodeId);

  let parentId = null;
  if (!clickHistory.includes(id)) {
    parentId = clickHistory.length > 0 ? clickHistory[clickHistory.length - 1] : null;
    clickHistory.push(id);
    if (clickHistory.length > MAX_CLICK_HISTORY) {
      evictOldest();
    }
  }

  let currentLevel = [startNodeId];
  for (let level = 0; level < depth; level++) {
    const unexpanded = currentLevel.filter(nodeId => !expandedNodes.has(String(nodeId)));
    if (unexpanded.length === 0) break;

    const nextLevelResults = await Promise.all(unexpanded.map(nodeId => expandNode(nodeId, parentId)));
    currentLevel = [...new Set(nextLevelResults.flat())];
  }

  const visibleEles = cy.elements().filter(ele => ele.style('display') !== 'none');
  if (visibleEles.length > 0) {
    cy.animate({ fit: { eles: visibleEles, padding: 80 }, duration: 400, easing: 'ease-out-cubic' });
  }

  updateBackButton();
  updateInfoBar(startNodeId);
}

// ── Event Handlers ───────────────────────────────────────────────────────────

document.getElementById('back-btn').addEventListener('click', goBack);

document.getElementById('strategy-panel-toggle').addEventListener('click', () => {
  const panel  = document.getElementById('strategy-panel');
  const toggle = document.getElementById('strategy-panel-toggle');
  const collapsed = panel.classList.toggle('collapsed');
  toggle.innerHTML = collapsed ? '&#43;' : '&#8722;';
});

const edgeTooltip = document.getElementById('edge-tooltip');

cy.on('mouseover', 'edge', (evt) => {
  const edge = evt.target;
  edge.addClass('hovered');
  const mid = edge.midpoint();
  const pan = cy.pan();
  const zoom = cy.zoom();
  const x = mid.x * zoom + pan.x;
  const y = mid.y * zoom + pan.y;
  edgeTooltip.textContent = edge.data('label');
  edgeTooltip.style.left = `${x}px`;
  edgeTooltip.style.top  = `${y}px`;
  edgeTooltip.style.color = edge.data('color');
  edgeTooltip.style.display = 'block';
});

cy.on('mouseout', 'edge', (evt) => {
  evt.target.removeClass('hovered');
  edgeTooltip.style.display = 'none';
});

cy.on('tap', 'node', (evt) => {
  const clickedNode = evt.target;
  const nodeId = parseInt(clickedNode.id(), 10);

  cy.nodes().removeClass('focused');
  clickedNode.addClass('focused');
  currentFocus = String(nodeId);

  expandBFS(nodeId);
});

init();