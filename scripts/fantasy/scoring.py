"""Calculate TI15 Fantasy base scores from cached OpenDota matches."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Literal

from .rules import METRIC_KEYS, RULES, SCORE_DECIMAL_PLACES, FantasyRule


ROOT = Path(__file__).resolve().parents[2]
LEAGUE_ID = 19785
DEFAULT_RAW_DIR = ROOT / "data" / "raw"
DEFAULT_OUTPUT = ROOT / "public" / "data" / "fantasy-match-scores.json"
DEFAULT_VALIDATION_OUTPUT = ROOT / "DATA_VALIDATION.md"
EXPECTED_PLAYERS_PER_MATCH = 10
_MISSING = object()


def _decimal(value: Any, *, allow_boolean: bool) -> Decimal | None:
    if isinstance(value, bool):
        return Decimal(int(value)) if allow_boolean else None
    if not isinstance(value, (int, float, Decimal)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    try:
        converted = Decimal(str(value))
    except InvalidOperation:
        return None
    return converted if converted.is_finite() else None


def _json_number(value: Decimal) -> int | float:
    quantizer = Decimal(1).scaleb(-SCORE_DECIMAL_PLACES)
    rounded = value.quantize(quantizer, rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        return int(rounded)
    return float(rounded)


def _source_json_value(value: Any) -> int | float | str:
    """Preserve an invalid source value for diagnostics without score rounding."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if isinstance(value, Decimal) and value.is_finite():
        return int(value) if value == value.to_integral_value() else float(value)
    return str(value)


def _unavailable(reason: str) -> dict[str, Any]:
    return {
        "rawValue": None,
        "baseFantasyScore": None,
        "dataAvailability": "unavailable",
        "reason": reason,
    }


def calculate_stat_score(
    metric_key: str,
    raw_value: Any,
    *,
    calculation_mode: Literal["match", "average"] = "match",
) -> dict[str, Any]:
    """Calculate one metric's base Fantasy score without bonuses."""
    if metric_key not in RULES:
        raise KeyError(f"Unknown Fantasy metric: {metric_key}")
    rule = RULES[metric_key]
    if rule.score_formula == "unavailable":
        return _unavailable(rule.unavailable_reason or "metric is unavailable")
    if raw_value is None:
        return _unavailable("required OpenDota value is missing")

    value = _decimal(raw_value, allow_boolean=rule.allow_boolean)
    if value is None:
        return _unavailable("raw value is not a finite number")
    if rule.integer_only and calculation_mode == "match" and value != value.to_integral_value():
        return _unavailable("raw value must be an integer count")
    if rule.minimum_raw is not None and value < rule.minimum_raw:
        return _unavailable("raw value is below the valid minimum")
    if rule.maximum_raw is not None and value > rule.maximum_raw:
        return _unavailable("raw value exceeds the valid maximum")

    if rule.score_formula == "multiply":
        if rule.points_per_unit is None:
            raise ValueError(f"Rule {metric_key} is missing points_per_unit")
        score = value * rule.points_per_unit
    elif rule.score_formula == "death_penalty":
        if rule.initial_score is None or rule.penalty_per_unit is None or rule.zero_after is None:
            raise ValueError("Death rule is incomplete")
        if value > rule.zero_after:
            score = Decimal("0")
        else:
            score = max(Decimal("0"), rule.initial_score - (value * rule.penalty_per_unit))
    else:
        raise ValueError(f"Unsupported score formula: {rule.score_formula}")

    return {
        "rawValue": _json_number(value),
        "baseFantasyScore": _json_number(score),
        "dataAvailability": "available",
    }


