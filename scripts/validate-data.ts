import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

type Status = "confirmed" | "partially_confirmed" | "pending" | "disputed";
type Confidence = "high" | "medium" | "low";

type Player = {
  id: string;
  name: string;
  slug: string;
  birth_year: number | null;
  position: string;
  current_club: string;
  verification_status: Status;
  relation_ids: string[];
  selection_ids: string[];
  appearance_ids: string[];
  identity_key?: string;
  tags?: string[];
};

type Relation = {
  id: string;
  player_id: string;
  relation_status: Status;
  source_id: string;
  confidence: Confidence;
};

type Selection = {
  id: string;
  player_id: string;
  national_team_level: string;
  selection_type: string;
  selection_date: string;
  source_id: string;
  confidence: Confidence;
  notes?: string;
};

type Source = {
  id: string;
  title: string;
  url: string;
  source_priority: string;
};

type Appearance = {
  id: string;
  player_id: string;
  source_id: string;
  confidence: Confidence;
};

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const allowedLevels = new Set(["U14", "U15", "U16", "U17", "U18", "U19", "U20", "U23", "senior"]);
const errors: string[] = [];
const warnings: string[] = [];

function readJson<T>(fileName: string): T {
  return JSON.parse(fs.readFileSync(path.join(root, "data", fileName), "utf8")) as T;
}

function fail(file: string, id: string, field: string, message: string, fix: string) {
  errors.push(`${file} ${id} ${field}: ${message}。修复：${fix}`);
}

function warn(file: string, id: string, field: string, message: string) {
  warnings.push(`${file} ${id} ${field}: ${message}`);
}

const players = readJson<Player[]>("players.json");
const relations = readJson<Relation[]>("relations.json");
const selections = readJson<Selection[]>("selections.json");
const sources = readJson<Source[]>("sources.json");
const appearances = fs.existsSync(path.join(root, "data", "appearances.json"))
  ? readJson<Appearance[]>("appearances.json")
  : [];

const sourceById = new Map(sources.map((source) => [source.id, source]));
const relationById = new Map(relations.map((relation) => [relation.id, relation]));
const selectionById = new Map(selections.map((selection) => [selection.id, selection]));
const appearanceById = new Map(appearances.map((appearance) => [appearance.id, appearance]));
const relationsByPlayer = new Map<string, Relation[]>();
const selectionsByPlayer = new Map<string, Selection[]>();
const appearancesByPlayer = new Map<string, Appearance[]>();

for (const relation of relations) {
  relationsByPlayer.set(relation.player_id, [...(relationsByPlayer.get(relation.player_id) || []), relation]);
}
for (const selection of selections) {
  selectionsByPlayer.set(selection.player_id, [...(selectionsByPlayer.get(selection.player_id) || []), selection]);
}
for (const appearance of appearances) {
  appearancesByPlayer.set(appearance.player_id, [...(appearancesByPlayer.get(appearance.player_id) || []), appearance]);
}

for (const source of sources) {
  if (!source.url?.trim()) {
    fail("data/sources.json", source.id, "url", "所有 URL 必须非空", "补充原始 URL；无法确认时不要生成 source 记录");
  }
  if (source.source_priority === "official_cfa" && !source.url.includes("thecfa.cn")) {
    fail("data/sources.json", source.id, "source_priority", "official_cfa 来源 URL 应包含 thecfa.cn", "改为正确足协 URL 或降低 source_priority");
  }
}

for (const relation of relations) {
  if (!sourceById.has(relation.source_id)) {
    fail("data/relations.json", relation.id, "source_id", `找不到来源 ${relation.source_id}`, "在 sources.json 中新增来源或修正 source_id");
  }
}

for (const selection of selections) {
  if (!selection.selection_date?.trim()) {
    fail("data/selections.json", selection.id, "selection_date", "selection_date 不能为空", "补充入选通知或赛事名单日期");
  }
  if (!allowedLevels.has(selection.national_team_level)) {
    fail("data/selections.json", selection.id, "national_team_level", `不在允许枚举中：${selection.national_team_level}`, "使用 U14/U15/U16/U17/U18/U19/U20/U23/senior");
  }
  if (!sourceById.has(selection.source_id)) {
    fail("data/selections.json", selection.id, "source_id", `找不到来源 ${selection.source_id}`, "在 sources.json 中新增来源或修正 source_id");
  }
}

