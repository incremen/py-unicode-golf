// ── Path tracing ─────────────────────────────────────────────────────────────

function resetGraph() {
  cy.elements().remove();
  expandedNodes.clear();
  nodeIncomingEdges.clear();
  clickHistory.length = 0;
  placedByExpansion.clear();
  evictionStack.length = 0;
  currentFocus = '0';
  updateBackButton();
}

function animateTraceDot(fromId, toId) {
  return new Promise(resolve => {
    const fromEl = cy.getElementById(String(fromId));
    const toEl   = cy.getElementById(String(toId));
    if (!fromEl.length || !toEl.length) { resolve(); return; }

    const container = document.getElementById('cy').getBoundingClientRect();
    const fromPos   = fromEl.renderedPosition();
    const toPos     = toEl.renderedPosition();

    const dot = document.createElement('div');
    dot.className     = 'trace-dot';
    dot.style.left    = `${container.left + fromPos.x}px`;
    dot.style.top     = `${container.top  + fromPos.y}px`;
    document.body.appendChild(dot);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        dot.style.transition = `left ${TRACE_ANIM_MS}ms ease-in-out, top ${TRACE_ANIM_MS}ms ease-in-out`;
        dot.style.left = `${container.left + toPos.x}px`;
        dot.style.top  = `${container.top  + toPos.y}px`;
      });
    });

    setTimeout(() => { dot.remove(); resolve(); }, TRACE_ANIM_MS + 50);
  });
}

async function tracePath(target) {
  const response = await fetch(`/api/path/${encodeURIComponent(target)}`);
  if (!response.ok && response.headers.get('content-type')?.includes('text/html')) {
    document.getElementById('trace-error').textContent = `Server error (${response.status})`;
    return;
  }
  const data = await response.json();

  if (data.error) {
    document.getElementById('trace-error').textContent = data.error;
    return;
  }
  document.getElementById('trace-error').textContent = '';

  resetGraph();
  await initStartNode();

  let prevId = 's';
  for (const nodeId of data.path) {
    const id = String(nodeId);

    // Dwell on the current node before moving
    await new Promise(resolve => setTimeout(resolve, TRACE_STEP_MS - TRACE_ANIM_MS - 50));

    // Animate dot traveling to the next node
    await animateTraceDot(prevId, id);

    // Expand and highlight the new node
    cy.nodes().removeClass('focused').removeClass('trace-active');
    const nodeEl = cy.getElementById(id);
    if (nodeEl.length) nodeEl.addClass('trace-active');

    currentFocus = id;
    await expandBFS(nodeId);

    prevId = id;
  }

  // Leave the final node highlighted
  cy.nodes().removeClass('focused');
  cy.getElementById(prevId).addClass('trace-active');
}

// ── Node expansion ────────────────────────────────────────────────────────────

async function expandNode(nodeId, parentId = null) {
  const id = String(nodeId);
  if (expandedNodes.has(id)) return [];

  expandedNodes.add(id);

  const response = await fetch(`/api/neighbors/${nodeId}`);
  const data     = await response.json();

  cy.getElementById(id).addClass('expanded');

  // 's' is the virtual start node — no chr leaf, no integer transform
  const isStartNode  = id === 's';
  const chrNeighbor  = isStartNode ? null : makeChrNeighbor(nodeId);
  const allNeighbors = chrNeighbor ? [...data.neighbors, chrNeighbor] : data.neighbors;

  const beforeIds = new Set(cy.nodes().map(node => node.id()));
  placeNeighborsRings(data.focus, allNeighbors, parentId);

  if (chrNeighbor) {
    const chrEl = cy.getElementById(chrNeighbor.id);
    if (chrEl.length) chrEl.addClass('chr-node').data('label', chrNeighbor.label);
  }

  const placed = new Set(cy.nodes().filter(node => !beforeIds.has(node.id())).map(node => node.id()));
  placedByExpansion.set(id, placed);

  data.neighbors.forEach(neighbor => placeEdge(data.focus, neighbor.id, neighbor.strategy));

  if (chrNeighbor) {
    const chrEdgeId = `e-${nodeId}-${chrNeighbor.id}-chr`;
    if (!cy.getElementById(chrEdgeId).length) {
      cy.add({ data: {
        id: chrEdgeId,
        source: id,
        target: chrNeighbor.id,
        strategy: 'chr',
        label: STRATEGY_LABELS.chr(nodeId),
        color: STRATEGY_COLORS.chr,
      }});
      if (!nodeIncomingEdges.has(chrNeighbor.id)) nodeIncomingEdges.set(chrNeighbor.id, []);
      nodeIncomingEdges.get(chrNeighbor.id).push(chrEdgeId);
    }
  }

  refreshEdgeVisibility();
  refreshNodeVisibility();

  return data.neighbors.map(neighbor => neighbor.id);
}

