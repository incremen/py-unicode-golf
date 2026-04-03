// ── Node & edge placement ─────────────────────────────────────────────────────

function placeNode(nodeId, x = 0, y = 0) {
  const id = String(nodeId);
  if (!cy.getElementById(id).length) {
    cy.add({ data: { id, label: id }, position: { x, y } });
  }
}

// Distributes neighbors into concentric rings around focusId.
// Rings grow outward; each ring's capacity is derived from its arc length so
// nodes are guaranteed at least NODE_SPACING pixels of arc between them.
// The sweep avoids the direction of parentId, leaving space for the trail edge.
function placeNeighborsRings(focusId, neighbors, parentId) {
  const focusEl  = cy.getElementById(String(focusId));
  const focusPos = focusEl.position();
  const unplaced = neighbors.filter(n => !cy.getElementById(String(n.id)).length);

  if (unplaced.length === 0) return;

  const INNER_RADIUS = 110;
  const RING_SPACING = 90;
  const NODE_SPACING = 58; // minimum arc-distance between node centres

  const parentEl = parentId ? cy.getElementById(String(parentId)) : null;
  let blockAngle  = null;
  let sweep       = 2 * Math.PI;

  if (parentEl && parentEl.length) {
    const parentPos = parentEl.position();
    blockAngle = Math.atan2(parentPos.y - focusPos.y, parentPos.x - focusPos.x);
    sweep = Math.PI * 1.33; // ~240°
  }

  let remaining = [...unplaced];
  let ringIndex  = 0;

  while (remaining.length > 0) {
    const radius      = INNER_RADIUS + ringIndex * RING_SPACING;
    const capacity    = Math.max(1, Math.floor(radius * sweep / NODE_SPACING));
    const nodesInRing = Math.min(capacity, remaining.length);
    const ringNodes   = remaining.splice(0, nodesInRing);

    const centerAngle = blockAngle !== null ? blockAngle + Math.PI : 0;
    const startAngle  = centerAngle - sweep / 2;
    const step        = nodesInRing === 1 ? 0 : sweep / (nodesInRing - 1);
    const offset      = ringIndex % 2 === 1 && nodesInRing > 1 ? step / 2 : 0;

    ringNodes.forEach((neighbor, i) => {
      const angle = nodesInRing === 1 ? centerAngle : startAngle + i * step + offset;
      placeNode(neighbor.id, focusPos.x + radius * Math.cos(angle), focusPos.y + radius * Math.sin(angle));
    });

    ringIndex++;
  }
}

function placeEdge(sourceId, targetId, strategy) {
  const edgeId = `e-${sourceId}-${targetId}-${strategy}`;
  if (!cy.getElementById(edgeId).length) {
    const labelFn = STRATEGY_LABELS[strategy];
    cy.add({
      data: {
        id: edgeId,
        source: String(sourceId),
        target: String(targetId),
        strategy,
        label: labelFn ? labelFn(sourceId, targetId) : strategy,
        color: STRATEGY_COLORS[strategy] || '#888',
      }
    });

    const targetIdStr = String(targetId);
    if (!nodeIncomingEdges.has(targetIdStr)) nodeIncomingEdges.set(targetIdStr, []);
    nodeIncomingEdges.get(targetIdStr).push(edgeId);
  }
}

function makeChrNeighbor(nodeId) {
  const codepoint   = Number(nodeId);
  const raw         = String.fromCodePoint(codepoint);
  const isPrintable = codepoint >= 32 && codepoint !== 127 && raw.trim() !== '';
  const label       = isPrintable ? raw : `\\x${codepoint.toString(16).padStart(2, '0')}`;
  return { id: `chr-${nodeId}`, label, isChr: true };
}
