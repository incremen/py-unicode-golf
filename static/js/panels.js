function showMain(btn, id) {
  const wasActive = document.getElementById(id).classList.contains('active');
  document.querySelectorAll('.main-panel').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.main-tab').forEach(el => el.classList.remove('active'));
  if (!wasActive) {
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
    logoPop();
  }
  const onCode    = id === 'panel-code';
  const onStrings = id === 'panel-strings';
  const topWrap      = document.getElementById('topCodeWrap');
  const inputRow     = document.querySelector('.input-row');
  const resultWrap   = document.querySelector('.result-wrapper');

  const snap = h => { topWrap.style.transition = 'none'; topWrap.style.height = h + 'px'; };
  const anim = h => requestAnimationFrame(() => requestAnimationFrame(() => {
    topWrap.style.transition = ''; topWrap.style.height = h + 'px';
  }));

  const leavingCode = topWrap.offsetHeight > 0 && !onCode;
  console.log('[showMain]', { id, onCode, onStrings, leavingCode,
    topWrapOffsetH: topWrap.offsetHeight,
    topWrapStyleH: topWrap.style.height,
    topWrapScrollH: topWrap.scrollHeight });

  if (onCode) {
    // Entering exec(): measure what disappears, compensate, then animate to code height
    const comboH   = inputRow.offsetHeight + resultWrap.offsetHeight;
    const contentH = topWrap.scrollHeight;
    snap(comboH);
    inputRow.classList.add('hidden');
    resultWrap.classList.add('hidden');
    anim(contentH);
  } else if (leavingCode) {
    document.getElementById('codeInput').value = '';
    document.getElementById('codeResult').classList.remove('visible');

    inputRow.classList.remove('hidden');
    resultWrap.classList.remove('hidden');
    const comboH = inputRow.offsetHeight + resultWrap.offsetHeight;
    inputRow.classList.add('hidden');
    resultWrap.classList.add('hidden');

    console.log('[leavingCode]', {
      computedH: getComputedStyle(topWrap).height,
      offsetH: topWrap.offsetHeight,
      scrollH: topWrap.scrollHeight,
      styleH: topWrap.style.height,
      transition: topWrap.style.transition,
      comboH,
      hasText: document.getElementById('codeInput').value.length > 0
    });

    console.log('[leavingCode] calling anim, target:', comboH);
    requestAnimationFrame(() => {
      console.log('[rAF 1] height now:', topWrap.style.height, 'transition:', topWrap.style.transition);
      requestAnimationFrame(() => {
        topWrap.style.transition = '';
        topWrap.style.height = comboH + 'px';
        console.log('[rAF 2] set height to', comboH, '| computedH:', getComputedStyle(topWrap).height, '| transition:', topWrap.style.transition);
      });
    });

    const onHeightDone = e => {
      console.log('[transitionend]', { propertyName: e.propertyName, elapsedTime: e.elapsedTime, heightNow: topWrap.offsetHeight });
      if (e.propertyName !== 'height') return;
      topWrap.removeEventListener('transitionend', onHeightDone);
      snap(0);
      inputRow.classList.remove('hidden');
      resultWrap.classList.remove('hidden');
      requestAnimationFrame(() => requestAnimationFrame(() => { topWrap.style.transition = ''; }));
    };
    topWrap.addEventListener('transitionend', onHeightDone);
  } else {
    // Normal tab switch: no animation, just show/hide instantly
    inputRow.classList.toggle('hidden', false);
    resultWrap.classList.toggle('hidden', false);
  }
  if (onCode) {
    leaveStringsPanel();
    if (vizRunning) stopVisualization();
    charInput.value = '';
    charInput.classList.add('wide');
    charInput.size = 11;
    lastExpr = '';
    lastData = null;
    result.classList.remove('visible');
    vizBtn().classList.remove('visible');
  } else if (onStrings) {
    enterStringsPanel();
  } else {
    leaveStringsPanel();
  }
}

function expandTopWrap() {
  const topWrap = document.getElementById('topCodeWrap');
  if (!topWrap) return;
  requestAnimationFrame(() => requestAnimationFrame(() => {
    topWrap.style.transition = '';
    topWrap.style.height = topWrap.scrollHeight + 'px';
  }));
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
