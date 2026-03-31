// ── Configuration ─────────────────────────────────────────────────────────

// Ordered by number of uses in the final DB (most useful first)
const STRATEGY_COLORS = {
  decrement:        '#e74c3c',  // 57,391
  quad_plus_3:      '#5dade2',  // 29,082
  bytearray_4x:     '#f39c12',  // 21,885
  quint_plus_5:     '#1abc9c',  // 12,986
  list_range:       '#e67e22',  // 11,602
  triple:           '#2ecc71',  // 11,146
  ascii_exp_2:      '#fd79a8',  //  8,542
  dict_enum_bytes:  '#a29bfe',  //  7,303
  list_enum_bytes:  '#74b9ff',  //  7,055
  zip_range:        '#55efc4',  //  6,120
  zip_chain_1:      '#ffeaa7',  //  5,615
  dict_enum_range:  '#fab1a0',  //  5,245
  ascii_exp_3:      '#ff7675',  //  4,583
  zip_chain_2:      '#81ecec',  //  2,960
  ascii_exp_4:      '#b2bec3',  //  2,514
  zip_chain_3:      '#dfe6e9',  //  1,805
};

const VERTICAL_SPACING   = 140;
const HORIZONTAL_SPACING = 110;

const TOP_5_STRATEGIES = new Set([
  'decrement', 'quad_plus_3', 'bytearray_4x', 'quint_plus_5', 'list_range',
]);

const enabledStrategies = new Set(TOP_5_STRATEGIES);

// ── Initialization ─────────────────────────────────────────────────────────

const cy = cytoscape({
  container: document.getElementById('cy'),
  userZoomingEnabled: true,
  userPanningEnabled: true,
  style: CYTOSCAPE_STYLES,
});

const expandedNodes  = new Set();
const occupiedSlots  = new Set(); // tracks taken grid positions as "col,row" strings

function slotKey(x, y) {
  return `${Math.round(x / HORIZONTAL_SPACING)},${Math.round(y / VERTICAL_SPACING)}`;
}

const MAX_LEFT_DRIFT  = 2;
const MAX_RIGHT_DRIFT = 2;

function findFreePosition(desiredX, desiredY, parentX) {
  const baseRow    = Math.round(desiredY / VERTICAL_SPACING);
  const baseCol    = Math.round(desiredX / HORIZONTAL_SPACING);
  const parentCol  = Math.round((parentX ?? desiredX) / HORIZONTAL_SPACING);
  const minCol     = parentCol - MAX_LEFT_DRIFT;
  const maxCol     = parentCol + MAX_RIGHT_DRIFT;

  for (let rowOffset = 0; rowOffset < 20; rowOffset++) {
    const row = baseRow + rowOffset;
    for (let col = baseCol; col <= maxCol; col++) {
      if (col < minCol) continue;
      const key = `${col},${row}`;
      if (!occupiedSlots.has(key)) {
        occupiedSlots.add(key);
        return {
          x: col * HORIZONTAL_SPACING,
          y: row * VERTICAL_SPACING + (desiredY - baseRow * VERTICAL_SPACING),
        };
      }
    }
    // also try left of baseCol down to minCol
    for (let col = baseCol - 1; col >= minCol; col--) {
      const key = `${col},${row}`;
      if (!occupiedSlots.has(key)) {
        occupiedSlots.add(key);
        return {
          x: col * HORIZONTAL_SPACING,
          y: row * VERTICAL_SPACING + (desiredY - baseRow * VERTICAL_SPACING),
        };
      }
    }
  }
  return { x: desiredX, y: desiredY };
}

function placeNode(nodeId, x, y, parentX) {
  const id = String(nodeId);
  if (!cy.getElementById(id).length) {
    const pos = findFreePosition(x, y, parentX);
    cy.add({ data: { id, label: id }, position: pos });
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
    if (!enabledStrategies.has(strategy)) {
      edge.style('display', 'none');
    }
  }
}

