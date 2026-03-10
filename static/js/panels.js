function showMain(btn, id) {
  const wasActive = document.getElementById(id).classList.contains('active');
  document.querySelectorAll('.main-panel').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.main-tab').forEach(el => el.classList.remove('active'));
  if (!wasActive) {
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
    logoPop();
  }
}

function loadStrategies() {
  document.getElementById('strategiesList').innerHTML = STRATEGY_BREAKDOWN.map(st =>
    `<span class="strategy-tag tip">${st.name} <span class="count">${st.count.toLocaleString()}</span>` +
    `<span class="tiptext">${st.count.toLocaleString()} numbers use ${st.name} (avg depth ${st.avg_depth})</span></span>`
  ).join('');
}

function loadHistory() {
  document.getElementById('historyBody').innerHTML = OPTIMIZATION_HISTORY.map(e => `
    <tr>
      <td>${e.label}</td>
      <td class="num">${e.avg_depth}</td>
      <td class="num">${e.max_depth}</td>
      <td class="num">${e.avg_len.toLocaleString()}</td>
    </tr>
  `).join('');
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
