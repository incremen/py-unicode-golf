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
const RADIAL_DISTANCE = 120;      // Physical distance between "generations"
const SWEEP_ANGLE     = Math.PI / 1.5; // 120-degree splay for neighbors
const BFS_DEPTH       = 1;

const TOP_5_STRATEGIES = new Set([
  'decrement', 'quad_plus_3', 'bytearray_4x', 'quint_plus_5', 'list_range',
]);

const enabledStrategies = new Set(TOP_5_STRATEGIES);
const expandedNodes     = new Set();

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

  // Seed the graph at the origin
  placeNode(0, 0, 0);
  const rootNode = cy.getElementById('0');
  rootNode.addClass('focused');
  
  expandBFS(0);
}

// ── Graph Construction ───────────────────────────────────────────────────────

function placeNode(nodeId, x, y) {
  const id = String(nodeId);
  if (!cy.getElementById(id).length) {
    cy.add({ 
      data: { id, label: id }, 
      position: { x, y } 
    });
  }
}

function placeEdge(sourceId, targetId, strategy) {
  const edgeId = `e-${sourceId}-${targetId}-${strategy}`;
  if (!cy.getElementById(edgeId).length) {
    const edge = cy.add({
      data: {
        id: edgeId,
        source: String(sourceId),
        target: String(targetId),
        strategy: strategy,
        color: STRATEGY_COLORS[strategy] || '#888',
      }
    });
    
    // Set initial visibility based on strategy checklist
    if (!enabledStrategies.has(strategy)) {
      edge.style('display', 'none');
    }
  }
}

/**
 * Computes radial positions for neighbors so they point outward from the focus node.
 */
function placeNeighborsRadial(focusId, neighbors) {
  const focusEl  = cy.getElementById(String(focusId));
  const focusPos = focusEl.position();
  const unplaced = neighbors.filter(neighbor => !cy.getElementById(String(neighbor.id)).length);

  if (unplaced.length === 0) return;

  // Vector from origin (0,0) to focus node
  const radius = Math.sqrt(focusPos.x ** 2 + focusPos.y ** 2);
  const angle  = Math.atan2(focusPos.y, focusPos.x);

  const nextRadius = radius + RADIAL_DISTANCE;

  unplaced.forEach((neighbor, index) => {
    let targetAngle;

    if (radius === 0) {
      // Root node (0,0) explodes neighbors in a full circle
      targetAngle = (index / unplaced.length) * (Math.PI * 2);
    } else {
      // Neighbors splay outward in a "cone" centered on the parent's current angle
      const spread = (unplaced.length === 1) ? 0 : SWEEP_ANGLE;
      const startAngle = angle - spread / 2;
      const step = (unplaced.length === 1) ? 0 : spread / (unplaced.length - 1);
      targetAngle = startAngle + index * step;
    }

    const x = nextRadius * Math.cos(targetAngle);
    const y = nextRadius * Math.sin(targetAngle);

    placeNode(neighbor.id, x, y);
  });
}

// ── Visibility & UI ──────────────────────────────────────────────────────────

function updateNodeVisibility(nodeId) {
  const nodeEl = cy.getElementById(String(nodeId));
  
  // Always show expanded nodes
  if (expandedNodes.has(String(nodeId))) {
    nodeEl.style('display', 'element');
    return;
  }
  
  // Hide fringe nodes if they have no visible incoming edges
  const hasVisibleIncomers = nodeEl.incomers('edge').filter(edge => !edge.hidden()).length > 0;
  nodeEl.style('display', hasVisibleIncomers ? 'element' : 'none');
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
    cy.edges(`[strategy = "${strategy}"]`).style('display', 'element');
  } else {
    enabledStrategies.delete(strategy);
    cy.edges(`[strategy = "${strategy}"]`).style('display', 'none');
  }

  // Update visibility for all target nodes affected by this toggle
  cy.edges(`[strategy = "${strategy}"]`).forEach(edge => {
    updateNodeVisibility(edge.target().id());
  });
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

  const focusNode = cy.getElementById(id);
  focusNode.addClass('expanded');

  // Place neighbors in radial cone
  placeNeighborsRadial(data.focus, data.neighbors);

  // Add edges and update neighbor visibility
  data.neighbors.forEach(neighbor => {
    placeEdge(data.focus, neighbor.id, neighbor.strategy);
    updateNodeVisibility(neighbor.id);
  });

  return data.neighbors.map(neighbor => neighbor.id);
}

/**
 * Expands a node and its descendants up to a certain depth.
 */
async function expandBFS(startNodeId, depth = BFS_DEPTH) {
  let currentLevel = [startNodeId];

  for (let level = 0; level < depth; level++) {
    const unexpanded = currentLevel.filter(id => !expandedNodes.has(String(id)));
    if (unexpanded.length === 0) break;

    const nextLevelResults = await Promise.all(unexpanded.map(id => expandNode(id)));
    currentLevel = [...new Set(nextLevelResults.flat())];
  }

  const visibleElements = cy.elements().filter(element => !element.hidden());
  if (visibleElements.length > 0) {
    cy.animate({ 
      center: { eles: visibleElements }, 
      duration: 500, 
      easing: 'ease-in-out-cubic' 
    });
  }

  updateInfoBar(startNodeId);
}

// ── Event Handlers ───────────────────────────────────────────────────────────

cy.on('tap', 'node', (evt) => {
  const clickedNode = evt.target;
  const nodeId = parseInt(clickedNode.id(), 10);

  cy.nodes().removeClass('focused');
  clickedNode.addClass('focused');
  
  expandBFS(nodeId);
});

init();