for (const appearance of appearances) {
  if (!sourceById.has(appearance.source_id)) {
    fail("data/appearances.json", appearance.id, "source_id", `找不到来源 ${appearance.source_id}`, "在 sources.json 中新增来源或修正 source_id");
  }
}

const names = new Map<string, Player[]>();
for (const player of players) {
  names.set(player.name, [...(names.get(player.name) || []), player]);

  for (const relationId of player.relation_ids) {
    if (!relationById.has(relationId)) {
      fail("data/players.json", player.id, "relation_ids", `找不到关系记录 ${relationId}`, "修正 relation_ids 或新增 relations.json 记录");
    }
  }
  for (const selectionId of player.selection_ids) {
    if (!selectionById.has(selectionId)) {
      fail("data/players.json", player.id, "selection_ids", `找不到入选记录 ${selectionId}`, "修正 selection_ids 或新增 selections.json 记录");
    }
  }
  for (const appearanceId of player.appearance_ids || []) {
    if (!appearanceById.has(appearanceId)) {
      fail("data/players.json", player.id, "appearance_ids", `找不到出场记录 ${appearanceId}`, "修正 appearance_ids 或新增 appearances.json 记录");
    }
  }

  const strongRelation = (relationsByPlayer.get(player.id) || []).some(
    (relation) => relation.relation_status === "confirmed",
  );
  const strongSelection = (selectionsByPlayer.get(player.id) || []).some(
    (selection) => selection.confidence === "high" || selection.confidence === "medium",
  );

  if (player.verification_status === "confirmed" && (!strongRelation || !strongSelection)) {
    fail(
      "data/players.json",
      player.id,
      "verification_status",
      "confirmed 球员必须至少有一条 confirmed 小将关系记录和一条 high/medium confidence 国字号入选记录",
      "补充强证据，或将状态降为 partially_confirmed/pending",
    );
  }

  if ((player.birth_year === null || player.birth_year === undefined) && player.verification_status === "confirmed") {
    warn("data/players.json", player.id, "birth_year", "birth_year 缺失，前端必须排除出生年份统计");
  }

  const sensitiveTags = [
    ...(player.tags || []),
    ...(selectionsByPlayer.get(player.id) || []).map((selection) => selection.selection_type),
  ].filter((tag) => /主力|首发|进球|助攻/.test(tag));
  if (sensitiveTags.length > 0 && (appearancesByPlayer.get(player.id) || []).length === 0) {
    fail(
      "data/players.json",
      player.id,
      "appearance_ids",
      "“主力”“首发”“进球”“助攻”等标签必须有 appearance 或 match evidence",
      "新增 appearances.json 逐场证据，或删除/降级该标签",
    );
  }
}

for (const [name, sameNamePlayers] of names.entries()) {
  if (sameNamePlayers.length > 1) {
    const identityKeys = new Set(
      sameNamePlayers.map((player) => `${player.birth_year || "unknown"}|${player.current_club}|${player.position}|${player.identity_key || ""}`),
    );
    if (identityKeys.size < sameNamePlayers.length) {
      fail(
        "data/players.json",
        name,
        "identity_key",
        "同名球员不能只靠 name 合并，且当前辅助身份字段不足",
        "补充 birth_year、club、position 或明确 identity_key",
      );
    }
  }
}

const confirmedCore = players.filter((player) => player.verification_status === "confirmed");
const pendingInConfirmed = confirmedCore.filter((player) =>
  (relationsByPlayer.get(player.id) || []).some((relation) => relation.relation_status === "pending"),
);
if (pendingInConfirmed.length > 0) {
  warn(
    "data/players.json",
    pendingInConfirmed.map((player) => player.id).join(","),
    "verification_status",
    "confirmed 球员含 pending 关系线索；前端统计只依据 player.verification_status=confirmed",
  );
}

if (errors.length > 0) {
  console.error(`Data validation failed with ${errors.length} error(s):`);
  for (const error of errors) console.error(`- ${error}`);
  if (warnings.length > 0) {
    console.error(`Warnings (${warnings.length}):`);
    for (const warning of warnings) console.error(`- ${warning}`);
  }
  process.exit(1);
}

if (warnings.length > 0) {
  console.warn(`Data validation warnings (${warnings.length}):`);
  for (const warning of warnings) console.warn(`- ${warning}`);
}

console.log(
  `Data validation passed: ${players.length} players, ${selections.length} selections, ${relations.length} relations, ${sources.length} sources, ${appearances.length} appearances.`,
);
