function showMain(btn, id) {
  const wasActive = document.getElementById(id).classList.contains('active');
  document.querySelectorAll('.main-panel').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.main-tab').forEach(el => el.classList.remove('active'));
  if (!wasActive) {
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
    logoPop();
  }
  const onCode = id === 'panel-code';
  document.querySelector('.input-row').classList.toggle('hidden', onCode);
  document.querySelector('.result-wrapper').classList.toggle('hidden', onCode);
  if (onCode) {
    if (vizRunning) stopVisualization();
    charInput.value = '';
    charInput.classList.add('wide');
    charInput.size = stringMode ? 20 : 11;
    lastExpr = '';
    lastData = null;
    result.classList.remove('visible');

    vizBtn().classList.remove('visible');
  }
}

function loadStrategies(sortKey = 'chain_entries') {
  document.querySelectorAll('.strategy-sort-btn').forEach(b =>
    b.classList.toggle('active', b.getAttribute('onclick').includes(`'${sortKey}'`))
  );
  const sorted = [...STRATEGY_BREAKDOWN].filter(st => st.name !== 'base').sort((a, b) => b[sortKey] - a[sortKey]);
  document.getElementById('strategiesList').innerHTML = sorted.map(st =>
    `<span class="strategy-tag">${st.name} <span class="count">${st[sortKey].toLocaleString()}</span></span>`
  ).join('');
}

function loadHistory() {
  // rows ending in (depth) start a new group; rows ending in (length) are the pair's second half
  document.getElementById('historyBody').innerHTML = OPTIMIZATION_HISTORY.map(e => {
    const cls = e.label.endsWith('(depth)')  ? ' class="group-start"'
              : e.label.endsWith('(length)') ? ' class="pair-second"'
              : '';
    const label = e.label.replace(' (depth)', ' <span class="metric-tag">depth</span>')
                         .replace(' (length)', ' <span class="metric-tag">length</span>');
    return `<tr${cls}>
      <td>${label}</td>
      <td class="num">${e.avg_depth.toFixed(2)}</td>
      <td class="num">${e.max_depth}</td>
      <td class="num">${e.avg_len.toFixed(1)}</td>
      <td class="num">${e.max_len ?? '—'}</td>
    </tr>`;
  }).join('');
}

function loadDbStats() {
  document.getElementById('dTotal').textContent = DB_STATS.total.toLocaleString();
  document.getElementById('dAvgDepth').textContent = DB_STATS.avg_depth;
  document.getElementById('dMaxDepth').textContent = DB_STATS.max_depth;
  document.getElementById('dAvgLen').textContent = DB_STATS.avg_len;
}

function loadFormulaStats() {
  document.getElementById('fAvgDepth').textContent = FORMULA_STATS.avg_depth;
  document.getElementById('fMaxDepth').textContent = FORMULA_STATS.max_depth;
  document.getElementById('fAvgLen').textContent = FORMULA_STATS.avg_len;
  document.getElementById('fMaxLen').textContent = FORMULA_STATS.max_len;
}

loadHistory();
loadStrategies();
loadDbStats();
loadFormulaStats();
