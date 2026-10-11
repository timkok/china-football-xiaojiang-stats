"""One-time, idempotent audit migration. Never invoked by the site build."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "data"
def read(name):
    return json.loads((root / f"{name}.json").read_text())
def write(name, value):
    (root / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

players, relations, selections, sources, log = map(read, ["players", "relations", "selections", "sources", "changelog"])
sid = "cfa-u17-20260911"
if any(s["id"] == sid for s in sources):
    raise SystemExit("Migration already applied")
clubs = {"顾博宇": "上海申花", "帅惟浩": "成都蓉城", "邝兆镭": "青岛海牛", "袁博涵": "深圳青年人", "周雨诺": "清华大学附属中学", "南子勋": "清华大学附属中学", "万项": "贝尔格拉德红星"}
for r in relations:
    r.update(relation_status="pending", confidence="low", evidence_text="历史来源线索，尚未逐条核实正文是否明确指向中国足球小将项目。", notes="有 URL 不等于证据核验完成。")
for s in selections:
    s.update(confidence="low", reviewed=False, notes="历史入选线索；原始名单、日期和球员身份需重新核对。", camp_start_date="", camp_end_date="")
    if s["selection_type"] == "正式报名":
        s["selection_type"] = "名单线索"
for s in sources:
    s.update(retrieved_at=None, reliability_score=None, reviewed=False)
    s["notes"] = "历史导入来源，标题、发布日期及内容尚待核验。"
sources.append(dict(id=sid, title="中国足球协会关于组织中国U-17国家男子足球队2026年第六期集训的通知", url="https://www.thecfa.cn/jxtz/20260911/38141.html", publisher="中国足球协会", source_type="official", source_priority="official_cfa", published_date="2026-09-11", retrieved_at="2026-10-11", archived_url="", reliability_score=95, access_status="accessible", reviewed=True, used_for=["national_team_selection"], involved_players=list(clubs), involved_levels=["U17"], notes="已核对正文参训运动员名单；仅关联现有库中的球员，不据此确认小将关系。"))
changes = []
for p in players:
    old = p["verification_status"]
    p.update(verification_status="pending", is_overseas=None, notes="历史出生年份、位置及小将关系待复核；单位为名单所列单位，不代表当前注册状态。")
    if p["name"] in clubs:
        p["verification_status"] = "partially_confirmed"
        record_id = f"sel-20260911-{p['slug']}"
        selections.append(dict(id=record_id, player_id=p["id"], national_team_level="U17", official_team_name="中国U-17国家男子足球队", selection_type="集训名单", selection_date="2026-09-11", event_name="2026年第六期集训", camp_start_date="2026-09-16", camp_end_date="2026-10-09", listed_club=clubs[p["name"]], source_id=sid, confidence="high", reviewed=True, notes="通知名单确认入选，不证明实际报到或比赛出场。"))
        p["selection_ids"].append(record_id)
        p["current_club"] = clubs[p["name"]]
        p["listed_club"] = clubs[p["name"]]
    changes.append(f"{p['name']}: {old} → {p['verification_status']}")
log.insert(0, dict(date="2026-10-11", title="重新审计历史证据并补充足协第六期名单", added_players=[], status_changes=changes, added_sources=[sid], stat_changes={"confirmed":0,"partially_confirmed":7,"pending":27,"selections":len(selections)}, deleted_or_corrected=["撤销仅凭 URL 存在的 confirmed 判定", "移除无法核实的留洋推断", "构建不再覆盖数据和变更日志"], reason="区分历史线索与正文核验结果，避免将结构校验通过误认为事实已确认。"))
for name, values in zip(["players", "relations", "selections", "sources", "changelog"], [players, relations, selections, sources, log]):
    write(name, values)
