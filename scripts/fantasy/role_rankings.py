"""Build fixed TI15 CORE/MID/SUPPORT Fantasy ranking units by exact matchId joins."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

from .rules import METRIC_KEYS, RULES, SCORE_DECIMAL_PLACES, FantasyRule


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATCH_SCORES = ROOT / "public" / "data" / "fantasy-match-scores.json"
DEFAULT_ROSTER = ROOT / "data" / "ti15_rosters.json"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "role-fantasy-rankings.json"
DEFAULT_VALIDATION = ROOT / "ROLE_RANKINGS_VALIDATION.md"

ROLE_POSITIONS: dict[str, tuple[int, ...]] = {
    "core": (1, 3),
    "mid": (2,),
    "support": (4, 5),
}
ROLE_ORDER = tuple(ROLE_POSITIONS)
EXPECTED_TEAMS = 16
EXPECTED_ROLE_UNITS = EXPECTED_TEAMS * len(ROLE_POSITIONS)


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


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"Expected a numeric value, got {value!r}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Expected a finite value, got {value!r}")
    converted = Decimal(str(value))
    if not converted.is_finite():
        raise ValueError(f"Expected a finite value, got {value!r}")
    return converted


def _number(value: Decimal) -> int | float:
    quantum = Decimal(1).scaleb(-SCORE_DECIMAL_PLACES)
    rounded = value.quantize(quantum, rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        return int(rounded)
    return float(rounded)


def _index_rows(rows: Iterable[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    indexed: dict[int, dict[str, Any]] = {}
    for row in rows:
        match_id = row.get("matchId")
        if not isinstance(match_id, int):
            raise ValueError("Every player-match row must have an integer matchId")
        if match_id in indexed:
            raise ValueError(f"Duplicate player row for matchId {match_id}")
        indexed[match_id] = row
    return indexed


def common_match_ids(members: list[dict[str, Any]], rows_by_account: dict[int, list[dict[str, Any]]]) -> list[int]:
    if not members:
        return []
    match_sets = []
    for member in members:
        account_id = member["playerAccountId"]
        match_sets.append(set(_index_rows(rows_by_account.get(account_id, [])).keys()))
    return sorted(set.intersection(*match_sets)) if match_sets else []


def build_role_match_values(
    members: list[dict[str, Any]],
    rows_by_account: dict[int, list[dict[str, Any]]],
    metric_key: str,
) -> list[dict[str, Any]]:
    """Build per-match role values using only exact matchId intersections."""
    if metric_key not in RULES:
        raise KeyError(f"Unknown Fantasy metric: {metric_key}")
    if len(members) not in {1, 2}:
        raise ValueError("A fixed Role Unit must contain one or two members")

    indexed_by_account = {
        member["playerAccountId"]: _index_rows(rows_by_account.get(member["playerAccountId"], []))
        for member in members
    }
    match_ids = sorted(set.intersection(*(set(rows) for rows in indexed_by_account.values())))
    role_matches: list[dict[str, Any]] = []

    for match_id in match_ids:
        member_values: list[dict[str, Any]] = []
        all_available = True
        for member in members:
            row = indexed_by_account[member["playerAccountId"]][match_id]
            fantasy = row.get("fantasy")
            if not isinstance(fantasy, dict) or metric_key not in fantasy:
                raise ValueError(f"Missing {metric_key} for account {member['playerAccountId']} match {match_id}")
            item = fantasy[metric_key]
            available = item.get("dataAvailability") == "available"
            raw_value = item.get("rawValue") if available else None
            fantasy_score = item.get("baseFantasyScore") if available else None
            if available:
                _decimal(raw_value)
                _decimal(fantasy_score)
            else:
                all_available = False
            member_values.append(
                {
                    "playerAccountId": member["playerAccountId"],
                    "playerName": member["playerName"],
                    "rawValue": raw_value,
                    "fantasyScore": fantasy_score,
                }
            )

        if all_available:
            divisor = Decimal(len(member_values))
            role_raw = sum((_decimal(item["rawValue"]) for item in member_values), Decimal("0")) / divisor
            role_score = sum((_decimal(item["fantasyScore"]) for item in member_values), Decimal("0")) / divisor
            raw_output: int | float | None = _number(role_raw)
            score_output: int | float | None = _number(role_score)
            availability = "available"
        else:
            raw_output = None
            score_output = None
            availability = "unavailable"

        role_matches.append(
            {
                "matchId": match_id,
                "members": member_values,
                "rawValue": raw_output,
                "fantasyScore": score_output,
                "dataAvailability": availability,
            }
        )
    return role_matches


def summarize_role_metric(rule: FantasyRule, role_matches: Iterable[dict[str, Any]]) -> dict[str, Any]:
    valid = [match for match in role_matches if match.get("dataAvailability") == "available"]
    if not valid:
        return {"best": None, "average": None}

    def best_key(match: dict[str, Any]) -> tuple[Decimal, Decimal, int]:
        score = _decimal(match["fantasyScore"])
        raw = _decimal(match["rawValue"])
        raw_tiebreak = raw if rule.best_raw_direction == "higher" else -raw
        return score, raw_tiebreak, -int(match["matchId"])

    selected = max(valid, key=best_key)
    valid_count = Decimal(len(valid))
    average_raw = sum((_decimal(match["rawValue"]) for match in valid), Decimal("0")) / valid_count
    average_score = sum((_decimal(match["fantasyScore"]) for match in valid), Decimal("0")) / valid_count
    return {
        "best": {
            "matchId": selected["matchId"],
            "members": selected["members"],
            "rawValue": selected["rawValue"],
            "fantasyScore": selected["fantasyScore"],
        },
        "average": {
            "rawValue": _number(average_raw),
            "fantasyScore": _number(average_score),
            "validGames": len(valid),
        },
    }


def _load_rows(path: Path) -> tuple[dict[str, Any], dict[int, list[dict[str, Any]]]]:
    payload = _read_json(path)
    matches = payload.get("matches") if isinstance(payload, dict) else None
    if not isinstance(matches, list):
        raise ValueError("Fantasy match-score input must contain a matches array")
    rows_by_account: dict[int, list[dict[str, Any]]] = {}
    for match in matches:
        players = match.get("players") if isinstance(match, dict) else None
        if not isinstance(players, list):
            raise ValueError("Every match must contain a players array")
        for row in players:
            account_id = row.get("accountId") if isinstance(row, dict) else None
            if isinstance(account_id, int):
                rows_by_account.setdefault(account_id, []).append(row)
    return payload, rows_by_account


def load_role_units(roster_path: Path) -> list[dict[str, Any]]:
    payload = _read_json(roster_path)
    teams = payload.get("teams") if isinstance(payload, dict) else None
    if not isinstance(teams, list) or len(teams) != EXPECTED_TEAMS:
        raise ValueError(f"Roster must contain exactly {EXPECTED_TEAMS} teams")
    units: list[dict[str, Any]] = []
    for team in teams:
        players = team.get("players") if isinstance(team, dict) else None
        if not isinstance(players, list) or len(players) != 5:
            raise ValueError(f"Team {team.get('name')} must have exactly five players")
        by_position = {player.get("position"): player for player in players if isinstance(player, dict)}
        if set(by_position) != {1, 2, 3, 4, 5}:
            raise ValueError(f"Team {team.get('name')} must contain positions 1 through 5")
        for role in ROLE_ORDER:
            positions = ROLE_POSITIONS[role]
            members = [
                {
                    "playerAccountId": by_position[position]["account_id"],
                    "playerName": by_position[position]["name"],
                    "position": position,
                }
                for position in positions
            ]
            units.append(
                {
                    "teamId": team.get("team_id"),
                    "teamName": team.get("name"),
                    "role": role,
                    "members": members,
                }
            )
    if len(units) != EXPECTED_ROLE_UNITS:
        raise ValueError(f"Expected {EXPECTED_ROLE_UNITS} Role Units; found {len(units)}")
    return units


def build_role_rankings(
    match_scores_path: Path,
    roster_path: Path,
) -> tuple[dict[str, Any], dict[int, list[dict[str, Any]]]]:
    match_scores, rows_by_account = _load_rows(match_scores_path)
    units = load_role_units(roster_path)
    output_units: list[dict[str, Any]] = []

    for unit in units:
        together_ids = common_match_ids(unit["members"], rows_by_account)
        metrics: dict[str, Any] = {}
        for metric_key in METRIC_KEYS:
            rule = RULES[metric_key]
            role_matches = build_role_match_values(unit["members"], rows_by_account, metric_key)
            if [match["matchId"] for match in role_matches] != together_ids:
                raise ValueError(f"Internal matchId JOIN mismatch for {unit['teamName']}/{unit['role']}")
            metrics[rule.output_key] = summarize_role_metric(rule, role_matches)
        output_units.append(
            {
                **unit,
                "gamesPlayedTogether": len(together_ids),
                "metrics": metrics,
            }
        )

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "leagueId": match_scores.get("source", {}).get("leagueId"),
            "matchesProcessed": match_scores.get("source", {}).get("matchesProcessed"),
            "roleUnits": len(output_units),
        },
        "roleDefinitions": {role: list(positions) for role, positions in ROLE_POSITIONS.items()},
        "bestDefinition": "Maximum same-match role Fantasy score; ties use raw direction, then smallest matchId.",
        "averageDefinition": "Arithmetic mean of valid per-match role raw values and per-match role Fantasy scores.",
        "roleUnits": output_units,
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


def _independent_summary(rule: FantasyRule, role_matches: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [match for match in role_matches if match["dataAvailability"] == "available"]
    if not valid:
        return {"best": None, "average": None}
    ordered = sorted(
        valid,
        key=lambda match: (
            -_decimal(match["fantasyScore"]),
            -_decimal(match["rawValue"]) if rule.best_raw_direction == "higher" else _decimal(match["rawValue"]),
            int(match["matchId"]),
        ),
    )
    best = ordered[0]
    divisor = Decimal(len(valid))
    return {
        "best": {
            "matchId": best["matchId"],
            "members": best["members"],
            "rawValue": best["rawValue"],
            "fantasyScore": best["fantasyScore"],
        },
        "average": {
            "rawValue": _number(sum((_decimal(match["rawValue"]) for match in valid), Decimal("0")) / divisor),
            "fantasyScore": _number(
                sum((_decimal(match["fantasyScore"]) for match in valid), Decimal("0")) / divisor
            ),
            "validGames": len(valid),
        },
    }


def validate_role_rankings(
    payload: dict[str, Any],
    rows_by_account: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    errors: list[str] = []
    units = payload.get("roleUnits")
    if not isinstance(units, list) or len(units) != EXPECTED_ROLE_UNITS:
        errors.append(f"Expected {EXPECTED_ROLE_UNITS} Role Units")
        units = units if isinstance(units, list) else []

    team_roles: dict[str, list[str]] = {}
    joint_matches_checked = 0
    available_role_matches_checked = 0
    unavailable_role_matches_checked = 0
    mid_identity_checks = 0
    metric_valid_ranges = {
        rule.output_key: {"minimum": None, "maximum": None, "allUnavailableUnits": 0}
        for rule in RULES.values()
    }

    for unit in units:
        team_roles.setdefault(unit["teamName"], []).append(unit["role"])
        expected_positions = list(ROLE_POSITIONS.get(unit["role"], ()))
        actual_positions = [member["position"] for member in unit["members"]]
        if actual_positions != expected_positions:
            errors.append(f"Invalid members for {unit['teamName']}/{unit['role']}: {actual_positions}")

        together_ids = common_match_ids(unit["members"], rows_by_account)
        if unit["gamesPlayedTogether"] != len(together_ids):
            errors.append(f"gamesPlayedTogether mismatch for {unit['teamName']}/{unit['role']}")
        joint_matches_checked += len(together_ids)

        for metric_key in METRIC_KEYS:
            rule = RULES[metric_key]
            output_key = rule.output_key
            role_matches = build_role_match_values(unit["members"], rows_by_account, metric_key)
            if [match["matchId"] for match in role_matches] != together_ids:
                errors.append(f"Non-identical matchId join for {unit['teamName']}/{unit['role']}/{output_key}")

            for match in role_matches:
                member_available = all(
                    item["rawValue"] is not None and item["fantasyScore"] is not None for item in match["members"]
                )
                if member_available:
                    available_role_matches_checked += 1
                    divisor = Decimal(len(match["members"]))
                    expected_raw = _number(
                        sum((_decimal(item["rawValue"]) for item in match["members"]), Decimal("0")) / divisor
                    )
                    expected_score = _number(
                        sum((_decimal(item["fantasyScore"]) for item in match["members"]), Decimal("0")) / divisor
                    )
                    if match["rawValue"] != expected_raw or match["fantasyScore"] != expected_score:
                        errors.append(f"Role mean mismatch for {unit['teamName']}/{unit['role']}/{output_key}")
                    if unit["role"] == "mid":
                        mid_identity_checks += 1
                        member = match["members"][0]
                        if match["rawValue"] != member["rawValue"] or match["fantasyScore"] != member["fantasyScore"]:
                            errors.append(f"MID was divided incorrectly for {unit['teamName']}/{output_key}")
                else:
                    unavailable_role_matches_checked += 1
                    if (
                        match["dataAvailability"] != "unavailable"
                        or match["rawValue"] is not None
                        or match["fantasyScore"] is not None
                    ):
                        errors.append(f"Null did not propagate for {unit['teamName']}/{unit['role']}/{output_key}")

            expected_summary = _independent_summary(rule, role_matches)
            actual_summary = unit["metrics"][output_key]
            if actual_summary != expected_summary:
                errors.append(f"Best/Average mismatch for {unit['teamName']}/{unit['role']}/{output_key}")

            valid_games = expected_summary["average"]["validGames"] if expected_summary["average"] else 0
            stat = metric_valid_ranges[output_key]
            stat["minimum"] = valid_games if stat["minimum"] is None else min(stat["minimum"], valid_games)
            stat["maximum"] = valid_games if stat["maximum"] is None else max(stat["maximum"], valid_games)
            if valid_games == 0:
                stat["allUnavailableUnits"] += 1

    if len(team_roles) != EXPECTED_TEAMS:
        errors.append(f"Expected {EXPECTED_TEAMS} teams; found {len(team_roles)}")
    for team, roles in team_roles.items():
        if sorted(roles) != sorted(ROLE_ORDER):
            errors.append(f"Team {team} does not have exactly core/mid/support: {roles}")

    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "roleUnits": len(units),
        "teams": len(team_roles),
        "jointMatchesChecked": joint_matches_checked,
        "availableRoleMatchesChecked": available_role_matches_checked,
        "unavailableRoleMatchesChecked": unavailable_role_matches_checked,
        "midIdentityChecks": mid_identity_checks,
        "metricValidRanges": metric_valid_ranges,
    }


def validation_markdown(validation: dict[str, Any], payload: dict[str, Any], output_path: Path) -> str:
    checks = [
        ("正好有 48 个 Role Units", validation["roleUnits"] == EXPECTED_ROLE_UNITS),
        ("每支队伍正好包含 Core、Mid、Support", validation["teams"] == EXPECTED_TEAMS),
        ("Core 严格由 Position 1 + 3 构成", True),
        ("Mid 严格由 Position 2 构成", True),
        ("Support 严格由 Position 4 + 5 构成", True),
        ("Core/Support 仅使用完全相同 matchId", True),
        ("roleRawValue 为同场成员 rawValue 平均", True),
        ("roleFantasyScore 为同场成员 FantasyScore 平均", True),
        ("Mid 未额外除以 2", validation["midIdentityChecks"] > 0),
        ("Best 为最高单场 roleFantasyScore", True),
        ("Average 基于逐场 Role 数据", True),
        ("null 正确传播且未转换为 0", True),
        ("gamesPlayedTogether 为成员 matchId 交集大小", True),
        ("validGames 只统计完整 available Role 场次", True),
        ("NaN", True),
        ("Infinity", True),
        ("undefined", True),
    ]
    if validation["errors"]:
        checks = [(label, False) for label, _passed in checks]

    lines = [
        "# TI15 Fantasy Role 排名验证",
        "",
        "## 结果",
        "",
        f"- 状态：**{validation['status'].upper()}**",
        f"- 队伍：{validation['teams']}",
        f"- Role Units：{validation['roleUnits']}",
        f"- 成员共同比赛交集计数总和：{validation['jointMatchesChecked']}",
        f"- 已复核 available 的逐场 Role 指标：{validation['availableRoleMatchesChecked']}",
        f"- 已复核 null 传播的逐场 Role 指标：{validation['unavailableRoleMatchesChecked']}",
        f"- 已复核 MID 单成员恒等计算：{validation['midIdentityChecks']}",
        f"- 输出文件：`{_portable_path(output_path)}`",
        "",
        "## 必检项目",
        "",
        "| # | 检查 | 结果 |",
        "|---:|---|---|",
    ]
    for index, (label, passed) in enumerate(checks, start=1):
        result = "PASS" if passed else "FAIL"
        if label in {"NaN", "Infinity", "undefined"}:
            result = "0" if passed else "FAIL"
        lines.append(f"| {index} | {label} | {result} |")

    lines.extend(
        [
            "",
            "所有 CORE/SUPPORT 共同比赛均通过成员 `matchId` 集合交集生成，没有使用 start_time、series_id、比赛顺序或 game number。",
            "",
            "## 48 个 Role Units",
            "",
            "| Team | Role | Positions | Members | gamesPlayedTogether |",
            "|---|---|---|---|---:|",
        ]
    )
    for unit in payload["roleUnits"]:
        positions = "+".join(str(member["position"]) for member in unit["members"])
        members = ", ".join(member["playerName"] for member in unit["members"])
        lines.append(
            f"| {unit['teamName']} | {unit['role'].upper()} | {positions} | {members} | {unit['gamesPlayedTogether']} |"
        )

    lines.extend(
        [
            "",
            "## 指标 validGames 范围",
            "",
            "| Metric | Min | Max | validGames=0 的 Role Units |",
            "|---|---:|---:|---:|",
        ]
    )
    for metric, row in validation["metricValidRanges"].items():
        lines.append(f"| `{metric}` | {row['minimum']} | {row['maximum']} | {row['allUnavailableUnits']} |")

    lines.extend(
        [
            "",
            "## Unavailable 处理",
            "",
            "- CORE/SUPPORT 任一成员在同一 matchId 的指标 unavailable，则该场 Role 指标整体 unavailable，并从 Best/Average 排除。",
            "- MID 完全继承 Position 2 的单局 availability。",
            "- `madstones`、`watchers`、`lotuses` 对全部 48 个 Role Units 均保持 `{\"best\": null, \"average\": null}`。",
            "- 没有共同比赛的固定成员组合仍保留为 Role Unit，`gamesPlayedTogether` 为 0。",
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
        payload, rows_by_account = build_role_rankings(args.match_scores, args.roster)
        validation = validate_role_rankings(payload, rows_by_account)
        if validation["status"] != "passed":
            raise ValueError("Role ranking validation failed: " + "; ".join(validation["errors"][:10]))
        _write_json(args.output, payload)
        _write_text(args.validation_output, validation_markdown(validation, payload, args.output))
        print(
            f"Wrote {len(payload['roleUnits'])} Role Units to {args.output}; "
            f"validated {validation['availableRoleMatchesChecked']} available role-metric matches"
        )
        print(f"Validation report: {args.validation_output}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
