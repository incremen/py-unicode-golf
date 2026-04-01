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
  const rawId       = clickedNode.id();
  const prevFocus   = currentFocus;

  cy.nodes().removeClass('focused').removeClass('trace-active');
  clickedNode.addClass('focused');
  currentFocus = rawId;

  const nodeId = rawId === 's' || rawId.startsWith('chr-') ? rawId : parseInt(rawId, 10);

  animateTraceDot(prevFocus, rawId).then(() => expandBFS(nodeId));
});

// ── Init ──────────────────────────────────────────────────────────────────────

async function initStartNode() {
  placeNode('s', 0, 0);
  cy.getElementById('s').addClass('focused');
  clickHistory.push('s');
  currentFocus = 's';
  await expandBFS('s');
  cy.center(cy.getElementById('s'));
}

function init() {
  buildStrategyChecklist();
  initStartNode();
}

init();
