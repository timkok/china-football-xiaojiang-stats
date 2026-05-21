#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import shutil
from collections import defaultdict
from datetime import date
from html import escape

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PROCESSED_JSON_FILE = os.path.join(DATA_DIR, "processed", "players_clean.json")
TODAY = date.today().isoformat()
SITE_URL = "https://timkok.github.io/china-football-xiaojiang-stats/"
SEO_TITLE = "中国足球小将国字号入选数据库｜U14-U20 国少国青统计"
SEO_DESCRIPTION = "基于中国足协官网、俱乐部公告、媒体公开报道整理中国足球小将相关球员入选 U14、U15、U16、U17、U19、U20 等各级国字号队伍的情况，包含出生年份、俱乐部、入选时间、来源证据和数据可信度。"

ALLOWED_LEVELS = ["U14", "U15", "U16", "U17", "U18", "U19", "U20", "U23", "senior"]

PLAYER_SLUGS = {
    "万项": "wan-xiang", "邝兆镭": "kuang-zhaolei", "赵松源": "zhao-songyuan",
    "谢晋": "xie-jin", "帅惟浩": "shuai-weihao", "汪修昊": "wang-xiuhao",
    "南子勋": "nan-zixun", "周雨诺": "zhou-yunuo", "顾博宇": "gu-boyu",
    "毛永彬": "mao-yongbin", "黄子杰": "huang-zijie", "戴宥哲": "dai-youzhe",
    "吕孟洋": "lv-mengyang", "吕孟洲": "lv-mengzhou", "李佑安": "li-youan",
    "张林峒": "zhang-lintong", "李东宸": "li-dongchen", "沙明": "sha-ming",
    "曾晨": "zeng-chen", "宋泓渝": "song-hongyu", "朴智轩": "piao-zhixuan",
    "袁博涵": "yuan-bohan", "吴王允祥": "wuwang-yunxiang", "廖梓成": "liao-zicheng",
    "詹景源": "zhan-jingyuan", "赵峰屹": "zhao-fengyi", "姜胤宇": "jiang-yinyu",
    "何浩源": "he-haoyuan", "刘凯源": "liu-kaiyuan", "刘礼豪": "liu-lihao",
    "杨皓砼": "yang-haotong", "李贺哲": "li-hezhe", "杜双杰": "du-shuangjie",
    "魏子烜": "wei-zixuan",
}

SOURCE_META = {
    "https://www.thecfa.cn/jxtz/20251104/37051.html": ("中国U-16国家男子足球队2025年第五期集训通知", "中国足球协会", "official_cfa", "2025-11-04", 95),
    "https://www.thecfa.cn/wqmdu17/20260415/37563.html": ("中国U-17国家男子足球队2026年第一期集训通知", "中国足球协会", "official_cfa", "2026-01-18", 95),
    "https://www.thecfa.cn/jxtz/20250925/36930.html": ("中国U-16国家男子足球队2025年第四期集训通知", "中国足球协会", "official_cfa", "2025-09-25", 95),
    "https://www.thecfa.cn/wqmdu17/20260311/37414.html": ("中国U-17国家男子足球队2026年第二期集训通知", "中国足球协会", "official_cfa", "2026-03-11", 95),
    "https://www.thecfa.cn/zxwj/20260428/33890.html": ("中国足球协会关于组织U-17国家男子足球队备战U17亚洲杯决赛阶段比赛的通知", "中国足球协会", "official_cfa", "2026-04-28", 95),
    "https://www.thecfa.cn/zxwj/20260410/33820.html": ("中国足球协会关于组织U-15国家男子足球队赴意大利参赛的通知", "中国足球协会", "official_cfa", "2026-04-10", 95),
    "https://www.thecfa.cn/zxwj/20240618/32155.html": ("中国足球协会关于组织2009年龄段男子国家少年足球选拔队集训的通知", "中国足球协会", "official_cfa", "2024-06-18", 95),
    "https://www.thecfa.cn/zxwj/20240610/32140.html": ("中国足球协会关于组织2010年龄段男子国家少年足球选拔队集训的通知", "中国足球协会", "official_cfa", "2024-06-10", 95),
    "https://www.thecfa.cn/zxwj/20240315/31822.html": ("中国足球协会关于组织2008年龄段国家少年男子足球队集训的通知", "中国足球协会", "official_cfa", "2024-03-15", 95),
    "https://www.thecfa.cn/zxwj/20231122/31560.html": ("中国足球协会关于组织2009年龄段男子国家少年足球选拔队精英集训的通知", "中国足球协会", "official_cfa", "2023-11-22", 95),
}

SOURCE_HINTS = [
    ("thecfa.cn", "中国足球协会", "official_cfa", 95),
    ("thepaper.cn", "澎湃新闻", "mainstream_media", 72),
    ("dongqiudi.com", "懂球帝", "mainstream_media", 70),
    ("zhibo8.com", "直播吧", "mainstream_media", 68),
    ("sina.com.cn", "新浪体育", "mainstream_media", 72),
    ("ifeng.com", "凤凰网体育", "mainstream_media", 65),
    ("163.com", "网易", "mainstream_media", 65),
    ("ppsports.com", "PP体育", "mainstream_media", 65),
]


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def slugify_name(name, index):
    return PLAYER_SLUGS.get(name) or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or f"player-{index:03d}"


def confidence_from_priority(priority):
    return "high" if priority in ["official_cfa", "official_team", "club", "xiaojiang_official"] else "medium" if priority == "mainstream_media" else "low"


def source_defaults(url, fallback_title):
    if url in SOURCE_META:
        title, publisher, priority, published_date, score = SOURCE_META[url]
        return title or fallback_title, publisher, priority, published_date, score
    for needle, publisher, priority, score in SOURCE_HINTS:
        if needle in url:
            return fallback_title or "待补充标题", publisher, priority, "", score
    return fallback_title or "待补充标题", "待核验", "unknown", "", 30


def age_group_from_birth_year(birth_year):
    return f"{birth_year}年龄段" if birth_year else "未知年龄段"