function buildStrategyChecklist() {
  const panel = document.getElementById('strategy-panel');
  for (const strategy of Object.keys(STRATEGY_COLORS)) {
    const isChecked = enabledStrategies.has(strategy);
    const row = document.createElement('label');
    row.className = 'strategy-row';

    const checkbox = document.createElement('input');
    checkbox.type    = 'checkbox';
    checkbox.checked = isChecked;
    checkbox.addEventListener('change', () => toggleStrategy(strategy, checkbox.checked));

    const dot = document.createElement('span');
    dot.className        = 'strategy-color-dot';
    dot.style.background = STRATEGY_COLORS[strategy];

    const label = document.createElement('span');
    label.className   = 'strategy-label';
    label.textContent = strategy;

    row.appendChild(checkbox);
    row.appendChild(dot);
    row.appendChild(label);
    panel.appendChild(row);
  }
}

function toggleStrategy(strategy, enabled) {
  if (enabled) {
    enabledStrategies.add(strategy);
    cy.edges(`[strategy = "${strategy}"]`).style('display', 'element');
  } else {
    enabledStrategies.delete(strategy);
    cy.edges(`[strategy = "${strategy}"]`).style('display', 'none');
  }
  cy.edges(`[strategy = "${strategy}"]`).forEach(edge => {
    updateNodeVisibility(edge.target().id());
  });
}

function placeNeighborsBelow(focusId, neighbors) {
  const focusEl    = cy.getElementById(String(focusId));
  const focusPos   = focusEl.position();
  const unplaced   = neighbors.filter(neighbor => !cy.getElementById(String(neighbor.id)).length);
  const totalWidth = (unplaced.length - 1) * HORIZONTAL_SPACING;
  const startX     = focusPos.x - totalWidth / 2;
  const targetY    = focusPos.y + VERTICAL_SPACING;

  unplaced.forEach((neighbor, index) => {
    placeNode(neighbor.id, startX + index * HORIZONTAL_SPACING, targetY, focusPos.x);
  });

  return unplaced.map(neighbor => String(neighbor.id));
}

function updateNodeVisibility(nodeId) {
  const nodeEl = cy.getElementById(String(nodeId));
  if (expandedNodes.has(String(nodeId))) {
    nodeEl.style('display', 'element');
    return;
  }
  const hasVisibleEdge = nodeEl.incomers('edge').filter(edge => !edge.hidden()).length > 0;
  nodeEl.style('display', hasVisibleEdge ? 'element' : 'none');
}

function updateInfoBar(focusId, neighborCount) {
  document.getElementById('info').textContent =
    `node ${focusId}  →  ${neighborCount} neighbors  |  ${expandedNodes.size} expanded total`;
}

async function expandNode(nodeId) {
  const id = String(nodeId);
  if (expandedNodes.has(id)) return;
  expandedNodes.add(id);

  const response = await fetch(`/api/neighbors/${nodeId}`);
  const data     = await response.json();

  cy.getElementById(id).addClass('expanded');

  const newNodeIds = placeNeighborsBelow(data.focus, data.neighbors);

  for (const neighbor of data.neighbors) {
    placeEdge(data.focus, neighbor.id, neighbor.strategy);
  }

  for (const neighbor of data.neighbors) {
    updateNodeVisibility(neighbor.id);
  }

  const newVisible = newNodeIds
    .map(nodeId => cy.getElementById(nodeId))
    .filter(nodeEl => !nodeEl.hidden());
  if (newVisible.length > 0) {
    cy.animate({ center: { eles: cy.collection(newVisible) }, duration: 400, easing: 'ease-in-out-quad' });
  }

  updateInfoBar(data.focus, data.neighbors.length);
}

cy.on('tap', 'node', function(evt) {
  cy.nodes().removeClass('focused');
  evt.target.addClass('focused');
  expandNode(parseInt(evt.target.id(), 10));
});

function init() {
  buildStrategyChecklist();
  const startX = window.innerWidth / 2;
  const startY = 80;
  occupiedSlots.add(slotKey(startX, startY));
  placeNode(0, startX, startY);
  cy.nodes().first().addClass('focused');
  expandNode(0);
}

init();
