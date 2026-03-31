// ── Configuration ─────────────────────────────────────────────────────────

const STRATEGY_COLORS = {
  decrement:        '#e74c3c',
  triple:           '#2ecc71',
  quad_plus_3:      '#5dade2',
  triangular:       '#9b59b6',
  bytearray_4x:     '#f39c12',
  quint_plus_5:     '#1abc9c',
  list_range:       '#e67e22',
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

const expandedNodes = new Set();

function placeNode(nodeId, x, y) {
  const id = String(nodeId);
  if (!cy.getElementById(id).length) {
    cy.add({ data: { id, label: id }, position: { x, y } });
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
}

function placeNeighborsBelow(focusId, neighbors) {
  const focusEl  = cy.getElementById(String(focusId));
  const focusPos = focusEl.position();

  const unplaced   = neighbors.filter(neighbor => !cy.getElementById(String(neighbor.id)).length);
  const totalWidth = (unplaced.length - 1) * HORIZONTAL_SPACING;
  const startX     = focusPos.x - totalWidth / 2;
  const targetY    = focusPos.y + VERTICAL_SPACING;

  unplaced.forEach((neighbor, index) => {
    placeNode(neighbor.id, startX + index * HORIZONTAL_SPACING, targetY);
  });

  if (unplaced.length > 0) {
    const newEles = cy.collection(unplaced.map(neighbor => cy.getElementById(String(neighbor.id))));
    cy.animate({ center: { eles: newEles }, duration: 400, easing: 'ease-in-out-quad' });
  }
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

  placeNeighborsBelow(data.focus, data.neighbors);

  for (const neighbor of data.neighbors) {
    placeEdge(data.focus, neighbor.id, neighbor.strategy);
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
  placeNode(0, window.innerWidth / 2, 80);
  cy.nodes().first().addClass('focused');
  expandNode(0);
}

init();
