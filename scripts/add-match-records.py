"""Import individually checked CFA match-report facts; safe to rerun."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1] / 'data'
def read(n): return json.loads((root / (n+'.json')).read_text())
def write(n,d): (root / (n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
players, sources, apps, log = map(read,['players','sources','appearances','changelog'])
if any(a['id'].startswith('match-import-') for a in apps): raise SystemExit('Already imported')
reports = [
 ('cfa-final-20260523','U17亚洲杯决赛战报','https://www.thecfa.cn/xinwenu17/20260523/37719.html','2026-05-23',['万项','赵松源','帅惟浩']),
 ('cfa-shanghai-20260807','上海明日之星冠军杯小组赛战报','https://www.thecfa.cn/shipinu17/20260807/38048.html','2026-08-07',['赵松源','周雨诺'])]
for sid,title,url,date,names in reports:
 sources.append(dict(id=sid,title=title,url=url,publisher='中国足球协会',source_type='official',source_priority='official_cfa',published_date=date,retrieved_at='2026-10-11',archived_url='',reliability_score=95,access_status='accessible',reviewed=True,used_for=['match_appearance'],involved_players=names,involved_levels=['U17'],notes='正文战报支持所列出场事实；非完整比赛技术统计。'))
# Dates follow the reports: final date is Beijing time, Shanghai dates are local.
fixtures=[('20260523-japan','2026-05-23','U17亚洲杯','决赛','日本U17','沙特阿拉伯','境外','国家队正式赛','2–3',reports[0][0]),('20260803-arsenal','2026-08-03','上海明日之星冠军杯','小组赛','阿森纳U17','中国','境内','国际邀请赛','3–2',reports[1][0]),('20260804-athletic','2026-08-04','上海明日之星冠军杯','小组赛','毕尔巴鄂竞技U17','中国','境内','国际邀请赛','1–0',reports[1][0]),('20260806-leverkusen','2026-08-06','上海明日之星冠军杯','小组赛','勒沃库森U17','中国','境内','国际邀请赛','2–1',reports[1][0])]
matches=[]
for mid,date,competition,stage,opponent,country,location,kind,score,sid in fixtures:
 matches.append(dict(id=mid,match_date=date,date_timezone='Asia/Shanghai',competition=competition,stage=stage,team='中国U17',team_level='U17',opponent=opponent,country=country,location_scope=location,competition_type=kind,score=score,source_id=sid))
facts=[('万项',0,None,1,'战报记载下半场进球。'),('赵松源',0,False,1,'战报说明未首发，并记载下半场点球得分。'),('帅惟浩',0,None,None,'战报记载参与进球前传球，支持出场；不据此填写官方助攻。'),('赵松源',1,None,1,'战报记载进球；制造乌龙球不计为个人进球。'),('周雨诺',1,True,None,'次轮战报说明首发只保留周雨诺，可确认前后两轮均首发。'),('周雨诺',2,True,None,'战报明确为保留的首发球员。'),('赵松源',2,False,None,'战报明确替补出场。'),('赵松源',3,None,1,'战报记载进球与进球前头球摆渡；助攻统计未明确。')]
for index,(name,mi,starter,goals,note) in enumerate(facts):
 p=next(p for p in players if p['name']==name); m=matches[mi]; aid=f'match-import-{index+1:03}'
 apps.append(dict(id=aid,player_id=p['id'],match_id=m['id'],match_date=m['match_date'],competition=m['competition'],team_level='U17',opponent=m['opponent'],participation_status='出场',starter=starter,minutes=None,goals=goals,assists=None,source_id=m['source_id'],confidence='high',reviewed=True,notes=note))
 p['appearance_ids'].append(aid);p['has_appearance']=True
 p['notes']+=' 已有官方比赛出场证据；小将关系仍待复核。'
 if p['verification_status']=='pending':p['verification_status']='partially_confirmed'
log.insert(0,dict(date='2026-10-11',title='新增国内外比赛记录',added_players=[],status_changes=['赵松源: pending → partially_confirmed（官方比赛出场已核验，小将关系待复核）'],added_sources=[r[0] for r in reports],stat_changes={'matches':len(matches),'appearances':len(apps)},deleted_or_corrected=[],reason='逐条录入官方战报支持的比赛表现；未披露技术统计保留 null，不将报名或球队参赛视为个人出场。'))
for n,d in [('matches',matches),('appearances',apps),('players',players),('sources',sources),('changelog',log)]:write(n,d)
