
// Keep the active search input mounted, including while an IME is composing.
setFilter = function (key, value) {
  state.filters[key] = value;
  if (key !== 'q') renderFilters();
  renderTable();
  renderCharts();
};
const oldRows = filteredRows;
filteredRows = function () {
  return oldRows().filter(r => !state.filters.is_overseas || r.player.is_overseas !== null);
};
const escapeText = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
renderCharts = function () {
  const d = state.data;
  const years = uniq(confirmedPlayers().map(p => p.birth_year));
  const levels = uniq(d.selections.map(s => s.national_team_level));
  // Each player contributes once per birth year; colour denotes highest recorded level.
  const highest = p => levels.filter(l => (d.selectionByPlayer[p.id] || []).some(s => s.national_team_level === l)).at(-1);
  const birth = years.map(y => ({key:y, players:confirmedPlayers().filter(p => p.birth_year === y)}));
  $('#birthYearChart').innerHTML = birth.map(b => `<div class="bar-row"><strong>${b.key}</strong><button class="bar-track" data-key="birth_year" data-value="${b.key}" title="${escapeText(b.players.map(p=>p.name).join('、'))}">${levels.map(l=>`<span class="bar-seg seg-${l}" style="width:${b.players.filter(p=>highest(p)===l).length/Math.max(1,confirmedPlayers().length)*100}%"></span>`).join('')}</button><span>${b.players.length}</span></div>`).join('') || '<p>暂无满足双证据链要求的出生年份统计。</p>';
  $('#birthYearChart').insertAdjacentHTML('beforeend','<p class="muted">仅 confirmed；每人一次，按最高已记录级别分色。</p>');
  $('#levelChart').innerHTML = levels.map(l => {
    const ids = new Set(d.selections.filter(s=>s.national_team_level===l).map(s=>s.player_id));
    const ps = d.players.filter(p=>ids.has(p.id));
    return `<div><button class="ghost-button" data-key="national_team_level" data-value="${l}" title="${escapeText(ps.map(p=>p.name).join('、'))}">${l}</button> ${statusOrder.map(s=>`${s}: ${ps.filter(p=>p.verification_status===s).length}`).join(' / ')}</div>`;
  }).join('');
  const trend = {};
  d.selections.forEach(s => {
    const p = d.players.find(p=>p.id===s.player_id);
    if (state.filters.birth_year && String(p.birth_year)!==state.filters.birth_year) return;
    if (state.filters.q && !p.name.includes(state.filters.q)) return;
    const year = s.selection_date.slice(0,4);
    (trend[year] ||= new Set()).add(s.player_id);
  });
  $('#timelineChart').innerHTML = Object.entries(trend).sort().map(([year,ids])=>`<div class="timeline-bar"><button data-key="selection_year" data-value="${year}" style="height:${40+ids.size*3}px">${ids.size}</button>${year}</div>`).join('') || '<p>无匹配记录。</p>';
  $('#timelineChart').insertAdjacentHTML('beforeend','<p class="muted">每年唯一球员数，包含待核验线索；随姓名、出生年筛选。</p>');
  document.querySelectorAll('[data-key]').forEach(el=>el.onclick=()=>setFilter(el.dataset.key,el.dataset.value));
};
const oldStats = renderStats;
renderStats = function () {
  oldStats();
  const rules = {confirmed:{verification_status:'confirmed'},by2009:{birth_year:'2009',verification_status:'confirmed'},by2010:{birth_year:'2010',verification_status:'confirmed'},u17asia:{national_team_level:'U17',verification_status:'confirmed'},pending:{verification_status:'pending'},official:{source_priority:'official_cfa'}};
  document.querySelectorAll('[data-card]').forEach(el=>{
    const replacement = el.cloneNode(true);
    el.replaceWith(replacement);
    replacement.onclick=()=>{
      Object.keys(state.filters).forEach(k=>state.filters[k]='');
      Object.assign(state.filters,rules[replacement.dataset.card]);
      renderFilters();renderTable();renderCharts();
      $('#tableSummary').scrollIntoView({block:'center'});
    };
  });
};
const oldRender = render;
render = function () {
  oldRender();
  $('#exportCsv').onclick = null;
  if (!document.querySelector('#auditNotice')) {
    $('#dataHealth').insertAdjacentHTML('afterend','<p id="auditNotice">2026-10-11 审计：历史来源尚待逐条复核。核心确认数下降反映证据标准调整，不代表球员未曾入选。已核对的新增来源为 2026 年 U17 第六期集训通知。</p>');
  }
};
