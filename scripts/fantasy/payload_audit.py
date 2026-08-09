"""Audit every cached match payload before Fantasy outputs are generated."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dataset_config import DatasetConfig, load_dataset, load_payload_audit_expectations, load_validation_expectations


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


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _lookup(root: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = root
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _league_path(raw_dir: Path, league_id: int) -> Path:
    namespaced = raw_dir / "leagues" / f"{league_id}.json"
    return namespaced if namespaced.exists() else raw_dir / f"league_{league_id}_matches.json"


def _roster_metadata(config: DatasetConfig) -> tuple[dict[int, dict[str, Any]], set[int], int]:
    payload = _read_json(config.roster.path)
    players: dict[int, dict[str, Any]] = {}
    team_ids: set[int] = set()
    for team in payload["teams"]:
        team_ids.add(int(team["team_id"]))
        for player in team["players"]:
            players[int(player["account_id"])] = {
                "name": player["name"],
                "team": team["name"],
                "position": player["position"],
                "actualGames": player.get("actualGames"),
            }
    return players, team_ids, len(payload.get("rosterChanges", []))


def audit_payloads(config: DatasetConfig, raw_dir: Path) -> dict[str, Any]:
    expected = load_validation_expectations(config)
    audit_expected = load_payload_audit_expectations(config)
    manifest_ids = list(config.match_source.manifest_match_ids or ())
    manifest_set = set(manifest_ids)
    errors: list[str] = []

    discovered: set[int] = set()
    league_rows = 0
    for league_id in config.match_source.league_ids:
        payload = _read_json(_league_path(raw_dir, league_id))
        if not isinstance(payload, list):
            errors.append(f"League {league_id} cache is not an array")
            continue
        league_rows += len(payload)
        discovered.update(
            int(row["match_id"])
            for row in payload
            if isinstance(row, dict) and isinstance(row.get("match_id"), int)
        )
    discovered -= config.match_source.excluded_match_ids
    if manifest_ids and discovered != manifest_set:
        errors.append(
            "League index differs from frozen manifest: "
            f"missing={sorted(manifest_set - discovered)}, unexpected={sorted(discovered - manifest_set)}"
        )

    matches: list[dict[str, Any]] = []
    missing_payloads: list[int] = []
    invalid_payloads: list[int] = []
    for match_id in manifest_ids or sorted(discovered):
        path = raw_dir / "matches" / f"{match_id}.json"
        if not path.exists():
            missing_payloads.append(match_id)
            continue
        match = _read_json(path)
        if not isinstance(match, dict) or match.get("match_id") != match_id:
            invalid_payloads.append(match_id)
            continue
        matches.append(match)
    if missing_payloads:
        errors.append(f"Missing match payloads: {missing_payloads}")
    if invalid_payloads:
        errors.append(f"Invalid match payloads: {invalid_payloads}")

    roster_players, roster_team_ids, roster_change_count = _roster_metadata(config)
    roster_accounts = set(roster_players)
    account_games: Counter[int] = Counter()
    payload_team_ids: set[int] = set()
    player_count_issues: list[dict[str, int]] = []
    parsed_match_ids: list[int] = []
    wrong_league_ids: list[int] = []
    series_ids: set[int] = set()
    durations: list[int] = []
    starts: list[int] = []
    source_field_missing: Counter[str] = Counter()
    teamfight_outliers: list[dict[str, Any]] = []
    negative_stuns: list[dict[str, Any]] = []
    first_blood_anomalies: list[dict[str, Any]] = []
    objective_types: Counter[str] = Counter()
    roshan_player_total = 0
    tormentor_rows = 0
    tormentor_total = 0
    smoke_rows = 0
    smoke_total = 0
    madstone_rows = 0
    madstone_total = 0
    watcher_paths = 0
    lotus_paths = 0

    required_rules = [
        rule
        for rule in config.ruleset.rules.values()
        if rule.raw_formula != "unavailable"
    ]
    for match in matches:
        match_id = int(match["match_id"])
        if match.get("leagueid") not in config.match_source.league_ids:
            wrong_league_ids.append(match_id)
        if match.get("version") is not None and isinstance(match.get("od_data"), dict) and match["od_data"].get("has_parsed") is True:
            parsed_match_ids.append(match_id)
        if isinstance(match.get("series_id"), int) and match["series_id"] > 0:
            series_ids.add(int(match["series_id"]))
        if isinstance(match.get("duration"), int):
            durations.append(int(match["duration"]))
        if isinstance(match.get("start_time"), int):
            starts.append(int(match["start_time"]))
        for key in ("radiant_team_id", "dire_team_id"):
            if isinstance(match.get(key), int):
                payload_team_ids.add(int(match[key]))

        objectives = match.get("objectives") if isinstance(match.get("objectives"), list) else []
        for objective in objectives:
            if isinstance(objective, dict) and isinstance(objective.get("type"), str):
                objective_types[objective["type"]] += 1
        first_blood_objectives = sum(
            1
            for objective in objectives
            if isinstance(objective, dict) and "FIRSTBLOOD" in str(objective.get("type", "")).upper()
        )

        players = match.get("players") if isinstance(match.get("players"), list) else []
        if len(players) != config.match_source.expected_players_per_match:
            player_count_issues.append({"matchId": match_id, "players": len(players)})
        claimed = 0
        for player in players:
            if not isinstance(player, dict):
                continue
            account_id = player.get("account_id")
            if isinstance(account_id, int):
                account_games[account_id] += 1
            for rule in required_rules:
                for source_path in rule.source_paths:
                    if rule.missing_leaf_means_zero and len(source_path) > 1:
                        value = _lookup(player, source_path[:-1])
                        label = ".".join(source_path[:-1])
                    else:
                        value = _lookup(player, source_path)
                        label = ".".join(source_path)
                    if value is None:
                        source_field_missing[label] += 1

            teamfight = player.get("teamfight_participation")
            if isinstance(teamfight, (int, float)) and not isinstance(teamfight, bool) and (teamfight < 0 or teamfight > 1):
                teamfight_outliers.append({"matchId": match_id, "accountId": account_id, "value": teamfight})
            stun = player.get("stuns")
            if isinstance(stun, (int, float)) and not isinstance(stun, bool) and stun < 0:
                negative_stuns.append({"matchId": match_id, "accountId": account_id, "value": stun})
            claimed_value = player.get("firstblood_claimed")
            if claimed_value is True or claimed_value == 1:
                claimed += 1
            roshan = player.get("roshans_killed")
            if isinstance(roshan, int):
                roshan_player_total += roshan
            killed = player.get("killed") if isinstance(player.get("killed"), dict) else {}
            tormentor = killed.get("npc_dota_miniboss")
            if isinstance(tormentor, int):
                tormentor_rows += 1
                tormentor_total += tormentor
            item_uses = player.get("item_uses") if isinstance(player.get("item_uses"), dict) else {}
            smoke = item_uses.get("smoke_of_deceit")
            if isinstance(smoke, int):
                smoke_rows += 1
                smoke_total += smoke
            madstone = item_uses.get("madstone_bundle")
            if isinstance(madstone, int):
                madstone_rows += 1
                madstone_total += madstone
            watcher_paths += sum("watcher" in str(key).lower() for key in item_uses)
            lotus_paths += sum("lotus" in str(key).lower() for key in item_uses)
        if match.get("first_blood_time", 0) > 0 and (claimed != 1 or first_blood_objectives != 1):
            first_blood_anomalies.append(
                {
                    "matchId": match_id,
                    "firstBloodTime": match.get("first_blood_time"),
                    "claimedPlayers": claimed,
                    "objectiveEvents": first_blood_objectives,
                }
            )

    payload_accounts = set(account_games)
    games_mismatches = [
        {
            "accountId": account_id,
            "player": metadata["name"],
            "expected": metadata["actualGames"],
            "actual": account_games.get(account_id, 0),
        }
        for account_id, metadata in roster_players.items()
        if metadata["actualGames"] is not None and metadata["actualGames"] != account_games.get(account_id, 0)
    ]
    first_blood_override_ids = set(config.metric_availability_overrides.get("first_blood", {}))
    first_blood_anomaly_ids = {row["matchId"] for row in first_blood_anomalies}
    expected_roshan_objectives = sum(
        count for objective_type, count in objective_types.items() if "ROSHAN_KILL" in objective_type.upper()
    )

    exact_checks = {
        "manifestMatches": (len(manifest_ids), expected.get("matchesDiscovered")),
        "payloadMatches": (len(matches), expected.get("matchesProcessed")),
        "playerMatchRows": (sum(account_games.values()), expected.get("playerMatchRows")),
        "uniqueAccountIds": (len(payload_accounts), audit_expected.get("uniqueAccountIds")),
        "parsedMatches": (len(parsed_match_ids), audit_expected.get("parsedMatches")),
        "series": (len(series_ids), audit_expected.get("series")),
        "teamfightOutOfRangeRows": (len(teamfight_outliers), audit_expected.get("teamfightOutOfRangeRows")),
        "negativeStunRows": (len(negative_stuns), audit_expected.get("negativeStunRows")),
    }
    for label, (actual, wanted) in exact_checks.items():
        if wanted is not None and actual != wanted:
            errors.append(f"{label} differs: {actual} != {wanted}")
    if wrong_league_ids:
        errors.append(f"Match payloads use an unexpected league ID: {wrong_league_ids}")
    if player_count_issues:
        errors.append(f"Match player counts differ from 10: {player_count_issues}")
    if payload_accounts != roster_accounts:
        errors.append(
            "Payload accounts differ from final roster: "
            f"missing={sorted(roster_accounts - payload_accounts)}, unexpected={sorted(payload_accounts - roster_accounts)}"
        )
    if payload_team_ids != roster_team_ids:
        errors.append(
            "Payload teams differ from final roster: "
            f"missing={sorted(roster_team_ids - payload_team_ids)}, unexpected={sorted(payload_team_ids - roster_team_ids)}"
        )
    if games_mismatches:
        errors.append(f"Roster actualGames mismatches: {games_mismatches}")
    if source_field_missing:
        errors.append(f"Required Fantasy source fields are missing: {dict(source_field_missing)}")
    if first_blood_anomaly_ids != first_blood_override_ids:
        errors.append(
            "First Blood anomaly set differs from the dataset availability policy: "
            f"audit={sorted(first_blood_anomaly_ids)}, policy={sorted(first_blood_override_ids)}"
        )
    if roshan_player_total != expected_roshan_objectives:
        errors.append(
            f"Roshan player attribution total differs from objectives: {roshan_player_total} != {expected_roshan_objectives}"
        )

    return {
        **config.provenance,
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "scope": {
            "leagueRows": league_rows,
            "manifestMatches": len(manifest_ids),
            "payloadMatches": len(matches),
            "playerMatchRows": sum(account_games.values()),
            "uniqueAccountIds": len(payload_accounts),
            "teams": len(payload_team_ids),
            "series": len(series_ids),
            "parsedMatches": len(parsed_match_ids),
            "minimumDuration": min(durations) if durations else None,
            "maximumDuration": max(durations) if durations else None,
            "firstStartTime": min(starts) if starts else None,
            "lastStartTime": max(starts) if starts else None,
        },
        "roster": {
            "configuredPlayers": len(roster_accounts),
            "configuredTeams": len(roster_team_ids),
            "rosterChanges": roster_change_count,
            "missingAccounts": sorted(roster_accounts - payload_accounts),
            "unexpectedAccounts": sorted(payload_accounts - roster_accounts),
            "gamesMismatches": games_mismatches,
        },
        "fieldCoverage": {
            "requiredSourceMissing": dict(source_field_missing),
            "smokeRows": smoke_rows,
            "smokeTotal": smoke_total,
            "madstoneCandidateRows": madstone_rows,
            "madstoneCandidateTotal": madstone_total,
            "watcherItemUsePaths": watcher_paths,
            "lotusItemUsePaths": lotus_paths,
            "tormentorRows": tormentor_rows,
            "tormentorTotal": tormentor_total,
            "roshanPlayerTotal": roshan_player_total,
            "roshanObjectiveEvents": expected_roshan_objectives,
            "objectiveTypes": dict(sorted(objective_types.items())),
        },
        "anomalies": {
            "firstBlood": first_blood_anomalies,
            "firstBloodPolicyMatchIds": sorted(first_blood_override_ids),
            "teamfightParticipation": teamfight_outliers,
            "negativeStuns": negative_stuns,
            "matchPlayerCount": player_count_issues,
        },
    }


def audit_markdown(audit: dict[str, Any]) -> str:
    scope = audit["scope"]
    roster = audit["roster"]
    fields = audit["fieldCoverage"]
    anomalies = audit["anomalies"]
    lines = [
        "# TI14 OpenDota Payload Audit",
        "",
        f"- 状态：**{audit['status'].upper()}**",
        f"- Dataset：`{audit['datasetId']}`",
        f"- Match source：`{audit['matchSourceId']}`",
        f"- Ruleset：`{audit['rulesetId']}`",
        "",
        "## 范围与完整性",
        "",
        "| 检查 | 结果 |",
        "|---|---:|",
        f"| Frozen manifest matches | {scope['manifestMatches']} |",
        f"| Cached payload matches | {scope['payloadMatches']} |",
        f"| Player-match rows | {scope['playerMatchRows']} |",
        f"| Unique account IDs | {scope['uniqueAccountIds']} |",
        f"| Teams | {scope['teams']} |",
        f"| Series | {scope['series']} |",
        f"| Parsed matches | {scope['parsedMatches']} |",
        f"| Duration range (seconds) | {scope['minimumDuration']}–{scope['maximumDuration']} |",
        "",
        "## Roster / account_id",
        "",
        f"- Final ranking roster：{roster['configuredPlayers']} players / {roster['configuredTeams']} teams。",
        f"- Structured roster changes：{roster['rosterChanges']}。",
        f"- Missing account IDs：`{roster['missingAccounts']}`。",
        f"- Unexpected account IDs：`{roster['unexpectedAccounts']}`。",
        f"- Per-player game-count mismatches：`{roster['gamesMismatches']}`。",
        "",
        "## Fantasy 字段兼容性",
        "",
        "- `kills` / `deaths` / `last_hits + denies` / `gold_per_min`：available。",
        "- `tower_kills` / `obs_placed` / `camps_stacked` / `rune_pickups` / `roshans_killed` / `teamfight_participation` / `stuns` / `courier_kills` / `firstblood_claimed` / smokes：parsed-only。",
        "- Madstones / Watchers / Lotuses：unavailable，继续沿用 `ti15-base-v1` 的 null 语义。",
        "- Tormentor：`killed.npc_dota_miniboss`，继续标记 medium reliability。",
        f"- Required source-field missing counts：`{fields['requiredSourceMissing']}`。",
        f"- Smokes：{fields['smokeRows']} rows / total {fields['smokeTotal']}。",
        f"- Madstone candidate（不计分）：{fields['madstoneCandidateRows']} rows / total {fields['madstoneCandidateTotal']}。",
        f"- Tormentor candidate：{fields['tormentorRows']} rows / total {fields['tormentorTotal']}。",
        f"- Roshan attribution cross-check：players {fields['roshanPlayerTotal']} / objectives {fields['roshanObjectiveEvents']}。",
        "",
        "## 已隔离异常",
        "",
        f"- First Blood attribution 缺失：{len(anomalies['firstBlood'])} matches；policy IDs = `{anomalies['firstBloodPolicyMatchIds']}`。",
        f"- Teamfight participation 越界：{len(anomalies['teamfightParticipation'])} rows。",
        f"- Negative stun duration：{len(anomalies['negativeStuns'])} rows。",
        "- 上述异常均作为 unavailable 隔离，不归零、不 clamp、不修改 Fantasy constants。",
        "",
        "## 错误",
        "",
        "无。" if not audit["errors"] else "\n".join(f"- {error}" for error in audit["errors"]),
        "",
    ]
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", help="Dataset ID; defaults to the registry default.")
    result.add_argument("--raw-dir", type=Path, help="Override the configured match-source cache directory.")
    result.add_argument("--json-output", type=Path)
    result.add_argument("--markdown-output", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        config = load_dataset(args.dataset)
        raw_dir = args.raw_dir or config.match_source.raw_dir_for_processing()
        audit = audit_payloads(config, raw_dir)
        json_output = args.json_output or config.paths.payload_audit_json
        markdown_output = args.markdown_output or config.paths.payload_audit_markdown
        _write_json(json_output, audit)
        _write_text(markdown_output, audit_markdown(audit))
        print(
            f"Payload audit {audit['status']}: matches={audit['scope']['payloadMatches']}, "
            f"rows={audit['scope']['playerMatchRows']}, accounts={audit['scope']['uniqueAccountIds']}"
        )
        print(f"Reports: {json_output}, {markdown_output}")
        if audit["errors"]:
            for error in audit["errors"]:
                print(f"  {error}", file=sys.stderr)
            return 1
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