def is_overseas(unit):
    if not unit:
        return False
    overseas_terms = ["红星", "贝尔格莱德", "皇家", "卡拉万切尔", "达姆", "塞尔维亚", "西班牙"]
    return any(term in unit for term in overseas_terms)


def normalize_selection_type(value):
    if not value:
        return "集训名单"
    if "正式" in value:
        return "正式报名"
    if "出场" in value:
        return "出场"
    return value


def build_data(records):
    source_by_url = {}
    source_players = defaultdict(set)
    source_levels = defaultdict(set)

    def ensure_source(url, fallback_title, player_name, role, level=""):
        if not url:
            return ""
        if url not in source_by_url:
            title, publisher, priority, published_date, score = source_defaults(url, fallback_title)
            sid = f"src-{len(source_by_url) + 1:03d}"
            source_by_url[url] = {
                "id": sid,
                "title": title,
                "url": url,
                "publisher": publisher,
                "source_type": "official" if priority.startswith("official") else priority,
                "source_priority": priority,
                "published_date": published_date,
                "retrieved_at": TODAY,
                "archived_url": "",
                "reliability_score": score,
                "access_status": "unchecked",
                "used_for": [],
                "involved_players": [],
                "involved_levels": [],
                "notes": "",
            }
        if role not in source_by_url[url]["used_for"]:
            source_by_url[url]["used_for"].append(role)
        source_players[url].add(player_name)
        if level:
            source_levels[url].add(level)
        return source_by_url[url]["id"]

    players_by_key = {}
    relations = []
    selections = []
    appearances = []

    for idx, row in enumerate(records, 1):
        name = row["player_name"].strip()
        birth_year = row.get("birth_year") or None
        listed_club = row.get("current_or_listed_club") or "未知"
        position = row.get("position") or "未知"
        identity_key = (name, birth_year, listed_club if name not in players_by_key else "", position)
        merge_key = (name, birth_year)
        existing_key = next((key for key in players_by_key if key[0] == name and key[1] == birth_year), None)
        player_key = existing_key or merge_key or identity_key

        if player_key not in players_by_key:
            player_id = f"player-{len(players_by_key) + 1:03d}"
            players_by_key[player_key] = {
                "id": player_id,
                "name": name,
                "slug": slugify_name(name, len(players_by_key) + 1),
                "aliases": [],
                "birth_year": birth_year,
                "age_group": age_group_from_birth_year(birth_year),
                "position": position,
                "current_club": listed_club,
                "listed_club": listed_club,
                "nationality": "中国",
                "is_overseas": is_overseas(listed_club),
                "has_appearance": False,
                "verification_status": "pending",
                "relation_ids": [],
                "selection_ids": [],
                "appearance_ids": [],
                "identity_key": f"{name}|{birth_year or 'unknown'}|{position}|{listed_club}",
                "notes": "",
            }

        player = players_by_key[player_key]
        if player["current_club"] == "未知" and listed_club != "未知":
            player["current_club"] = listed_club
            player["listed_club"] = listed_club
        player["is_overseas"] = player["is_overseas"] or is_overseas(listed_club)

        relation_source_id = ensure_source(
            row.get("relation_source_url", ""),
            f"{name}与中国足球小将关系来源",
            name,
            "xiaojiang_relation",
        )
        relation_id = f"rel-{idx:03d}"
        relation_priority = source_by_url.get(row.get("relation_source_url", ""), {}).get("source_priority", "unknown")
        relation_status = "confirmed" if relation_priority in ["xiaojiang_official", "club", "mainstream_media", "official_cfa", "official_team"] else "pending"
        relations.append({
            "id": relation_id,
            "player_id": player["id"],
            "relation_type": row.get("football_xiaojiang_relation") or "待确认",
            "relation_status": relation_status,
            "source_id": relation_source_id,
            "evidence_text": "来源记录该球员与中国足球小将项目、队伍、赛事或公开报道之间的关系。",
            "confidence": confidence_from_priority(relation_priority),
            "notes": "",
        })
        player["relation_ids"].append(relation_id)

        if row.get("national_team_level"):
            selection_source_id = ensure_source(
                row.get("national_team_source_url", ""),
                row.get("source_title", ""),
                name,
                "national_team_selection",
                row.get("national_team_level", ""),
            )
            selection_priority = source_by_url.get(row.get("national_team_source_url", ""), {}).get("source_priority", "unknown")
            selection_id = f"sel-{idx:03d}"
            selection_type = normalize_selection_type(row.get("selection_type"))
            selections.append({
                "id": selection_id,
                "player_id": player["id"],
                "national_team_level": row.get("national_team_level"),
                "official_team_name": row.get("team_name_official"),
                "selection_type": selection_type,
                "selection_date": row.get("selection_date"),
                "event_name": row.get("event_or_context"),
                "camp_start_date": row.get("selection_date"),
                "camp_end_date": "",
                "listed_club": listed_club,
                "source_id": selection_source_id,
                "confidence": confidence_from_priority(selection_priority),
                "notes": "",
            })
            player["selection_ids"].append(selection_id)

            if selection_type in ["出场", "首发", "进球", "助攻"] and "亚洲杯" in (row.get("event_or_context") or ""):
                appearance_id = f"app-{len(appearances) + 1:03d}"
                appearances.append({
                    "id": appearance_id,
                    "player_id": player["id"],
                    "match_date": row.get("selection_date"),
                    "competition": row.get("event_or_context"),
                    "team_level": row.get("national_team_level"),
                    "opponent": "",
                    "starter": None,
                    "minutes": None,
                    "goals": None,
                    "assists": None,
                    "source_id": selection_source_id,
                    "confidence": "medium",
                    "notes": "原始数据标记为“正式名单/出场”，但缺少逐场技术统计；仅作为出场线索，不用于“主力”结论。",
                })
                player["appearance_ids"].append(appearance_id)
                player["has_appearance"] = True

    requested_sources = [
        "https://www.thecfa.cn/jxtz/20251104/37051.html",
        "https://www.thecfa.cn/wqmdu17/20260415/37563.html",
        "https://www.thecfa.cn/jxtz/20250925/36930.html",
        "https://www.thecfa.cn/wqmdu17/20260311/37414.html",
    ]
    for url in requested_sources:
        ensure_source(url, "", "", "priority_reference")
        source_by_url[url]["notes"] = "优先跟踪的中国足协国字号集训通知；是否逐名并入以 selections.json 为准。"

    for url, source in source_by_url.items():
        source["involved_players"] = sorted(name for name in source_players[url] if name)
        source["involved_levels"] = sorted(source_levels[url])

    relation_by_player = defaultdict(list)
    selection_by_player = defaultdict(list)
    for rel in relations:
        relation_by_player[rel["player_id"]].append(rel)
    for sel in selections:
        selection_by_player[sel["player_id"]].append(sel)

    source_by_id = {source["id"]: source for source in source_by_url.values()}
    for player in players_by_key.values():
        strong_rel = any(rel["relation_status"] == "confirmed" and rel["confidence"] in ["high", "medium"] for rel in relation_by_player[player["id"]])
        strong_sel = any(sel["confidence"] in ["high", "medium"] for sel in selection_by_player[player["id"]])
        has_rel = bool(relation_by_player[player["id"]])
        has_sel = bool(selection_by_player[player["id"]])
        if strong_rel and strong_sel:
            player["verification_status"] = "confirmed"
        elif has_rel and has_sel:
            player["verification_status"] = "partially_confirmed"
        elif has_rel or has_sel:
            player["verification_status"] = "pending"
        else:
            player["verification_status"] = "disputed"

    players = sorted(players_by_key.values(), key=lambda p: (p.get("birth_year") or 9999, p["name"]))
    return players, selections, list(source_by_url.values()), relations, appearances, source_by_id


