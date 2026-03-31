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

function placeNode(nodeId) {
  const id = String(nodeId);
  if (!cy.getElementById(id).length) {
    cy.add({ data: { id, label: id }, position: { x: 0, y: 0 } });
  }
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
async function expandNode(nodeId) {
  const id = String(nodeId);
  if (expandedNodes.has(id)) return [];

  expandedNodes.add(id);

  const response = await fetch(`/api/neighbors/${nodeId}`);
  const data     = await response.json();

  cy.getElementById(id).addClass('expanded');

  const beforeIds = new Set(cy.nodes().map(node => node.id()));
  data.neighbors.forEach(neighbor => placeNode(neighbor.id));
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

  if (!clickHistory.includes(id)) {
    clickHistory.push(id);
    if (clickHistory.length > MAX_CLICK_HISTORY) {
      evictOldest();
    }
  }

  let currentLevel = [startNodeId];
  for (let level = 0; level < depth; level++) {
    const unexpanded = currentLevel.filter(nodeId => !expandedNodes.has(String(nodeId)));
    if (unexpanded.length === 0) break;

    const nextLevelResults = await Promise.all(unexpanded.map(nodeId => expandNode(nodeId)));
    currentLevel = [...new Set(nextLevelResults.flat())];
  }

// Run the layout silently first (animate: false)
const layout = cy.elements().layout({
  name: 'breadthfirst',
  directed: true,
  spacingFactor: 1.5,
  roots: cy.getElementById(clickHistory[0]),
  animate: false // Turn off native animation so we can intercept the coordinates
});

layout.promiseOn('layoutstop').then(() => {
  // 1. Inject the "Wobble" to force angled edges
  let toggle = 1;
  const WOBBLE_AMOUNT = 45; // Pixels to push left/right
  
  // Sort history so we wobble down the line sequentially
  cy.nodes().forEach(node => {
    const id = node.id();
    // Apply the alternating zig-zag primarily to the main history trail
    if (clickHistory.includes(id)) {
      const pos = node.position();
      node.position({ x: pos.x + (toggle * WOBBLE_AMOUNT), y: pos.y });
      toggle *= -1; // Flip direction for the next node
    }
  });

  const visibleEles = cy.elements().filter(ele => ele.style('display') !== 'none');
  
  // 2. Now manually animate the camera to the new angled layout
  if (visibleEles.length > 0) {
    cy.animate({ 
      fit: { eles: visibleEles, padding: 80 }, 
      duration: 400, 
      easing: 'ease-out-cubic' 
    });
  }
});

layout.run();

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