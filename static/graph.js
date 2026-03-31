const STRATEGY_COLORS = {
  decrement:        '#e74c3c',
  quad_plus_3:      '#5dade2',
  bytearray_4x:     '#f39c12',
  quint_plus_5:     '#1abc9c',
  list_range:       '#e67e22',
  triple:           '#2ecc71',
  ascii_exp_2:      '#fd79a8',
  dict_enum_bytes:  '#a29bfe',
  list_enum_bytes:  '#74b9ff',
  zip_range:        '#55efc4',
  zip_chain_1:      '#ffeaa7',
  dict_enum_range:  '#fab1a0',
  ascii_exp_3:      '#ff7675',
  zip_chain_2:      '#81ecec',
  ascii_exp_4:      '#b2bec3',
  zip_chain_3:      '#dfe6e9',
};

// Layout Constants
const BFS_DEPTH         = 1;
const MAX_CLICK_HISTORY = 9;

const TOP_5_STRATEGIES = new Set([
  'decrement', 'quad_plus_3', 'bytearray_4x', 'quint_plus_5', 'list_range',
]);

// const enabledStrategies = new Set(TOP_5_STRATEGIES);
const enabledStrategies = new Set(Object.keys(STRATEGY_COLORS));

const expandedNodes     = new Set();
const nodeIncomingEdges = new Map(); // nodeId -> [edgeId, ...]
const clickHistory      = [];        // oldest-first list of clicked nodeIds
const placedByExpansion = new Map(); // expandedNodeId -> Set of nodeIds it placed
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
    cy.add({
      data: {
        id: edgeId,
        source: String(sourceId),
        target: String(targetId),
        strategy: strategy,
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
async function expandNode(nodeId, parentId = null) {
  const id = String(nodeId);
  if (expandedNodes.has(id)) return [];

  expandedNodes.add(id);

  const response = await fetch(`/api/neighbors/${nodeId}`);
  const data     = await response.json();

  cy.getElementById(id).addClass('expanded');

  const beforeIds = new Set(cy.nodes().map(node => node.id()));
  placeNeighborsRings(data.focus, data.neighbors, parentId);
  const placed = new Set(cy.nodes().filter(node => !beforeIds.has(node.id())).map(node => node.id()));
  placedByExpansion.set(id, placed);

  data.neighbors.forEach(neighbor => placeEdge(data.focus, neighbor.id, neighbor.strategy));
  refreshEdgeVisibility();
  refreshNodeVisibility();

  return data.neighbors.map(neighbor => neighbor.id);
}

function evictOldest() {
  const evicted = clickHistory.shift();
  expandedNodes.delete(evicted);

  // Compute which nodes are still needed by the remaining history
  const needed = new Set(clickHistory);
  clickHistory.forEach(id => {
    (placedByExpansion.get(id) || new Set()).forEach(nodeId => needed.add(nodeId));
  });

  // Remove nodes no longer needed
  cy.nodes().forEach(node => {
    if (!needed.has(node.id())) {
      nodeIncomingEdges.delete(node.id());
      node.remove();
    }
  });
  placedByExpansion.delete(evicted);
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

  updateInfoBar(startNodeId);
}

// ── Event Handlers ───────────────────────────────────────────────────────────

cy.on('tap', 'node', (evt) => {
  const clickedNode = evt.target;
  const nodeId = parseInt(clickedNode.id(), 10);

  cy.nodes().removeClass('focused');
  clickedNode.addClass('focused');
  currentFocus = String(nodeId);

  expandBFS(nodeId);
});

init();