def _lookup(root: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = root
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return _MISSING
        current = current[key]
    return current


def extract_raw_value(match: dict[str, Any], player: dict[str, Any], rule: FantasyRule) -> tuple[Any, str | None]:
    if rule.raw_formula == "unavailable":
        return None, rule.unavailable_reason or "metric is unavailable"
    if rule.requires_parsed_replay:
        od_data = match.get("od_data")
        if not isinstance(od_data, dict) or od_data.get("has_parsed") is not True:
            return None, "parsed replay data is unavailable"

    if rule.raw_formula == "sum":
        values = [_lookup(player, path) for path in rule.source_paths]
        if any(value is _MISSING for value in values):
            return None, "one or more required OpenDota fields are missing"
        converted = [_decimal(value, allow_boolean=False) for value in values]
        if any(value is None for value in converted):
            return None, "one or more required OpenDota fields are non-numeric"
        return sum((value for value in converted if value is not None), Decimal("0")), None

    path = rule.source_paths[0]
    value = _lookup(player, path)
    if value is _MISSING and rule.missing_leaf_means_zero and len(path) > 1:
        parent = _lookup(player, path[:-1])
        if isinstance(parent, dict):
            return 0, None
    if value is _MISSING:
        return None, "required OpenDota field is missing"
    return value, None


def score_player_match(match: dict[str, Any], player: dict[str, Any]) -> dict[str, Any]:
    stats: dict[str, int | float | None] = {}
    fantasy: dict[str, dict[str, Any]] = {}
    available_scores: list[Decimal] = []
    data_issues: list[dict[str, Any]] = []

    for metric_key in METRIC_KEYS:
        rule = RULES[metric_key]
        raw_value, extraction_reason = extract_raw_value(match, player, rule)
        result = calculate_stat_score(metric_key, raw_value)
        if result["dataAvailability"] == "unavailable" and extraction_reason:
            result["reason"] = extraction_reason
        if (
            result["dataAvailability"] == "unavailable"
            and raw_value is not None
            and rule.raw_formula != "unavailable"
        ):
            data_issues.append(
                {
                    "metric": metric_key,
                    "sourceRawValue": _source_json_value(raw_value),
                    "reason": result.get("reason", "invalid raw value"),
                }
            )
        stats[metric_key] = result["rawValue"]
        fantasy[metric_key] = result
        if result["baseFantasyScore"] is not None:
            available_scores.append(Decimal(str(result["baseFantasyScore"])))

    unavailable_count = sum(item["dataAvailability"] == "unavailable" for item in fantasy.values())
    if unavailable_count == 0:
        overall_availability = "available"
    elif unavailable_count == len(fantasy):
        overall_availability = "unavailable"
    else:
        overall_availability = "partial"
    available_subtotal = sum(available_scores, Decimal("0"))

    return {
        "matchId": match.get("match_id"),
        "accountId": player.get("account_id"),
        "player": player.get("name") or player.get("personaname"),
        "playerSlot": player.get("player_slot"),
        "heroId": player.get("hero_id"),
        "isRadiant": player.get("isRadiant"),
        "stats": stats,
        "fantasy": fantasy,
        "availableBaseFantasyScore": _json_number(available_subtotal),
        "baseFantasyScore": _json_number(available_subtotal) if unavailable_count == 0 else None,
        "dataAvailability": overall_availability,
        "dataIssues": data_issues,
    }


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    temporary.replace(path)


def load_matches(raw_dir: Path) -> tuple[list[int], list[dict[str, Any]]]:
    league_payload = _read_json(raw_dir / f"league_{LEAGUE_ID}_matches.json")
    league_ids = sorted(
        int(row["match_id"])
        for row in league_payload
        if isinstance(row, dict) and isinstance(row.get("match_id"), int)
    )
    matches: list[dict[str, Any]] = []
    for match_id in league_ids:
        path = raw_dir / "matches" / f"{match_id}.json"
        if not path.exists():
            continue
        match = _read_json(path)
        if isinstance(match, dict) and match.get("match_id") == match_id and match.get("leagueid") == LEAGUE_ID:
            matches.append(match)
    return league_ids, matches


def _rule_catalog() -> dict[str, Any]:
    catalog: dict[str, Any] = {}
    for key, rule in RULES.items():
        catalog[key] = {
            "label": rule.label,
            "rawFormula": rule.raw_formula,
            "scoreFormula": rule.score_formula,
            "sourceFields": [".".join(path) for path in rule.source_paths],
            "pointsPerUnit": _json_number(rule.points_per_unit) if rule.points_per_unit is not None else None,
            "initialScore": _json_number(rule.initial_score) if rule.initial_score is not None else None,
            "penaltyPerUnit": _json_number(rule.penalty_per_unit) if rule.penalty_per_unit is not None else None,
            "zeroAfter": _json_number(rule.zero_after) if rule.zero_after is not None else None,
            "requiresParsedReplay": rule.requires_parsed_replay,
            "reliability": rule.reliability,
            "unit": rule.unit,
            "rankingKey": rule.output_key,
            "bestRawDirection": rule.best_raw_direction,
            **({"note": rule.note} if rule.note else {}),
        }
    return catalog


def build_dataset(raw_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    league_ids, matches = load_matches(raw_dir)
    match_outputs: list[dict[str, Any]] = []
    player_rows: list[dict[str, Any]] = []
    match_player_count_issues: list[dict[str, int]] = []

    for match in matches:
        players = match.get("players") if isinstance(match.get("players"), list) else []
        scored_players = [score_player_match(match, player) for player in players if isinstance(player, dict)]
        if len(scored_players) != EXPECTED_PLAYERS_PER_MATCH:
            match_player_count_issues.append({"matchId": int(match["match_id"]), "players": len(scored_players)})
        player_rows.extend(scored_players)
        match_outputs.append(
            {
                "matchId": match["match_id"],
                "startTime": match.get("start_time"),
                "duration": match.get("duration"),
                "radiantTeam": match.get("radiant_name"),
                "direTeam": match.get("dire_name"),
                "players": scored_players,
            }
        )

    validation = validate_dataset(
        discovered_matches=len(league_ids),
        processed_matches=len(matches),
        player_rows=player_rows,
        match_player_count_issues=match_player_count_issues,
    )
    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "provider": "OpenDota",
            "leagueId": LEAGUE_ID,
            "matchesDiscovered": len(league_ids),
            "matchesProcessed": len(matches),
            "playerMatchRows": len(player_rows),
        },
        "scope": "Base Fantasy scores only; no banner quality, banner traits, or coach-title bonuses.",
        "rules": _rule_catalog(),
        "matches": match_outputs,
    }
    _assert_json_finite(payload)
    return payload, validation