def clean_generated_dirs():
    for item in ["players", "sources", "changelog", "methodology", "assets"]:
        path = os.path.join(BASE_DIR, item)
        if os.path.exists(path):
            shutil.rmtree(path)
    os.makedirs(ASSETS_DIR, exist_ok=True)


def page_shell(title, description, body, root_path="", extra_head=""):
    dataset_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "中国足球小将国字号入选数据库",
        "description": SEO_DESCRIPTION,
        "url": SITE_URL,
        "dateModified": TODAY,
        "inLanguage": "zh-CN",
    }, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}">
  <meta property="og:image" content="{SITE_URL}assets/og-cover.svg">
  <meta property="og:locale" content="zh_CN">
  <link rel="canonical" href="{SITE_URL}">
  <link rel="stylesheet" href="{root_path}assets/styles.css">
  <script type="application/ld+json">{dataset_json}</script>
  {extra_head}
</head>
<body data-root="{root_path}" data-updated-at="{TODAY}">
  <nav class="topbar">
    <a class="brand" href="{root_path}">中国足球小将国字号入选数据库</a>
    <div class="navlinks">
      <a href="{root_path}">Dashboard</a>
      <a href="{root_path}sources/">来源库</a>
      <a href="{root_path}changelog/">Changelog</a>
      <a href="{root_path}methodology/">统计口径</a>
    </div>
  </nav>
  {body}
