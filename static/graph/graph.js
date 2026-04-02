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

const charPopup = document.getElementById('char-popup');

cy.on('mouseover', 'node', (evt) => {
  const node  = evt.target;
  const rawId = node.id();
  if (!rawId.startsWith('chr-')) return;

  const codepoint = parseInt(rawId.slice(4), 10);
  const pos  = node.renderedPosition();
  const rect = document.getElementById('cy').getBoundingClientRect();
  charPopup.style.left    = `${rect.left + pos.x}px`;
  charPopup.style.top     = `${rect.top  + pos.y}px`;
  charPopup.style.display = 'block';
  charPopup.innerHTML     = '<span class="char-name">loading…</span>';

  fetch(`/api/char/${encodeURIComponent(String.fromCodePoint(codepoint))}`)
    .then(r => r.json())
    .then(data => {
      charPopup.innerHTML = `
        <span class="char-glyph">${data.char}</span>
        <span class="char-name">${data.name ?? 'no name'}</span>
        U+${data.code_point.toString(16).toUpperCase().padStart(4, '0')}
        <br>depth ${data.formula?.depth ?? '?'} &nbsp; len ${data.formula?.len ?? '?'}
      `;
    });
});

cy.on('mouseout', 'node', (evt) => {
  if (evt.target.id().startsWith('chr-')) charPopup.style.display = 'none';
});

cy.on('tap', 'node', (evt) => {
  const clickedNode = evt.target;
  const rawId       = clickedNode.id();

  if (rawId.startsWith('chr-')) {
    navigator.clipboard.writeText(String.fromCodePoint(parseInt(rawId.slice(4), 10)));
    playStrategyNote('chr');
    return;
  }

  const prevFocus = currentFocus;
  cy.nodes().removeClass('focused').removeClass('trace-active');
  clickedNode.addClass('focused');
  currentFocus = rawId;

  const connectingEdge = cy.edges(`[source="${prevFocus}"][target="${rawId}"]`).first();
  const edgeStrategy   = connectingEdge.length ? connectingEdge.data('strategy') : null;

  const nodeId = rawId === 's' ? rawId : parseInt(rawId, 10);
  animateTraceDot(prevFocus, rawId, edgeStrategy).then(() => expandBFS(nodeId));
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