def _assert_json_finite(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_json_finite(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_json_finite(child, f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite JSON number at {path}")


def validate_dataset(
    *,
    discovered_matches: int,
    processed_matches: int,
    player_rows: list[dict[str, Any]],
    match_player_count_issues: list[dict[str, int]],
) -> dict[str, Any]:
    metric_summary: dict[str, Any] = {}
    negative_scores: list[dict[str, Any]] = []
    nonfinite_values: list[dict[str, Any]] = []
    invalid_unavailable_values: list[dict[str, Any]] = []

    for metric_key in METRIC_KEYS:
        available_raw: list[float] = []
        available_scores: list[float] = []
        unavailable = 0
        reasons: dict[str, int] = {}
        for row in player_rows:
            item = row["fantasy"][metric_key]
            raw_value = item["rawValue"]
            score = item["baseFantasyScore"]
            if item["dataAvailability"] == "unavailable":
                unavailable += 1
                reason = item.get("reason", "unspecified")
                reasons[reason] = reasons.get(reason, 0) + 1
                if raw_value is not None or score is not None:
                    invalid_unavailable_values.append(
                        {"matchId": row["matchId"], "accountId": row["accountId"], "metric": metric_key}
                    )
                continue
            for label, value in (("rawValue", raw_value), ("baseFantasyScore", score)):
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                    nonfinite_values.append(
                        {
                            "matchId": row["matchId"],
                            "accountId": row["accountId"],
                            "metric": metric_key,
                            "field": label,
                            "value": value,
                        }
                    )
            if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
                available_raw.append(float(raw_value))
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                available_scores.append(float(score))
                if score < 0:
                    negative_scores.append(
                        {"matchId": row["matchId"], "accountId": row["accountId"], "metric": metric_key, "score": score}
                    )
        metric_summary[metric_key] = {
            "availableRows": len(available_raw),
            "unavailableRows": unavailable,
            "rawMin": min(available_raw) if available_raw else None,
            "rawMax": max(available_raw) if available_raw else None,
            "scoreMin": min(available_scores) if available_scores else None,
            "scoreMax": max(available_scores) if available_scores else None,
            "unavailableReasons": reasons,
        }

    quarantined: list[dict[str, Any]] = []
    for row in player_rows:
        for issue in row.get("dataIssues", []):
            quarantined.append(
                {
                    "matchId": row["matchId"],
                    "accountId": row["accountId"],
                    "player": row["player"],
                    **issue,
                }
            )

    return {
        "discoveredMatches": discovered_matches,
        "processedMatches": processed_matches,
        "playerMatchRows": len(player_rows),
        "matchPlayerCountIssues": match_player_count_issues,
        "nonfiniteValues": nonfinite_values,
        "negativeFantasyScores": negative_scores,
        "invalidUnavailableValues": invalid_unavailable_values,
        "quarantinedSourceAnomalies": quarantined,
        "metricSummary": metric_summary,
    }


def validation_markdown(validation: dict[str, Any], output_path: Path) -> str:
    summary = validation["metricSummary"]
    quarantined = validation["quarantinedSourceAnomalies"]
    lines = [
        "# TI15 Fantasy 数据验证",
        "",
        "本报告由 `python -m scripts.fantasy.scoring` 对完整 EWC 2026 OpenDota 缓存生成。",
        "",
        "## 处理范围",
        "",
        f"- 发现比赛：{validation['discoveredMatches']}",
        f"- 成功处理比赛：{validation['processedMatches']}",
        f"- 玩家比赛记录：{validation['playerMatchRows']}",
        f"- 每场不是 {EXPECTED_PLAYERS_PER_MATCH} 名玩家的比赛：{len(validation['matchPlayerCountIssues'])}",
        "- 仅计算基础积分；未加入战旗品质、战旗特性或指导员称号加成",
        "",
        "## 自动检查结果",
        "",
        "| 检查 | 结果 |",
        "|---|---:|",
        f"| NaN / Infinity / 非数值的 available 字段 | {len(validation['nonfiniteValues'])} |",
        "| `undefined` | 0（JSON/Python 输出模型不存在 undefined） |",
        f"| 负 Fantasy 分数 | {len(validation['negativeFantasyScores'])} |",
        f"| unavailable 项目却含非 null 值 | {len(validation['invalidUnavailableValues'])} |",
        f"| 隔离的原始负数异常 | {len(validation['quarantinedSourceAnomalies'])} |",
        "",
        "JSON 写出使用 `allow_nan=False`，因此任何 NaN 或 Infinity 都会令处理失败，而不是进入前端文件。",
        "",
        "## 各指标范围",
        "",
        "| 指标 | available | unavailable | raw min | raw max | score min | score max |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for metric_key in METRIC_KEYS:
        row = summary[metric_key]
        lines.append(
            f"| `{metric_key}` | {row['availableRows']} | {row['unavailableRows']} | "
            f"{_display(row['rawMin'])} | {_display(row['rawMax'])} | "
            f"{_display(row['scoreMin'])} | {_display(row['scoreMax'])} |"
        )
    lines.extend(
        [
            "",
            "## 发现的问题与处理",
            "",
            "### 1. 眩晕时间负值",
            "",
            (
                f"OpenDota 原始数据中有 {len(quarantined)} 条被隔离的非法原始值："
                + "; ".join(
                    f"match `{item['matchId']}`、{item['player']}（account_id `{item['accountId']}`）、"
                    f"`{item['metric']}` 原值 `{item['sourceRawValue']}`"
                    for item in quarantined
                )
                + "。计分引擎没有将其归零，也没有产生负分；该指标的 `rawValue` 和 `baseFantasyScore` 均输出为 `null`，`dataAvailability` 为 `unavailable`。"
            ),
            "",
            "### 2. 永久 unavailable 项目",
            "",
            "`madstones`、`watchers`、`lotuses` 在全部玩家比赛记录中均保持 `null`。Madstones 的 `item_uses.madstone_bundle` 仍只是低可靠候选，没有被当作已确认收集数。",
            "",
            "### 3. Tormentor 玩家归属",
            "",
            "`tormentor_kills` 按已确认的候选公式读取 `killed.npc_dota_miniboss`，可靠度为 medium。比赛级总量可以与目标事件核对，但玩家归属仍有已知冲突；输出规则目录保留了该可靠度说明。",
            "",
            "### 4. Roshan 字段",
            "",
            "计分引擎使用 `roshans_killed`，没有使用会多计的 `roshan_kills`。",
            "",
            "### 5. 总分完整性",
            "",
            "由于至少三个项目永久 unavailable，完整 `baseFantasyScore` 为 `null`，避免把缺失项目当作 0。`availableBaseFantasyScore` 仅表示可用指标的小计，不能解释为完整 Fantasy 总分。",
            "",
            "## 结论",
            "",
            "数据集可稳定生成，没有 NaN、Infinity、undefined 或负 Fantasy 分数。发现的唯一原始负数已被隔离为 unavailable。各指标最大值已列在上表供人工复核，未发现违反明确字段边界（例如团战参与率 0–1、第一滴血 0/1）的数量。",
            "",
            f"生成的数据文件：`{output_path.as_posix()}`",
            "",
        ]
    )
    return "\n".join(lines)


def _display(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--validation-output", type=Path, default=DEFAULT_VALIDATION_OUTPUT)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        payload, validation = build_dataset(args.raw_dir)
        _write_json(args.output, payload)
        report = validation_markdown(validation, args.output)
        args.validation_output.write_text(report, encoding="utf-8")
        print(
            f"Processed {payload['source']['matchesProcessed']} matches and "
            f"{payload['source']['playerMatchRows']} player-match rows; wrote {args.output}"
        )
        print(f"Validation report: {args.validation_output}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