</body>
</html>
"""


def build_index():
    faq_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "什么算中国足球小将队员？", "acceptedAnswer": {"@type": "Answer", "text": "需有中国足球小将官方、董路公开确认、俱乐部学校地方足协或可信媒体明确记录其属于、曾代表、曾训练于或被称为中国足球小将相关球员。"}},
            {"@type": "Question", "name": "什么算入选国字号？", "acceptedAnswer": {"@type": "Answer", "text": "以中国足协、中国之队、亚足联、FIFA、俱乐部公告等可追溯来源中的 U14-U23 或成年国家队集训、比赛、报名或出场记录为准。"}},
            {"@type": "Question", "name": "为什么 pending 不计入核心确认人数？", "acceptedAnswer": {"@type": "Answer", "text": "pending 缺少至少一条核心证据链或来源强度不足，只作为待核验线索保留。"}},
        ],
    }, ensure_ascii=False)
    body = """<main class="container">
    <section class="hero">
      <p class="eyebrow">可审计体育数据集</p>
      <h1>中国足球小将国字号入选统计与可视化</h1>
      <p>本页面从结构化 JSON 数据自动生成统计、筛选、图表和证据链。核心确认人数只统计同时具备中国足球小将关系证据和国字号入选证据的 confirmed 球员。</p>
      <div class="meta-strip" id="dataHealth"></div>
    </section>
    <section class="stats-grid" id="statsGrid" aria-live="polite"></section>
    <section class="panel">
      <div class="section-head">
        <div><p class="eyebrow">Interactive Charts</p><h2>分布与趋势</h2></div>
        <p class="muted">点击图表中的年份或国字号级别可联动筛选明细表。</p>
      </div>
      <div class="chart-grid">
        <div class="chart-card"><h3>出生年份分布</h3><div id="birthYearChart" class="bar-chart"></div></div>
        <div class="chart-card"><h3>国字号级别分布</h3><div id="levelChart" class="bar-chart"></div></div>
        <div class="chart-card wide"><h3>入选时间线</h3><div id="timelineChart" class="timeline-chart"></div></div>
      </div>
    </section>
    <section class="panel">
      <div class="section-head">
        <div><p class="eyebrow">Player Database</p><h2>球员数据库</h2></div>
        <div class="button-row">
          <button id="exportCsv" class="ghost-button" type="button">导出 CSV</button>
          <button id="resetFilters" class="ghost-button" type="button">重置筛选</button>
        </div>
      </div>
      <div class="filters" id="filters"></div>
      <div class="table-summary" id="tableSummary"></div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>姓名</th><th>出生年份</th><th>位置</th><th>俱乐部/单位</th><th>小将关系状态</th>
              <th>国字号级别</th><th>入选时间</th><th>集训/赛事背景</th><th>来源优先级</th>
              <th>可信度</th><th>验证状态</th><th>证据链链接</th><th>备注</th>
            </tr>
          </thead>
          <tbody id="playerRows"></tbody>
        </table>
      </div>
    </section>
    <section class="panel faq">
      <p class="eyebrow">FAQ</p>
      <h2>统计口径摘要</h2>
      <details open><summary>“U17 亚洲杯相关入选/出场球员”如何定义？</summary><p>本版不使用“主力”表述。该指标仅统计 selections.json 中事件名称包含“U17亚洲杯”且球员为 confirmed 的记录。若未来补充逐场首发、分钟、进球或助攻证据，可在 appearances.json 中单独计算。</p></details>
      <details><summary>集训名单、比赛名单、正式报名、实际出场有什么区别？</summary><p>集训名单表示进入集训通知；比赛名单或正式报名表示进入赛事报名或参赛名单；实际出场需要 appearance 或 match evidence 支撑。</p></details>
      <details><summary>如何提交纠错？</summary><p>请补充球员、证据类型、来源 URL、发布时间和需要修改的字段。更新后需运行 npm run validate:data。</p></details>
    </section>
  </main>
  <script type="application/ld+json">""" + faq_json + """</script>
  <script src="assets/app.js"></script>"""
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(page_shell(SEO_TITLE, SEO_DESCRIPTION, body))


def build_sources_page():
    body = """<main class="container">
    <section class="hero compact">
      <p class="eyebrow">Sources</p>
      <h1>来源库</h1>
      <p>来源库记录标题、发布机构、日期、优先级、涉及球员和可访问性状态。国字号事实优先引用中国足协等官方来源。</p>
    </section>
    <section class="panel">
      <div class="table-wrap">
        <table>
          <thead><tr><th>来源标题</th><th>发布机构</th><th>发布日期</th><th>类型</th><th>优先级</th><th>涉及球员</th><th>涉及级别</th><th>可访问性</th><th>原始链接</th><th>归档</th></tr></thead>
          <tbody id="sourceRows"></tbody>
        </table>
      </div>
    </section>
  </main>
  <script src="../assets/sources.js"></script>"""
    os.makedirs(os.path.join(BASE_DIR, "sources"), exist_ok=True)
    with open(os.path.join(BASE_DIR, "sources", "index.html"), "w", encoding="utf-8") as f:
        f.write(page_shell("来源库｜中国足球小将国字号入选数据库", "中国足球小将国字号入选数据库来源库。", body, "../"))


def build_changelog_page(players, selections, sources, relations):
    changelog = [{
        "date": TODAY,
        "title": "升级为可审计、可筛选、可持续更新的数据产品",
        "added_players": [p["name"] for p in players],
        "status_changes": [],
        "added_sources": [s["id"] for s in sources],
        "stat_changes": {
            "players": len(players),
            "selections": len(selections),
            "sources": len(sources),
            "relations": len(relations),
        },
        "deleted_or_corrected": [],
        "reason": "将静态展示页重构为数据驱动的证据链数据库，并降低无法逐场核验的主力表述。",
    }]
    write_json(os.path.join(DATA_DIR, "changelog.json"), changelog)
    body = """<main class="container">
    <section class="hero compact"><p class="eyebrow">Changelog</p><h1>变更日志</h1><p>记录新增球员、来源、状态变化、统计变化、删除或修正原因。</p></section>
    <section class="panel" id="changelogList"></section>
  </main>
  <script src="../assets/changelog.js"></script>"""
    os.makedirs(os.path.join(BASE_DIR, "changelog"), exist_ok=True)
    with open(os.path.join(BASE_DIR, "changelog", "index.html"), "w", encoding="utf-8") as f:
        f.write(page_shell("变更日志｜中国足球小将国字号入选数据库", "中国足球小将国字号入选数据库变更日志。", body, "../"))


def build_methodology_page():
    body = """<main class="container">
    <section class="hero compact"><p class="eyebrow">Methodology</p><h1>统计口径与 FAQ</h1><p>本页说明身份判定、入选判定、状态规则和更新流程。</p></section>
    <section class="panel faq">
      <details open><summary>什么算“中国足球小将队员”？</summary><p>需要有中国足球小将官方账号、董路公开确认、俱乐部/学校/地方足协，或可信媒体明确说明其属于、曾代表、曾训练于或被称为中国足球小将相关球员。</p></details>
      <details open><summary>什么算“入选国字号”？</summary><p>以 U14、U15、U16、U17、U18、U19、U20、U23 或成年国家队的集训通知、比赛名单、正式报名、出场记录为准。中国足协官网优先。</p></details>
      <details><summary>集训名单、比赛名单、正式报名、实际出场有什么区别？</summary><p>集训名单只表示进入训练名单；比赛名单或正式报名表示进入赛事名单；实际出场、首发、进球、助攻必须有 appearance 或 match evidence。</p></details>
      <details><summary>为什么 pending 不计入核心数字？</summary><p>pending 说明至少一条核心证据链缺失或来源强度不足。它保留为线索，但不进入 confirmed 核心统计。</p></details>
      <details><summary>“U17 亚洲杯主力”如何处理？</summary><p>当前数据缺少逐场首发或分钟证据，因此页面改为“U17 亚洲杯相关入选/出场球员”。只有补充 appearances.json 后，才可计算首发、分钟或进球助攻指标。</p></details>
      <details><summary>数据多久更新一次？</summary><p>本仓库为静态数据集，更新频率取决于维护者提交。每次更新应写入 changelog 并运行数据校验。</p></details>
      <details><summary>如何提交纠错？</summary><p>请提供球员姓名、出生年或俱乐部辅助识别、需要修改的字段、来源 URL、发布日期和证据摘录。</p></details>
    </section>
  </main>"""
    os.makedirs(os.path.join(BASE_DIR, "methodology"), exist_ok=True)
    with open(os.path.join(BASE_DIR, "methodology", "index.html"), "w", encoding="utf-8") as f:
        f.write(page_shell("统计口径｜中国足球小将国字号入选数据库", "中国足球小将国字号入选数据库统计口径和 FAQ。", body, "../"))


def build_player_pages(players):
    os.makedirs(os.path.join(BASE_DIR, "players"), exist_ok=True)
    for player in players:
        page_dir = os.path.join(BASE_DIR, "players", player["slug"])
        os.makedirs(page_dir, exist_ok=True)
        body = f"""<main class="container detail-page" data-player-slug="{escape(player['slug'])}">
    <section class="hero compact">
      <p class="eyebrow">Player Detail</p>
      <h1>{escape(player['name'])}</h1>
      <p>该详情页从 data/*.json 读取基本信息、中国足球小将关系、国字号入选时间线、出场线索和来源列表。</p>
    </section>
    <section class="panel" id="playerDetail"></section>
  </main>
  <script src="../../assets/player.js"></script>"""
        with open(os.path.join(page_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page_shell(f"{player['name']}｜球员详情", f"{player['name']} 的证据链和国字号入选记录。", body, "../../"))


def build_assets():
    styles = r""":root{--bg:#f7f8fb;--ink:#172033;--muted:#667085;--line:#d9dee8;--panel:#fff;--soft:#f2f4f7;--blue:#1f5eff;--green:#16794c;--amber:#9a6700;--red:#b42318;--violet:#6941c6}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif;line-height:1.55}a{color:var(--blue);text-decoration:none}.topbar{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;gap:20px;align-items:center;padding:14px 24px;background:rgba(255,255,255,.94);border-bottom:1px solid var(--line);backdrop-filter:blur(14px)}.brand{font-weight:800;color:var(--ink)}.navlinks{display:flex;gap:16px;flex-wrap:wrap}.container{max-width:1240px;margin:0 auto;padding:28px 20px 64px}.hero{padding:46px 0 26px}.hero.compact{padding-bottom:10px}.hero h1{font-size:clamp(2rem,4vw,3.4rem);line-height:1.08;margin:8px 0 14px;letter-spacing:0}.hero p{max-width:840px;color:var(--muted);font-size:1.05rem}.eyebrow{margin:0;color:var(--blue);font-size:.78rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.meta-strip{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 10px;font-size:.84rem}.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:18px 0 24px}.stat-card{border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:16px;text-align:left;cursor:pointer;min-height:132px}.stat-card:hover,.stat-card.active{border-color:var(--blue);box-shadow:0 8px 24px rgba(31,94,255,.12)}.stat-card .label{color:var(--muted);font-size:.86rem}.stat-card .value{display:block;font-size:2.1rem;font-weight:850;margin:6px 0}.stat-card .hint{color:var(--muted);font-size:.8rem}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:20px;margin-top:18px}.section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:16px}.section-head h2,.panel h2{margin:4px 0 0}.button-row{display:flex;gap:8px;flex-wrap:wrap}.ghost-button{border:1px solid var(--line);background:#fff;border-radius:6px;padding:9px 12px;color:var(--ink);cursor:pointer}.filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:16px}.filter label{display:block;color:var(--muted);font-size:.8rem;margin-bottom:5px}.filter input,.filter select{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--ink)}.table-summary{color:var(--muted);margin-bottom:10px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:8px}table{width:100%;border-collapse:collapse;min-width:1120px}th,td{border-bottom:1px solid var(--line);padding:10px;text-align:left;vertical-align:top;font-size:.9rem}th{color:#344054;background:var(--soft);font-weight:800}.badge{display:inline-flex;align-items:center;border-radius:999px;padding:3px 8px;font-size:.76rem;font-weight:800;background:#eef4ff;color:#1f5eff;white-space:nowrap}.badge.confirmed,.badge.high{background:#e9f7ef;color:var(--green)}.badge.partially_confirmed,.badge.medium{background:#fff7e6;color:var(--amber)}.badge.pending,.badge.low,.badge.disputed{background:#fff1f0;color:var(--red)}.evidence{display:flex;gap:6px;flex-wrap:wrap}.muted{color:var(--muted)}.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.chart-card{border:1px solid var(--line);border-radius:8px;padding:14px;background:#fff}.chart-card.wide{grid-column:1/-1}.bar-row{display:grid;grid-template-columns:96px 1fr auto;gap:10px;align-items:center;margin:10px 0}.bar-track{display:flex;height:28px;border-radius:6px;overflow:hidden;background:var(--soft);border:1px solid var(--line);cursor:pointer}.bar-seg{height:100%;min-width:2px}.seg-U14{background:#56ccf2}.seg-U15{background:#1f5eff}.seg-U16{background:#12b76a}.seg-U17{background:#f79009}.seg-U18,.seg-U19,.seg-U20{background:#6941c6}.timeline-chart{display:flex;gap:10px;align-items:flex-end;min-height:180px;overflow-x:auto;padding-top:12px}.timeline-bar{min-width:76px;text-align:center}.timeline-bar button{width:100%;border:0;background:#1f5eff;color:#fff;border-radius:6px 6px 0 0;cursor:pointer}.detail-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.evidence-card{border:1px solid var(--line);border-radius:8px;padding:16px;background:#fff}.evidence-card h3{margin-top:0}.faq details{border-top:1px solid var(--line);padding:12px 0}.faq summary{font-weight:800;cursor:pointer}.error{border-color:#fecdca;background:#fff6f5;color:var(--red)}@media(max-width:760px){.topbar{align-items:flex-start;flex-direction:column}.section-head{display:block}.chart-grid{grid-template-columns:1fr}.bar-row{grid-template-columns:70px 1fr 36px}.container{padding:20px 12px 48px}table{min-width:1040px}.stat-card{min-height:116px}}"""
    app_js = r"""const BASE=document.body.dataset.root||'';const $=s=>document.querySelector(s);const uniq=a=>[...new Set(a.filter(v=>v!==undefined&&v!==null&&String(v).trim()!==''))].sort((a,b)=>String(a).localeCompare(String(b),'zh-CN'));const state={filters:{q:'',birth_year:'',age_group:'',national_team_level:'',position:'',club:'',verification_status:'',source_priority:'',is_overseas:'',has_appearance:'',selection_year:''},data:null};const statusOrder=['confirmed','partially_confirmed','pending','disputed'];async function loadData(){try{const names=['players','selections','sources','relations','appearances'];const [players,selections,sources,relations,appearances]=await Promise.all(names.map(n=>fetch(`${BASE}data/${n}.json`).then(r=>{if(!r.ok)throw new Error(`${n}.json ${r.status}`);return r.json()})));const by=id=>Object.fromEntries(id.map(x=>[x.id,x]));const group=(arr,key)=>arr.reduce((m,x)=>((m[x[key]]??=[]).push(x),m),{});state.data={players,selections,sources,relations,appearances,sourceById:by(sources),selectionByPlayer:group(selections,'player_id'),relationByPlayer:group(relations,'player_id'),appearanceByPlayer:group(appearances,'player_id')};render();}catch(err){document.body.insertAdjacentHTML('afterbegin',`<div class="panel error">数据加载失败：${err.message}</div>`)}}function playerRows(){const d=state.data;return d.players.flatMap(p=>{const sels=d.selectionByPlayer[p.id]||[null];return sels.map(sel=>{const src=sel?d.sourceById[sel.source_id]:null;const rel=(d.relationByPlayer[p.id]||[])[0]||null;return{player:p,selection:sel,source:src,relation:rel}})})}function confirmedPlayers(){return state.data.players.filter(p=>p.verification_status==='confirmed')}function countPlayersBy(fn){return new Set(confirmedPlayers().filter(fn).map(p=>p.id)).size}function statCard(id,label,value,hint,onClick){return `<button class="stat-card" data-card="${id}" type="button" title="${hint}"><span class="label">${label}</span><span class="value">${value}</span><span class="hint">${hint}</span></button>`}function renderHealth(){const d=state.data;const official=d.sources.filter(s=>s.source_priority==='official_cfa'||s.source_priority==='official_team').length;const years=uniq(d.players.map(p=>p.birth_year));const levels=uniq(d.selections.map(s=>s.national_team_level));const statuses=Object.fromEntries(statusOrder.map(s=>[s,d.players.filter(p=>p.verification_status===s).length]));$('#dataHealth').innerHTML=[`最后更新 ${document.body.dataset.updatedAt}`,`confirmed ${statuses.confirmed}`,`partially ${statuses.partially_confirmed}`,`pending ${statuses.pending}`,`官方来源占比 ${Math.round(official/d.sources.length*100)}%`,`出生年份 ${years[0]}-${years.at(-1)}`,`国字号 ${levels.join(' / ')}`].map(x=>`<span class="pill">${x}</span>`).join('')}function renderStats(){const d=state.data;const asiaCup=countPlayersBy(p=>(d.selectionByPlayer[p.id]||[]).some(s=>s.national_team_level==='U17'&&/亚洲杯/.test(s.event_name||'')));const stats=[['confirmed','已确认国字号球员',confirmedPlayers().length,'仅统计 confirmed：双证据链均满足',()=>{setFilter('verification_status','confirmed')}],['by2009','2009 年龄段入选',countPlayersBy(p=>p.birth_year===2009),'仅统计 confirmed 且 birth_year=2009',()=>{setFilter('birth_year','2009');setFilter('verification_status','confirmed')}],['by2010','2010 年龄段入选',countPlayersBy(p=>p.birth_year===2010),'仅统计 confirmed 且 birth_year=2010',()=>{setFilter('birth_year','2010');setFilter('verification_status','confirmed')}],['u17asia','U17 亚洲杯相关入选/出场球员',asiaCup,'仅统计 confirmed；不使用未量化的“主力”结论',()=>{setFilter('national_team_level','U17');setFilter('verification_status','confirmed')}],['official','官方来源',d.sources.filter(s=>s.source_priority==='official_cfa'||s.source_priority==='official_team').length,'来源优先级 official_cfa + official_team',()=>{setFilter('source_priority','official_cfa')}],['pending','待补证据球员',d.players.filter(p=>p.verification_status==='pending').length,'pending 不计入核心确认人数',()=>{setFilter('verification_status','pending')}]];$('#statsGrid').innerHTML=stats.map(s=>statCard(...s.slice(0,4))).join('');stats.forEach(s=>document.querySelector(`[data-card="${s[0]}"]`).addEventListener('click',s[4]))}function setFilter(k,v){state.filters[k]=v;renderFilters();renderTable();renderCharts()}function clearFilters(){state.filters={q:'',birth_year:'',age_group:'',national_team_level:'',position:'',club:'',verification_status:'',source_priority:'',is_overseas:'',has_appearance:'',selection_year:''};render()}function optionList(key,opts){return `<div class="filter"><label>${key[1]}</label><select data-filter="${key[0]}"><option value="">全部</option>${opts.map(o=>`<option value="${o}" ${state.filters[key[0]]==String(o)?'selected':''}>${o}</option>`).join('')}</select></div>`}function renderFilters(){const d=state.data;const html=[`<div class="filter"><label>姓名搜索</label><input data-filter="q" value="${state.filters.q}" placeholder="输入姓名或别名"></div>`,optionList(['birth_year','出生年份'],uniq(d.players.map(p=>p.birth_year))),optionList(['age_group','年龄段'],uniq(d.players.map(p=>p.age_group))),optionList(['national_team_level','国字号级别'],uniq(d.selections.map(s=>s.national_team_level))),optionList(['position','位置'],uniq(d.players.map(p=>p.position))),optionList(['club','俱乐部/单位'],uniq(d.players.map(p=>p.current_club))),optionList(['verification_status','验证状态'],statusOrder),optionList(['source_priority','来源优先级'],uniq(d.sources.map(s=>s.source_priority))),optionList(['is_overseas','是否留洋'],['是','否']),optionList(['has_appearance','是否有正式比赛出场线索'],['是','否'])].join('');$('#filters').innerHTML=html;document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener(el.tagName==='INPUT'?'input':'change',e=>setFilter(e.target.dataset.filter,e.target.value)))}function filteredRows(){const f=state.filters;return playerRows().filter(({player:p,selection:s,source:src})=>(!f.q||p.name.includes(f.q)||p.aliases?.some(a=>a.includes(f.q)))&&(!f.birth_year||String(p.birth_year)===f.birth_year)&&(!f.age_group||p.age_group===f.age_group)&&(!f.national_team_level||s?.national_team_level===f.national_team_level)&&(!f.position||p.position===f.position)&&(!f.club||p.current_club===f.club)&&(!f.verification_status||p.verification_status===f.verification_status)&&(!f.source_priority||src?.source_priority===f.source_priority)&&(!f.is_overseas||(p.is_overseas?'是':'否')===f.is_overseas)&&(!f.has_appearance||(p.has_appearance?'是':'否')===f.has_appearance)&&(!f.selection_year||(s?.selection_date||'').slice(0,4)===f.selection_year))}function renderTable(){const rows=filteredRows();$('#tableSummary').textContent=`当前显示 ${rows.length} 条明细记录，涉及 ${new Set(rows.map(r=>r.player.id)).size} 名球员。`;$('#playerRows').innerHTML=rows.map(({player:p,selection:s,source:src,relation:r})=>`<tr><td><a href="${BASE}players/${p.slug}/">${p.name}</a></td><td>${p.birth_year||'<span class="muted">缺失</span>'}</td><td>${p.position}</td><td>${p.current_club}</td><td><span class="badge ${r?.relation_status||'pending'}">${r?.relation_status||'pending'}</span></td><td>${s?.national_team_level||'<span class="muted">未记录</span>'}</td><td>${s?.selection_date||'<span class="muted">缺失</span>'}</td><td>${s?.event_name||'<span class="muted">缺失</span>'}</td><td>${src?`<span class="badge">${src.source_priority}</span>`:'<span class="muted">缺失</span>'}</td><td><span class="badge ${s?.confidence||'low'}">${s?.confidence||'low'}</span></td><td><span class="badge ${p.verification_status}">${p.verification_status}</span></td><td class="evidence"><a href="${BASE}players/${p.slug}/">详情</a>${src?`<a href="${src.url}" target="_blank" rel="noopener">来源</a>`:''}</td><td>${p.notes||''}</td></tr>`).join('')||'<tr><td colspan="13">没有符合筛选条件的记录。</td></tr>'}function renderCharts(){const d=state.data;const byYear={};confirmedPlayers().forEach(p=>{if(!p.birth_year)return;(d.selectionByPlayer[p.id]||[]).forEach(s=>{byYear[p.birth_year]??={};byYear[p.birth_year][s.national_team_level]=(byYear[p.birth_year][s.national_team_level]||0)+1})});const maxYear=Math.max(1,...Object.values(byYear).map(o=>Object.values(o).reduce((a,b)=>a+b,0)));$('#birthYearChart').innerHTML=Object.entries(byYear).sort().map(([year,levels])=>{const total=Object.values(levels).reduce((a,b)=>a+b,0);return `<div class="bar-row"><strong>${year}</strong><div class="bar-track" title="${year}: ${total}" data-chart-filter="birth_year" data-value="${year}">${Object.entries(levels).map(([lv,c])=>`<span class="bar-seg seg-${lv}" style="width:${c/maxYear*100}%"></span>`).join('')}</div><span>${total}</span></div>`}).join('');const byLevel={};state.data.selections.forEach(s=>{const p=d.players.find(x=>x.id===s.player_id);byLevel[s.national_team_level]??={confirmed:0,pending:0};byLevel[s.national_team_level][p?.verification_status==='confirmed'?'confirmed':'pending']++});const maxLevel=Math.max(1,...Object.values(byLevel).map(o=>o.confirmed+o.pending));$('#levelChart').innerHTML=Object.entries(byLevel).sort().map(([lv,o])=>`<div class="bar-row"><strong>${lv}</strong><div class="bar-track" title="${lv}: confirmed ${o.confirmed}, other ${o.pending}" data-chart-filter="national_team_level" data-value="${lv}"><span class="bar-seg seg-${lv}" style="width:${o.confirmed/maxLevel*100}%"></span><span class="bar-seg" style="background:#fecdca;width:${o.pending/maxLevel*100}%"></span></div><span>${o.confirmed+o.pending}</span></div>`).join('');const byDate={};d.selections.forEach(s=>{const y=(s.selection_date||'未知').slice(0,4);byDate[y]=(byDate[y]||0)+1});const maxDate=Math.max(1,...Object.values(byDate));$('#timelineChart').innerHTML=Object.entries(byDate).sort().map(([y,c])=>`<div class="timeline-bar"><button style="height:${40+c/maxDate*120}px" data-chart-filter="selection_year" data-value="${y}" title="${y}: ${c}">${c}</button><div>${y}</div></div>`).join('');document.querySelectorAll('[data-chart-filter]').forEach(el=>el.addEventListener('click',()=>{if(el.dataset.chartFilter==='selection_year'){state.filters.selection_year=el.dataset.value;renderTable()}else setFilter(el.dataset.chartFilter,el.dataset.value)}))}function exportCsv(){const headers=['name','birth_year','position','club','team_level','selection_date','event','source_priority','confidence','status'];const csv=[headers.join(',')].concat(filteredRows().map(({player:p,selection:s,source:src})=>headers.map(h=>`"${String({name:p.name,birth_year:p.birth_year||'',position:p.position,club:p.current_club,team_level:s?.national_team_level||'',selection_date:s?.selection_date||'',event:s?.event_name||'',source_priority:src?.source_priority||'',confidence:s?.confidence||'',status:p.verification_status}[h]||'').replaceAll('"','""')}"`).join(','))).join('\n');const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='china-football-xiaojiang-filtered.csv';a.click();URL.revokeObjectURL(a.href)}function render(){renderHealth();renderStats();renderFilters();renderTable();renderCharts();$('#resetFilters')?.addEventListener('click',clearFilters);$('#exportCsv')?.addEventListener('click',exportCsv)}loadData();"""
    sources_js = r"""const BASE=document.body.dataset.root||'';fetch(`${BASE}data/sources.json`).then(r=>r.json()).then(sources=>{document.querySelector('#sourceRows').innerHTML=sources.map(s=>`<tr><td>${s.title}</td><td>${s.publisher}</td><td>${s.published_date||'<span class="muted">待补</span>'}</td><td>${s.source_type}</td><td><span class="badge">${s.source_priority}</span></td><td>${s.involved_players.length?s.involved_players.join('、'):'<span class="muted">尚未关联球员</span>'}</td><td>${s.involved_levels.join(' / ')||'<span class="muted">未关联</span>'}</td><td>${s.access_status}</td><td><a href="${s.url}" target="_blank" rel="noopener">打开</a></td><td>${s.archived_url?`<a href="${s.archived_url}">归档</a>`:'<span class="muted">无</span>'}</td></tr>`).join('')});"""
    changelog_js = r"""const BASE=document.body.dataset.root||'';fetch(`${BASE}data/changelog.json`).then(r=>r.json()).then(items=>{document.querySelector('#changelogList').innerHTML=items.map(item=>`<article class="evidence-card"><p class="eyebrow">${item.date}</p><h2>${item.title}</h2><p>${item.reason}</p><p><strong>统计变化：</strong>${Object.entries(item.stat_changes).map(([k,v])=>`${k}: ${v}`).join(' / ')}</p><p><strong>新增来源：</strong>${item.added_sources.length}</p><p><strong>删除或修正：</strong>${item.deleted_or_corrected.length?item.deleted_or_corrected.join('；'):'无'}</p></article>`).join('')});"""
    player_js = r"""const BASE=document.body.dataset.root||'';const slug=document.querySelector('[data-player-slug]').dataset.playerSlug;Promise.all(['players','selections','sources','relations','appearances'].map(n=>fetch(`${BASE}data/${n}.json`).then(r=>r.json()))).then(([players,selections,sources,relations,appearances])=>{const p=players.find(x=>x.slug===slug);const src=Object.fromEntries(sources.map(s=>[s.id,s]));const rels=relations.filter(r=>r.player_id===p.id);const sels=selections.filter(s=>s.player_id===p.id).sort((a,b)=>(a.selection_date||'').localeCompare(b.selection_date||''));const apps=appearances.filter(a=>a.player_id===p.id);const sourceIds=[...new Set([...rels.map(r=>r.source_id),...sels.map(s=>s.source_id),...apps.map(a=>a.source_id)].filter(Boolean))];document.querySelector('#playerDetail').innerHTML=`<div class="detail-grid"><div class="evidence-card"><h2>${p.name}</h2><p><strong>出生年份：</strong>${p.birth_year||'缺失'}</p><p><strong>年龄段：</strong>${p.age_group}</p><p><strong>位置：</strong>${p.position}</p><p><strong>俱乐部/单位：</strong>${p.current_club}</p><p><strong>是否留洋：</strong>${p.is_overseas?'是':'否'}</p><p><strong>验证状态：</strong><span class="badge ${p.verification_status}">${p.verification_status}</span></p><p><strong>同名/异名说明：</strong>${p.aliases?.length?p.aliases.join('、'):'暂无别名记录；identity_key 用于避免仅凭姓名合并。'}</p></div><div class="evidence-card"><h3>中国足球小将经历</h3>${rels.map(r=>`<p><span class="badge ${r.relation_status}">${r.relation_status}</span> ${r.relation_type}<br>${r.evidence_text}<br>${src[r.source_id]?`<a href="${src[r.source_id].url}" target="_blank" rel="noopener">${src[r.source_id].title}</a>`:'缺失来源'}</p>`).join('')||'<p class="muted">缺失</p>'}</div><div class="evidence-card"><h3>国字号入选时间线</h3>${sels.map(s=>`<p><strong>${s.selection_date}</strong> ${s.national_team_level} ${s.selection_type}<br>${s.event_name}<br>${src[s.source_id]?`<a href="${src[s.source_id].url}" target="_blank" rel="noopener">${src[s.source_id].title}</a>`:'缺失来源'}</p>`).join('')||'<p class="muted">缺失</p>'}</div><div class="evidence-card"><h3>比赛出场记录</h3>${apps.length?apps.map(a=>`<p>${a.match_date} ${a.competition}｜首发：${a.starter??'待补'}｜分钟：${a.minutes??'待补'}</p>`).join(''):'<p class="muted">暂无逐场首发、分钟、进球或助攻证据。涉及“出场”的原始记录仅作为线索。</p>'}</div><div class="evidence-card"><h3>相关来源列表</h3>${sourceIds.map(id=>src[id]?`<p><span class="badge">${src[id].source_priority}</span> <a href="${src[id].url}" target="_blank" rel="noopener">${src[id].title}</a></p>`:'').join('')}</div><div class="evidence-card"><h3>待核验信息</h3><p>${p.verification_status==='confirmed'?'暂无核心证据链缺口；仍建议补充逐场出场数据。':'至少一条核心证据链不足，需补充官方或可靠来源。'}</p></div></div>`});"""
    og_cover = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><rect width="1200" height="630" fill="#f7f8fb"/><text x="80" y="190" font-family="Arial,'Noto Sans SC',sans-serif" font-size="58" font-weight="700" fill="#172033">中国足球小将国字号入选数据库</text><text x="80" y="280" font-family="Arial,'Noto Sans SC',sans-serif" font-size="34" fill="#667085">U14-U20 国少国青统计 · 证据链 · 来源库</text><rect x="80" y="360" width="1040" height="110" rx="12" fill="#ffffff" stroke="#d9dee8"/><text x="120" y="430" font-family="Arial,'Noto Sans SC',sans-serif" font-size="34" fill="#1f5eff">Data-driven, auditable, updateable</text></svg>"""
    files = {"styles.css": styles, "app.js": app_js, "sources.js": sources_js, "changelog.js": changelog_js, "player.js": player_js, "og-cover.svg": og_cover}
    for name, content in files.items():
        with open(os.path.join(ASSETS_DIR, name), "w", encoding="utf-8") as f:
            f.write(content)
            f.write("\n")


def main():
    records = read_json(PROCESSED_JSON_FILE)
    players, selections, sources, relations, appearances, _ = build_data(records)
    clean_generated_dirs()
    write_json(os.path.join(DATA_DIR, "players.json"), players)
    write_json(os.path.join(DATA_DIR, "selections.json"), selections)
    write_json(os.path.join(DATA_DIR, "sources.json"), sources)
    write_json(os.path.join(DATA_DIR, "relations.json"), relations)
    write_json(os.path.join(DATA_DIR, "appearances.json"), appearances)
    build_assets()
    build_index()
    build_sources_page()
    build_changelog_page(players, selections, sources, relations)
    build_methodology_page()
    build_player_pages(players)
    print(f"Built site with {len(players)} players, {len(selections)} selections, {len(sources)} sources, {len(relations)} relations, {len(appearances)} appearances.")


if __name__ == "__main__":
    main()
