(async function () {
  const root = document.body.dataset.root || '';
  const container = document.querySelector('#matchRecords');
  const esc = x => String(x ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const known = x => x === null || x === undefined ? '未披露' : esc(x);
  try {
    const [matches, apps, players, sources] = await Promise.all(['matches','appearances','players','sources'].map(async n => {
      const response = await fetch(`${root}data/${n}.json?v=${document.body.dataset.release}`);
      if (!response.ok) throw new Error('无法载入比赛数据');
      return response.json();
    }));
    const slug = document.querySelector('[data-player-slug]')?.dataset.playerSlug;
    const ps = Object.fromEntries(players.map(p=>[p.id,p]));
    const ms = Object.fromEntries(matches.map(m=>[m.id,m]));
    const ss = Object.fromEntries(sources.map(s=>[s.id,s]));
    const rows = apps.filter(a=>!slug || ps[a.player_id]?.slug===slug);
    container.innerHTML = `<h2>国内外比赛记录</h2><p>已核验战报覆盖部分场次，未列出不代表未参赛。地点与赛事性质分别记录；未知数据不计为零。日期沿用来源口径，比分以代表队为前者。俱乐部记录不计为国字号入选。</p><div class="filters"><label>代表队类型<select id="matchTeam"><option value="">全部</option><option value="national">国家队</option><option value="club">俱乐部</option></select></label><label>球员姓名<input id="matchName" placeholder="搜索球员"></label><label>比赛地点<select id="matchLocation"><option value="">全部</option><option>境内</option><option>境外</option></select></label><label>赛事性质<select id="matchType"><option value="">全部</option>${[...new Set(matches.map(m=>m.competition_type))].map(x=>`<option>${esc(x)}</option>`).join('')}</select></label></div><p id="matchCount" aria-live="polite"></p><div class="table-wrap"><table><thead><tr>${['球员','日期','赛事 / 阶段','代表队','对手 / 比分','地点','性质','参赛情况','首发','分钟','进球','助攻','依据 / 备注'].map(x=>`<th>${x}</th>`).join('')}</tr></thead><tbody id="matchRows"></tbody></table></div>`;
    function render() {
      const filtered = rows.filter(a=>{
        const m=ms[a.match_id];
        return ps[a.player_id].name.includes(document.querySelector('#matchName').value) && (!document.querySelector('#matchTeam').value || m.team_type===document.querySelector('#matchTeam').value) && (!document.querySelector('#matchLocation').value || m.location_scope===document.querySelector('#matchLocation').value) && (!document.querySelector('#matchType').value || m.competition_type===document.querySelector('#matchType').value);
      });
      document.querySelector('#matchCount').textContent=`${new Set(filtered.map(a=>a.player_id)).size} 名球员 · ${new Set(filtered.map(a=>a.match_id)).size} 场比赛 · ${filtered.length} 条个人记录`;
      document.querySelector('#matchRows').innerHTML=filtered.map(a=>{const p=ps[a.player_id],m=ms[a.match_id],s=ss[a.source_id];return `<tr><td><a href="${root}players/${p.slug}/">${esc(p.name)}</a></td><td>${m.match_date}<br><small>${esc(m.date_basis || m.date_timezone || '时区待核验')}</small></td><td>${esc(m.competition)} / ${esc(m.stage)}</td><td>${esc(m.team)}</td><td>${esc(m.opponent)} / ${esc(m.score)}</td><td>${m.location_scope} · ${esc(m.country)}</td><td>${esc(m.competition_type)}</td><td>${esc(a.participation_status)}</td><td>${a.starter===null?'未披露':a.starter?'是':'否'}</td><td>${known(a.minutes)}</td><td>${known(a.goals)}</td><td>${known(a.assists)}</td><td><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.publisher)} · ${s.source_priority.startsWith('official_')?'官方来源':'媒体报道'}</a><br>可信度：${esc(a.confidence)}<br>${esc(a.notes)}</td></tr>`}).join('') || '<tr><td colspan="13">暂无已核验的匹配比赛记录。</td></tr>';
    }
    container.querySelectorAll('input,select').forEach(el=>el.addEventListener('input',render));render();
  } catch (error) { container.textContent=`比赛记录加载失败，请刷新重试。${error.message}`; }
})();
