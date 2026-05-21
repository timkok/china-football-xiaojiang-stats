# 中国足球小将国字号入选数据库

本项目把“中国足球小将国字号入选统计与可视化”从静态展示页升级为一个可审计、可筛选、可持续更新的静态数据产品。核心原则是：统计数字必须来自 `data/*.json` 自动汇总，任何核心结论都能追溯到球员、关系、入选记录和来源。

线上地址：

```text
https://timkok.github.io/china-football-xiaojiang-stats/
```

## 项目目标

- 记录中国足球小将相关球员入选 U14-U20 等各级国字号队伍的公开信息。
- 为每名球员保留两条证据链：小将关系证据、国字号入选证据。
- 区分 `confirmed`、`partially_confirmed`、`pending`、`disputed`，避免把线索当作结论。
- 支持筛选、搜索、来源核验、球员详情页、来源库和变更日志。

## 数据结构

核心数据位于 `data/`：

- `players.json`：球员主表，含 `id`、`name`、`slug`、`aliases`、`birth_year`、`age_group`、`position`、`current_club`、`listed_club`、`nationality`、`verification_status`、证据 ID。
- `relations.json`：中国足球小将关系证据，含 `relation_type`、`relation_status`、`source_id`、`evidence_text`、`confidence`。
- `selections.json`：国字号入选记录，含 `national_team_level`、`official_team_name`、`selection_type`、`selection_date`、`event_name`、`listed_club`、`source_id`、`confidence`。
- `sources.json`：来源库，含 `title`、`url`、`publisher`、`source_type`、`source_priority`、`published_date`、`retrieved_at`、`archived_url`、`reliability_score`。
- `appearances.json`：逐场出场证据。目前为空；没有逐场首发、分钟、进球、助攻证据时，不生成“主力”结论。
- `changelog.json`：每次数据结构、来源、状态和统计变化记录。

## 数据口径

- 首页所有统计数字由浏览器读取 `players.json`、`selections.json`、`sources.json`、`relations.json`、`appearances.json` 后自动汇总。
- “已确认国字号球员”只统计 `players.verification_status = confirmed`。
- “2009 年龄段入选”“2010 年龄段入选”只统计 `confirmed` 且 `birth_year` 对应的唯一球员。
- “U17 亚洲杯相关入选/出场球员”只统计 `confirmed` 且 `selections.event_name` 包含 U17 亚洲杯的唯一球员。本项目不再使用缺少逐场证据的“主力”表述。
- 出生年份分布不统计 `birth_year` 缺失球员。
- `pending` 保留为线索，不计入首页核心确认人数。

## 验证状态

- `confirmed`：至少有一条 confirmed 小将关系记录，并且至少有一条 high 或 medium confidence 的国字号入选记录。
- `partially_confirmed`：两条证据链都存在，但至少一侧较弱或仍需补强。
- `pending`：只有媒体线索、社媒线索、二手资料，或缺少核心证据链。
- `disputed`：信息冲突，需要人工复核。

## 来源优先级

- `official_cfa`：中国足协官网。
- `official_team`：中国之队、亚足联、FIFA 等官方机构。
- `club`：俱乐部、学校、地方足协。
- `xiaojiang_official`：中国足球小将官方账号、董路公开确认。
- `mainstream_media`：主流媒体报道。
- `social`：社媒、视频平台、球迷整理。
- `unknown`：来源不明确。

## 如何新增球员

1. 在上游数据源或 `data/processed/players_clean.json` 添加球员基础信息。
2. 同时补充小将关系来源和国字号入选来源。
3. 运行 `npm run build` 重新生成结构化数据和静态页面。
4. 运行 `npm run validate:data`。

## 如何新增来源

优先补充中国足协、中国之队、亚足联、FIFA、俱乐部或学校等官方来源。每个来源必须有 URL、标题、发布机构、来源优先级、发布日期或待补说明。

## 如何修改验证状态

不要直接为展示效果修改状态。状态应由证据强度决定：

- 补齐 confirmed 小将关系证据和 high/medium 国字号入选证据后，才可改为 `confirmed`。
- 一侧证据不足时使用 `partially_confirmed` 或 `pending`。
- 同名、年份、俱乐部或位置冲突时使用 `disputed`，并在 notes 说明。

## 本地开发

```bash
npm install
npm run build
python3 -m http.server 8765
```

打开：

```text
http://localhost:8765/
```

## 数据校验

```bash
npm run validate:data
```

校验覆盖：

- confirmed 球员必须有强小将关系证据和强国字号入选证据。
- `selection_date` 不能为空。
- `national_team_level` 必须属于允许枚举。
- `source_id` 必须能在 `sources.json` 找到。
- `official_cfa` URL 必须包含 `thecfa.cn`。
- “主力”“首发”“进球”“助攻”等标签必须有 `appearances.json` 证据。
- 同名球员不能只靠 `name` 合并。
- pending 不能计入首页 confirmed 统计。

## 构建和部署 GitHub Pages

```bash
npm run build
npm run validate:data
git add .
git commit -m "Improve auditable china football database"
git push origin main
```

GitHub Pages 从 `main` 分支发布后，访问：

```text
https://timkok.github.io/china-football-xiaojiang-stats/
```

## 如何提交纠错

请提供：

- 球员姓名、出生年份、位置或俱乐部，用于避免同名误合并。
- 需要修改的字段。
- 来源 URL、标题、发布机构、发布时间。
- 证据摘录，以及该证据支持的是小将关系、国字号入选还是出场记录。

## 当前已知数据缺口

- `appearances.json` 当前为空，缺少逐场首发、分钟、进球、助攻等比赛技术统计。
- 仍有部分球员只具备小将关系证据，缺少可核验国字号入选证据。
- 部分媒体来源缺少准确发布日期和归档链接。
- 来源可访问性目前标记为 `unchecked`，后续可加入自动 HEAD 检查或归档状态检查。
