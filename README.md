# 中国足球小将国字号入选统计与分析项目

本项目旨在统计“中国足球小将”各年龄段队员入选中国各级国家队/国字号队伍（U14、U15、U16、U17等）的情况，并生成可供核验的结构化数据表、统计汇总以及可视化 Markdown 报告。

## 项目结构

```text
china_football_xiaojiang/
├── data/
│   ├── raw/                 # 原始抓取数据与失败URL记录
│   └── processed/           # 经过清洗、去重和标准化处理的数据
├── scripts/
│   ├── scrape_sources.py    # 数据采集脚本 (包含容错 fallback 机制)
│   ├── normalize_players.py # 球员姓名纠错、去重与状态标记脚本
│   └── build_reports.py     # 报表统计及 Markdown 报告生成脚本
├── outputs/                 # 生成的最终可核验产物
│   ├── players_national_team_selection.csv # 球员明细数据表
│   ├── summary_by_birth_year.csv          # 按出生年份统计表
│   ├── summary_by_team_level.csv          # 按国字号层级统计表
│   └── report.md                           # 完整核验统计报告
├── README.md                # 项目说明文档
```

## 使用说明与运行复现

### 前置要求
- Python 3.6 或更高版本。
- 本项目仅使用 Python 标准库（如 `json`, `csv`, `urllib` 等），无需额外安装第三方依赖。

### 运行步骤
进入项目根目录 `/Users/tian/.gemini/antigravity/scratch/china_football_xiaojiang` 并在终端依次执行以下命令：

1. **第一步：采集原始数据**
   运行数据采集脚本。该脚本会自动尝试连接中国足协等相关网站获取信息，若网络不通或遇到反爬，将自动降级使用内置的高精度静态结构化缓存，确保数据收集不中断：
   ```bash
   python scripts/scrape_sources.py
   ```

2. **第二步：数据清洗与标准化**
   对采集到的数据进行拼写纠错（如繁简体转换、同音异形字修复）、归一化位置和俱乐部名称，并校验关系与国少数据链：
   ```bash
   python scripts/normalize_players.py
   ```

3. **第三步：生成汇总数据与报告**
   汇总统计并生成最终的 CSV 表格及结构化的 Markdown 报告：
   ```bash
   python scripts/build_reports.py
   ```

## 数据处理细节

- **Spelling Variations**: 自动处理如 “邝兆雷” -> “邝兆镭” 等拼写变体。
- **Confirmation Status**: 
  - `confirmed`: 具有明确的足球小将体系培养记录且有国家队入选双向可查证据。
  - `partially_confirmed`: 证据链存在弱项（单侧来源较弱）。
  - `pending`: 只有部分自媒体报道，但未在正式的足协集训名单中找到记录。
