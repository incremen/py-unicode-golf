// ── Cytoscape instance ────────────────────────────────────────────────────────

const cy = cytoscape({
  container: document.getElementById('cy'),
  userZoomingEnabled: true,
  userPanningEnabled: true,
  style: CYTOSCAPE_STYLES,
});

// ── cy event handlers ─────────────────────────────────────────────────────────

cy.on('mouseover', 'edge', (evt) => {
  const edge = evt.target;
  edge.addClass('hovered');
  const mid  = edge.midpoint();
  const pan  = cy.pan();
  const zoom = cy.zoom();
  edgeTooltip.textContent   = edge.data('label');
  edgeTooltip.style.left    = `${mid.x * zoom + pan.x}px`;
  edgeTooltip.style.top     = `${mid.y * zoom + pan.y}px`;
  edgeTooltip.style.color   = edge.data('color');
  edgeTooltip.style.display = 'block';
});

cy.on('mouseout', 'edge', (evt) => {
  evt.target.removeClass('hovered');
  edgeTooltip.style.display = 'none';
});

cy.on('tap', 'node', (evt) => {
  const clickedNode = evt.target;
  cy.nodes().removeClass('focused');
  clickedNode.addClass('focused');
  currentFocus = clickedNode.id();
  expandBFS(parseInt(clickedNode.id(), 10));
});

// ── Init ──────────────────────────────────────────────────────────────────────

function init() {
  buildStrategyChecklist();
  placeNode(0, 0, 0);
  cy.getElementById('0').addClass('focused');
  clickHistory.push('0');
  expandBFS(0).then(() => cy.center(cy.getElementById('0')));
}

init();
