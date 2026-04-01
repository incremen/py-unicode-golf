// ── Visibility ────────────────────────────────────────────────────────────────

// An edge is visible if its strategy is enabled AND it either leaves the current
// focus node or connects two nodes on the history trail.
function refreshEdgeVisibility() {
  const historySet = new Set(clickHistory);
  cy.edges().forEach(edge => {
    const source     = edge.data('source');
    const target     = edge.data('target');
    const strategyOn = enabledStrategies.has(edge.data('strategy'));
    const fromFocus  = source === currentFocus;
    const isTailEdge = historySet.has(source) && historySet.has(target);
    edge.style('display', strategyOn && (fromFocus || isTailEdge) ? 'element' : 'none');
  });
}

// History nodes are always visible. Others require a visible incoming edge.
function refreshNodeVisibility() {
  cy.nodes().forEach(node => {
    const id = node.id();
    if (clickHistory.includes(id)) {
      node.style('display', 'element');
      return;
    }
    const edges = nodeIncomingEdges.get(id) || [];
    const visible = edges.some(edgeId => cy.getElementById(edgeId).style('display') !== 'none');
    node.style('display', visible ? 'element' : 'none');
  });
}

// ── Strategy panel ────────────────────────────────────────────────────────────

function buildStrategyChecklist() {
  const panel = document.getElementById('strategy-panel');
  if (!panel) return;

  Object.keys(STRATEGY_COLORS).forEach(strategy => {
    const row = document.createElement('label');
    row.className = 'strategy-row';

    const checkbox = document.createElement('input');
    checkbox.type    = 'checkbox';
    checkbox.checked = enabledStrategies.has(strategy);
    checkbox.addEventListener('change', () => toggleStrategy(strategy, checkbox.checked));

    const colorDot = document.createElement('span');
    colorDot.className        = 'strategy-color-dot';
    colorDot.style.background = STRATEGY_COLORS[strategy];

    const textLabel = document.createElement('span');
    textLabel.className   = 'strategy-label';
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

// ── Info / back button ────────────────────────────────────────────────────────

function updateInfoBar(focusId) {
  const infoBar = document.getElementById('info');
  if (infoBar) {
    infoBar.textContent = `node ${focusId} | ${expandedNodes.size} expanded total`;
  }
}

function updateBackButton() {
  document.getElementById('back-btn').disabled = clickHistory.length <= 1;
}

// ── DOM event listeners ───────────────────────────────────────────────────────

document.getElementById('back-btn').addEventListener('click', () => goBack());

document.getElementById('strategy-panel-toggle').addEventListener('click', () => {
  const panel    = document.getElementById('strategy-panel');
  const toggle   = document.getElementById('strategy-panel-toggle');
  const collapsed = panel.classList.toggle('collapsed');
  toggle.innerHTML = collapsed ? '&#43;' : '&#8722;';
});

// Exposed so graph.js can bind the cy edge-hover events.
const edgeTooltip = document.getElementById('edge-tooltip');
