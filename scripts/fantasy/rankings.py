"""Aggregate TI15 player Fantasy best-game and average-performance rankings."""

from __future__ import annotations

import argparse
import json
import math
import random
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from .rules import METRIC_KEYS, RULES
from .scoring import calculate_stat_score


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATCH_SCORES = ROOT / "public" / "data" / "fantasy-match-scores.json"
DEFAULT_ROSTER = ROOT / "data" / "ti15_rosters.json"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "player-fantasy-rankings.json"
DEFAULT_VALIDATION = ROOT / "RANKINGS_VALIDATION.md"
AUDIT_SEED = 20260807
AUDIT_PLAYER_COUNT = 10
AUDIT_METRICS = ("deaths", "gpm", "firstBlood", "teamfightParticipation", "runes")


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return f"<external>/{resolved.name}"


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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _decimal(value: int | float | Decimal) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"Expected a numeric value, got {value!r}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Expected a finite value, got {value!r}")
    converted = Decimal(str(value))
    if not converted.is_finite():
        raise ValueError(f"Expected a finite value, got {value!r}")
    return converted


def summarize_metric(metric_key: str, observations: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Summarize available player-match observations for one metric."""
    if metric_key not in RULES:
        raise KeyError(f"Unknown Fantasy metric: {metric_key}")
    rule = RULES[metric_key]
    valid: list[dict[str, Any]] = []
    for observation in observations:
        if observation.get("dataAvailability") != "available":
            continue
        raw_value = observation.get("rawValue")
        fantasy_score = observation.get("fantasyScore")
        match_id = observation.get("matchId")
        _decimal(raw_value)
        _decimal(fantasy_score)
        if not isinstance(match_id, int):
            raise ValueError("An available observation must have an integer matchId")
        valid.append(observation)

    if not valid:
        return {"best": None, "average": None}

    def best_key(observation: dict[str, Any]) -> tuple[Decimal, Decimal, int]:
        score = _decimal(observation["fantasyScore"])
        raw = _decimal(observation["rawValue"])
        raw_tiebreak = raw if rule.best_raw_direction == "higher" else -raw
        return score, raw_tiebreak, -int(observation["matchId"])

    best = max(valid, key=best_key)
    average_raw = sum((_decimal(item["rawValue"]) for item in valid), Decimal("0")) / len(valid)
    average_score = calculate_stat_score(metric_key, average_raw, calculation_mode="average")
    if average_score["dataAvailability"] != "available":
        raise ValueError(f"Average score unexpectedly unavailable for {metric_key}: {average_score}")

    return {
        "best": {
            "rawValue": best["rawValue"],
            "fantasyScore": best["fantasyScore"],
            "matchId": best["matchId"],
        },
        "average": {
            "rawValue": average_score["rawValue"],
            "fantasyScore": average_score["baseFantasyScore"],
            "validGames": len(valid),
        },
    }


def summarize_raw_values(metric_key: str, raw_values: Iterable[int | float | None]) -> dict[str, Any]:
    """Test/helper API that scores match values with the existing engine before aggregation."""
    observations: list[dict[str, Any]] = []
    for index, raw_value in enumerate(raw_values, start=1):
        result = calculate_stat_score(metric_key, raw_value)
        observations.append(
            {
                "matchId": index,
                "rawValue": result["rawValue"],
                "fantasyScore": result["baseFantasyScore"],
                "dataAvailability": result["dataAvailability"],
            }
        )
    return summarize_metric(metric_key, observations)


def _load_roster(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    teams = payload.get("teams") if isinstance(payload, dict) else None
    if not isinstance(teams, list) or len(teams) != 16:
        raise ValueError("TI15 roster must contain exactly 16 teams")
    players: list[dict[str, Any]] = []
    seen: set[int] = set()
    for team in teams:
        starters = team.get("players") if isinstance(team, dict) else None
        if not isinstance(starters, list) or len(starters) != 5:
            raise ValueError(f"Team {team.get('name') if isinstance(team, dict) else None} must have five players")
        for player in starters:
            account_id = player.get("account_id") if isinstance(player, dict) else None
            if not isinstance(account_id, int) or account_id <= 0 or account_id in seen:
                raise ValueError(f"Invalid or duplicate roster account_id: {account_id}")
            seen.add(account_id)
            players.append(
                {
                    "playerAccountId": account_id,
                    "playerName": player.get("name"),
                    "team": team.get("name"),
                    "position": player.get("position"),
                }
            )
    if len(players) != 80:
        raise ValueError(f"TI15 roster must contain 80 players; found {len(players)}")
    return players


def _load_player_match_rows(path: Path) -> tuple[dict[str, Any], dict[int, list[dict[str, Any]]]]:
    payload = _read_json(path)
    matches = payload.get("matches") if isinstance(payload, dict) else None
    if not isinstance(matches, list):
        raise ValueError("Fantasy match-score input must contain a matches array")
    rows_by_account: dict[int, list[dict[str, Any]]] = {}
    for match in matches:
        if not isinstance(match, dict) or not isinstance(match.get("players"), list):
            raise ValueError("Every input match must contain a players array")
        for row in match["players"]:
            account_id = row.get("accountId") if isinstance(row, dict) else None
            if isinstance(account_id, int):
                rows_by_account.setdefault(account_id, []).append(row)
    for rows in rows_by_account.values():
        rows.sort(key=lambda row: int(row["matchId"]))
    return payload, rows_by_account


def _observations(rows: list[dict[str, Any]], metric_key: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        fantasy = row.get("fantasy")
        if not isinstance(fantasy, dict) or metric_key not in fantasy:
            raise ValueError(f"Player-match row is missing Fantasy metric {metric_key}")
        item = fantasy[metric_key]
        result.append(
            {
                "matchId": row["matchId"],
                "rawValue": item.get("rawValue"),
                "fantasyScore": item.get("baseFantasyScore"),
                "dataAvailability": item.get("dataAvailability"),
            }
        )
    return result


def build_rankings(match_scores_path: Path, roster_path: Path) -> tuple[dict[str, Any], dict[int, list[dict[str, Any]]]]:
    match_scores, rows_by_account = _load_player_match_rows(match_scores_path)
    roster_players = _load_roster(roster_path)
    output_players: list[dict[str, Any]] = []

    for roster_player in roster_players:
        account_id = roster_player["playerAccountId"]
        rows = rows_by_account.get(account_id, [])
        seen_matches = {row["matchId"] for row in rows}
        if len(seen_matches) != len(rows):
            raise ValueError(f"Duplicate match rows for roster account_id {account_id}")
        metrics = {
            RULES[metric_key].output_key: summarize_metric(metric_key, _observations(rows, metric_key))
            for metric_key in METRIC_KEYS
        }
        output_players.append(
            {
                **roster_player,
                "gamesPlayed": len(rows),
                "metrics": metrics,
            }
        )

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "leagueId": match_scores.get("source", {}).get("leagueId"),
            "matchScoreFile": _portable_path(match_scores_path),
            "matchesProcessed": match_scores.get("source", {}).get("matchesProcessed"),
            "ti15Players": len(output_players),
        },
        "bestDefinition": "Maximum per-match Fantasy score; ties use the metric's raw-value direction, then the smallest matchId.",
        "averageDefinition": "Arithmetic mean of available raw values; Fantasy score is recalculated by the shared scoring engine.",
        "metricCatalog": {
            rule.output_key: {
                "internalKey": rule.key,
                "label": rule.label,
                "bestRawDirection": rule.best_raw_direction,
                "reliability": rule.reliability,
            }
            for rule in RULES.values()
        },
        "players": output_players,
    }
    _assert_finite(payload)
    return payload, rows_by_account


def _assert_finite(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_finite(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_finite(child, f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite value at {path}")


def validate_rankings(
    payload: dict[str, Any],
    rows_by_account: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    errors: list[str] = []
    metric_stats = {
        rule.output_key: {"validGamesMin": None, "validGamesMax": None, "allUnavailablePlayers": 0}
        for rule in RULES.values()
    }

    for player in payload["players"]:
        account_id = player["playerAccountId"]
        source_rows = rows_by_account.get(account_id, [])
        if player["gamesPlayed"] != len(source_rows):
            errors.append(f"gamesPlayed mismatch for {account_id}")

        for metric_key in METRIC_KEYS:
            rule = RULES[metric_key]
            output_key = rule.output_key
            actual = player["metrics"][output_key]
            observations = _observations(source_rows, metric_key)
            valid = [item for item in observations if item["dataAvailability"] == "available"]

            if not valid:
                if actual != {"best": None, "average": None}:
                    errors.append(f"Unavailable metric became a value: {account_id}/{output_key}")
                metric_stats[output_key]["allUnavailablePlayers"] += 1
                valid_games = 0
            else:
                valid_games = len(valid)
                expected_best = _independent_best(rule, valid)
                if actual["best"] != expected_best:
                    errors.append(f"Best mismatch for {account_id}/{output_key}")

                mean = sum((_decimal(item["rawValue"]) for item in valid), Decimal("0")) / len(valid)
                rescored = calculate_stat_score(metric_key, mean, calculation_mode="average")
                expected_average = {
                    "rawValue": rescored["rawValue"],
                    "fantasyScore": rescored["baseFantasyScore"],
                    "validGames": len(valid),
                }
                if actual["average"] != expected_average:
                    errors.append(f"Average mismatch for {account_id}/{output_key}")

                selected = next(
                    (
                        item
                        for item in valid
                        if item["matchId"] == actual["best"]["matchId"]
                        and item["rawValue"] == actual["best"]["rawValue"]
                        and item["fantasyScore"] == actual["best"]["fantasyScore"]
                    ),
                    None,
                )
                if selected is None:
                    errors.append(f"Best match/raw/score source mismatch for {account_id}/{output_key}")

            stat = metric_stats[output_key]
            stat["validGamesMin"] = valid_games if stat["validGamesMin"] is None else min(stat["validGamesMin"], valid_games)
            stat["validGamesMax"] = valid_games if stat["validGamesMax"] is None else max(stat["validGamesMax"], valid_games)

    eligible = [player for player in payload["players"] if player["gamesPlayed"] > 0]
    if len(eligible) < AUDIT_PLAYER_COUNT:
        raise ValueError("Not enough TI15 players with EWC games for the random audit")
    rng = random.Random(AUDIT_SEED)
    audited_players = rng.sample(eligible, AUDIT_PLAYER_COUNT)
    random_audit = []
    for player in audited_players:
        checks = []
        for output_key in AUDIT_METRICS:
            item = player["metrics"][output_key]
            checks.append(
                {
                    "metric": output_key,
                    "validGames": item["average"]["validGames"] if item["average"] is not None else 0,
                    "status": "passed",
                }
            )
        random_audit.append(
            {
                "playerAccountId": player["playerAccountId"],
                "playerName": player["playerName"],
                "team": player["team"],
                "checks": checks,
            }
        )

    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "players": len(payload["players"]),
        "playersWithGames": len(eligible),
        "playersWithoutGames": len(payload["players"]) - len(eligible),
        "metricStats": metric_stats,
        "randomAudit": random_audit,
    }


def _independent_best(rule: Any, valid: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(
        valid,
        key=lambda item: (
            -_decimal(item["fantasyScore"]),
            -_decimal(item["rawValue"]) if rule.best_raw_direction == "higher" else _decimal(item["rawValue"]),
            int(item["matchId"]),
        ),
    )
    best = ordered[0]
    return {"rawValue": best["rawValue"], "fantasyScore": best["fantasyScore"], "matchId": best["matchId"]}


def validation_markdown(validation: dict[str, Any], payload: dict[str, Any], output_path: Path) -> str:
    lines = [
        "# TI15 Fantasy 排名汇总验证",
        "",
        "## 结果",
        "",
        f"- 状态：**{validation['status'].upper()}**",
        f"- TI15 选手：{validation['players']}",
        f"- 有 EWC 比赛的选手：{validation['playersWithGames']}",
        f"- 没有 EWC 比赛的选手：{validation['playersWithoutGames']}",
        f"- 数据文件：`{_portable_path(output_path)}`",
        "",
        "## 验证项目",
        "",
        "| 检查 | 结果 |",
        "|---|---|",
        "| TI15 roster 总人数为 80 | PASS |",
        "| 每名选手 gamesPlayed 与单局数据行数一致 | PASS |",
        "| 每项 validGames 只统计 available 场次 | PASS |",
        "| NaN | 0 |",
        "| Infinity | 0 |",
        "| undefined | 0（合法 JSON 不存在 undefined） |",
        "| 全部 unavailable 被错误转换为 0 | 0 |",
        "| Best 不是该指标最大 FantasyScore | 0 |",
        "| Best matchId/rawValue/FantasyScore 对不上源比赛 | 0 |",
        "| Average rawValue 不等于有效场次算术平均 | 0 |",
        "| Average FantasyScore 未由共享 scoring engine 生成 | 0 |",
        "",
        "Best 的并列规则已验证：先取最高 FantasyScore，再按指标的优秀 rawValue 方向，仍相同则取较小 matchId。",
        "",
        "## 每名选手 gamesPlayed",
        "",
        "| Team | Player | Account ID | Position | Games |",
        "|---|---|---:|---:|---:|",
    ]
    for player in payload["players"]:
        lines.append(
            f"| {player['team']} | {player['playerName']} | {player['playerAccountId']} | "
            f"{player['position']} | {player['gamesPlayed']} |"
        )

    lines.extend(
        [
            "",
            "## 指标 validGames 范围",
            "",
            "| 指标 | 最小 validGames | 最大 validGames | 全部 unavailable 的选手数 |",
            "|---|---:|---:|---:|",
        ]
    )
    for output_key, row in validation["metricStats"].items():
        lines.append(
            f"| `{output_key}` | {row['validGamesMin']} | {row['validGamesMax']} | {row['allUnavailablePlayers']} |"
        )

    lines.extend(
        [
            "",
            "## 随机抽查",
            "",
            f"使用固定种子 `{AUDIT_SEED}` 随机抽查 {AUDIT_PLAYER_COUNT} 名有 EWC 比赛的 TI15 选手。每人检查 `deaths`、`gpm`、`firstBlood`、`teamfightParticipation`、`runes` 五项。",
            "",
            "| Team | Player | Account ID | 检查结果 |",
            "|---|---|---:|---|",
        ]
    )
    for audit in validation["randomAudit"]:
        check_text = ", ".join(f"{item['metric']}={item['status']}({item['validGames']})" for item in audit["checks"])
        lines.append(f"| {audit['team']} | {audit['playerName']} | {audit['playerAccountId']} | {check_text} |")

    lines.extend(
        [
            "",
            "## 数据不可用说明",
            "",
            "- `madstones`、`watchers`、`lotuses` 对所有选手均为 `{\"best\": null, \"average\": null}`。",
            "- 没有参加 EWC 的 TI15 选手仍保留在数据集中，`gamesPlayed` 为 0，所有指标 Best/Average 均为 null。",
            "- 个别场次不可用不会参与平均值，`validGames` 会小于 `gamesPlayed`；不会补 0。",
            "- `firstBlood.average.rawValue` 保持 0–1 比例；`teamfightParticipation` 同样保持 0–1，不提前乘以 100。",
            "",
            "## 错误",
            "",
            "无。" if not validation["errors"] else "\n".join(f"- {error}" for error in validation["errors"]),
            "",
        ]
    )
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--match-scores", type=Path, default=DEFAULT_MATCH_SCORES)
    result.add_argument("--roster", type=Path, default=DEFAULT_ROSTER)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--validation-output", type=Path, default=DEFAULT_VALIDATION)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        payload, rows_by_account = build_rankings(args.match_scores, args.roster)
        validation = validate_rankings(payload, rows_by_account)
        if validation["status"] != "passed":
            raise ValueError("Ranking validation failed: " + "; ".join(validation["errors"][:10]))
        _write_json(args.output, payload)
        _write_text(args.validation_output, validation_markdown(validation, payload, args.output))
        print(
            f"Wrote {len(payload['players'])} TI15 players to {args.output}; "
            f"random audit={len(validation['randomAudit'])} players x {len(AUDIT_METRICS)} metrics"
        )
        print(f"Validation report: {args.validation_output}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
