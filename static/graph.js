const STRATEGY_COLORS = {
  decrement:    '#e74c3c',
  triple:       '#2ecc71',
  quad_plus_3:  '#5dade2',
  triangular:   '#9b59b6',
  bytearray_4x: '#f39c12',
};

const VERTICAL_SPACING   = 140;
const HORIZONTAL_SPACING = 110;

const cy = cytoscape({
  container: document.getElementById('cy'),
  userZoomingEnabled: true,
  userPanningEnabled: true,
  style: [
    {
      selector: 'node',
      style: {
        'background-color': '#2c3e50',
        'border-color': '#4a5568',
        'border-width': 2,
        'color': 'white',
        'label': 'data(label)',
        'font-family': 'Courier New',
        'font-size': '13px',
        'text-valign': 'center',
        'text-halign': 'center',
        'width': 46,
        'height': 46,
      }
    },
    {
      selector: 'node.expanded',
      style: { 'border-color': '#2ecc71', 'border-width': 3 }
    },
    {
      selector: 'node.focused',
      style: { 'background-color': '#1a3a5c', 'border-color': '#5dade2', 'border-width': 3 }
    },
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': 'data(color)',
        'target-arrow-color': 'data(color)',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(strategy)',
        'font-family': 'Courier New',
        'font-size': '9px',
        'color': 'data(color)',
        'text-background-color': '#12151e',
        'text-background-opacity': 0.85,
        'text-background-padding': '2px',
      }
    }
  ]
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
    cy.add({
      data: {
        id: edgeId,
        source: String(sourceId),
        target: String(targetId),
        strategy: strategy,
        color: STRATEGY_COLORS[strategy] || '#888',
      }
    });
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

  cy.animate({ fit: { eles: cy.nodes(), padding: 60 }, duration: 400, easing: 'ease-in-out-quad' });
  updateInfoBar(data.focus, data.neighbors.length);
}

cy.on('tap', 'node', function(evt) {
  cy.nodes().removeClass('focused');
  evt.target.addClass('focused');
  expandNode(parseInt(evt.target.id(), 10));
});

function init() {
  placeNode(0, window.innerWidth / 2, 80);
  cy.nodes().first().addClass('focused');
  expandNode(0);
}

init();
