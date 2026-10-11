// One-time, idempotent migration of individually reviewed media reports.
import fs from 'node:fs';
const root = new URL('../data/', import.meta.url);
const read = name => JSON.parse(fs.readFileSync(new URL(`${name}.json`, root), 'utf8'));
const data = Object.fromEntries(['players','sources','matches','appearances','changelog'].map(n=>[n,read(n)]));
const reports = [
  {id:'media-wan-club-20260302',title:'足球报：万项将提前归队备战亚少赛 邝兆镭中超出场情况有待观察',url:'https://m.zhibo8.cc/news/web/zuqiu/2026-03-02/69a545aa3a506native.htm',publisher:'足球报（直播吧转载）',published_date:'2026-03-02',involved_players:['万项'],involved_levels:[]},
  {id:'media-kuang-club-20260307',title:'玉昆3-1海牛开门红 侯永永、克莱伯破门 16岁邝兆镭中超首秀',url:'https://news.sina.cn/gn/2026-03-07/detail-inhqeria1498903.d.html',publisher:'直播吧（新浪转载）',published_date:'2026-03-07',involved_players:['邝兆镭'],involved_levels:[]}
];
const fixtures = [
  {id:'20260221-redstar-backa',match_date:'2026-02-21',date_timezone:null,date_basis:'媒体报道的比赛日期，时区未单独核验',competition:'塞尔维亚U17联赛',stage:'联赛',team:'贝尔格莱德红星U17',team_level:'U17',opponent:'巴奇卡托波拉U17',country:'塞尔维亚',location_scope:'境外',competition_type:'海外青年联赛',score:'2–2',source_id:reports[0].id},
  {id:'20260307-hainiu-yukun',match_date:'2026-03-07',date_timezone:'Asia/Shanghai',date_basis:'北京时间',competition:'中国足球超级联赛',stage:'第1轮',team:'青岛海牛',team_level:'senior',opponent:'云南玉昆',country:'中国',location_scope:'境内',competition_type:'国内职业联赛',score:'1–3',source_id:reports[1].id}
];
for (const m of data.matches) m.team_type ??= 'national';
for (const report of reports) {
  if (!data.sources.some(s=>s.id===report.id)) data.sources.push({...report,source_type:'media',source_priority:'mainstream_media',retrieved_at:'2026-10-11',archived_url:'',reliability_score:75,access_status:'accessible',reviewed:true,used_for:['club_match_appearance'],notes:'已核对报道正文；属于媒体证据，不是官方技术统计，也不是国字号入选证据。'});
}
fixtures.forEach((m,i)=>{
  if (!data.matches.some(x=>x.id===m.id)) data.matches.push({...m,team_type:'club'});
  const p = data.players.find(p=>p.name===reports[i].involved_players[0]);
  const id = `club-appearance-${m.id}`;
  if (!data.appearances.some(a=>a.id===id)) data.appearances.push({id,player_id:p.id,match_id:m.id,match_date:m.match_date,competition:m.competition,team_level:m.team_level,opponent:m.opponent,participation_status:'出场',starter:false,entry_minute:i===0?38:87,minutes:null,goals:null,assists:null,source_id:m.source_id,confidence:'medium',reviewed:true,notes:`媒体明确记载第${i===0?38:87}分钟替补出场；不据换人时间推算实际出场分钟。俱乐部出场不用于提高国字号验证状态。`});
  if (!p.appearance_ids.includes(id)) p.appearance_ids.push(id);
  p.has_appearance = true;
});
if (!data.changelog.some(c=>c.title==='新增国内及海外俱乐部比赛')) data.changelog.unshift({date:'2026-10-11',title:'新增国内及海外俱乐部比赛',added_players:[],status_changes:[],added_sources:reports.map(s=>s.id),stat_changes:{added_matches:2,added_appearances:2},deleted_or_corrected:[],reason:'补充邝兆镭中超首秀和万项塞尔维亚青年联赛出场。媒体证据标为 medium；未知技术统计留空，不改变国字号确认人数。'});
for (const [name,rows] of Object.entries(data)) fs.writeFileSync(new URL(`${name}.json`,root),JSON.stringify(rows,null,2)+'\n');