// ── History management ────────────────────────────────────────────────────────

function evictOldest() {
  const evicted    = clickHistory.shift();
  const evictedPos = cy.getElementById(evicted).position();
  expandedNodes.delete(evicted);
  evictionStack.push({ id: evicted, pos: { x: evictedPos.x, y: evictedPos.y } });

  const needed = new Set(clickHistory);
  clickHistory.forEach(id => {
    (placedByExpansion.get(id) || new Set()).forEach(nodeId => needed.add(nodeId));
  });

  cy.nodes().forEach(node => {
    if (!needed.has(node.id())) {
      nodeIncomingEdges.delete(node.id());
      node.remove();
    }
  });
  placedByExpansion.delete(evicted);
}

async function goBack() {
  if (clickHistory.length <= 1) return;

  const removed        = clickHistory.pop();
  const placedByRemoved = placedByExpansion.get(removed) || new Set();
  expandedNodes.delete(removed);

  const stillNeeded = new Set(clickHistory);
  clickHistory.forEach(id => {
    (placedByExpansion.get(id) || new Set()).forEach(nodeId => stillNeeded.add(nodeId));
  });

  placedByRemoved.forEach(nodeId => {
    if (!stillNeeded.has(nodeId)) {
      nodeIncomingEdges.delete(nodeId);
      cy.getElementById(nodeId).remove();
    }
  });
  placedByExpansion.delete(removed);

  if (evictionStack.length > 0) {
    const { id: restored, pos } = evictionStack.pop();
    clickHistory.unshift(restored);
    placeNode(restored, pos.x, pos.y);
    await expandNode(restored, null);
  }

  currentFocus = clickHistory[clickHistory.length - 1];
  cy.nodes().removeClass('focused');
  cy.getElementById(currentFocus).addClass('focused');

  refreshEdgeVisibility();
  refreshNodeVisibility();
  updateBackButton();

  const visibleEles = cy.elements().filter(ele => ele.style('display') !== 'none');
  if (visibleEles.length > 0) {
    cy.animate({ fit: { eles: visibleEles, padding: 80 }, duration: 400, easing: 'ease-out-cubic' });
  }
  updateInfoBar(currentFocus);
}

async function expandBFS(startNodeId, depth = BFS_DEPTH) {
  const id = String(startNodeId);

  let parentId = null;
  if (!clickHistory.includes(id)) {
    parentId = clickHistory.length > 0 ? clickHistory[clickHistory.length - 1] : null;
    clickHistory.push(id);
    if (clickHistory.length > MAX_CLICK_HISTORY) evictOldest();
  }

  let currentLevel = [startNodeId];
  for (let level = 0; level < depth; level++) {
    const unexpanded = currentLevel.filter(nodeId => !expandedNodes.has(String(nodeId)));
    if (unexpanded.length === 0) break;

    const results = await Promise.all(unexpanded.map(nodeId => expandNode(nodeId, parentId)));
    currentLevel = [...new Set(results.flat())];
  }

  const visibleEles = cy.elements().filter(ele => ele.style('display') !== 'none');
  if (visibleEles.length > 0) {
    cy.animate({ fit: { eles: visibleEles, padding: 80 }, duration: 400, easing: 'ease-out-cubic' });
  }

  updateBackButton();
  updateInfoBar(startNodeId);
}
