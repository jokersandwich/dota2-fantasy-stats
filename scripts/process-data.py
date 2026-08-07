#!/usr/bin/env python3
"""Build frontend-ready TI15 player statistics from cached EWC match JSON."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
LEAGUE_ID = 19785
DEFAULT_RAW_DIR = ROOT / "data" / "raw"
DEFAULT_ROSTER = ROOT / "data" / "ti15_rosters.json"
DEFAULT_OUTPUT = ROOT / "public" / "data" / "player-stats.json"
DEFAULT_AUDIT_OUTPUT = ROOT / "data" / "audit" / "latest.json"

Extractor = Callable[[dict[str, Any], dict[str, Any]], float | None]


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    unit: str
    source_fields: tuple[str, ...]
    formula: str
    reliable: bool
    requires_parsed_replay: bool
    extractor: Extractor
    note: str | None = None

    def catalog_entry(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "unit": self.unit,
            "source_fields": list(self.source_fields),
            "formula": self.formula,
            "reliable": self.reliable,
            "requires_parsed_replay": self.requires_parsed_replay,
            **({"note": self.note} if self.note else {}),
        }


def number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        converted = float(value)
        return converted if math.isfinite(converted) else None
    return None


def direct(field: str) -> Extractor:
    return lambda _match, player: number(player.get(field))


def creep_score(_match: dict[str, Any], player: dict[str, Any]) -> float | None:
    last_hits = number(player.get("last_hits"))
    denies = number(player.get("denies"))
    return None if last_hits is None or denies is None else last_hits + denies


def wards(_match: dict[str, Any], player: dict[str, Any]) -> float | None:
    observers = number(player.get("obs_placed"))
    sentries = number(player.get("sen_placed"))
    return None if observers is None or sentries is None else observers + sentries


def smoke_uses(_match: dict[str, Any], player: dict[str, Any]) -> float | None:
    item_uses = player.get("item_uses")
    if not isinstance(item_uses, dict):
        return None
    return number(item_uses.get("smoke_of_deceit", 0))


def unavailable(_match: dict[str, Any], _player: dict[str, Any]) -> None:
    return None


METRICS = (
    MetricSpec("kills", "Kills", "count", ("players[].kills",), "kills", True, False, direct("kills")),
    MetricSpec("deaths", "Deaths", "count", ("players[].deaths",), "deaths", True, False, direct("deaths")),
    MetricSpec("assists", "Assists", "count", ("players[].assists",), "assists", True, False, direct("assists")),
    MetricSpec(
        "creep_score",
        "Creep score",
        "count",
        ("players[].last_hits", "players[].denies"),
        "last_hits + denies",
        True,
        False,
        creep_score,
        "Creep score is explicitly defined by this project as last hits plus denies.",
    ),
    MetricSpec("gpm", "GPM", "gold_per_minute", ("players[].gold_per_min",), "gold_per_min", True, False, direct("gold_per_min")),
    MetricSpec(
        "runes",
        "Runes",
        "count",
        ("players[].rune_pickups",),
        "rune_pickups",
        True,
        True,
        direct("rune_pickups"),
        "Do not sum players[].runes; the actual EWC payload does not consistently equal rune_pickups.",
    ),
    MetricSpec(
        "teamfight_participation",
        "Teamfight participation",
        "ratio",
        ("players[].teamfight_participation",),
        "teamfight_participation",
        True,
        True,
        direct("teamfight_participation"),
        "Use OpenDota's parsed value; it is not always equal to (kills + assists) / final team score.",
    ),
    MetricSpec(
        "wards",
        "Wards placed",
        "count",
        ("players[].obs_placed", "players[].sen_placed"),
        "obs_placed + sen_placed",
        True,
        True,
        wards,
    ),
    MetricSpec(
        "camps_stacked",
        "Camps stacked",
        "count",
        ("players[].camps_stacked",),
        "camps_stacked",
        True,
        True,
        direct("camps_stacked"),
    ),
    MetricSpec(
        "smokes",
        "Smokes used",
        "count",
        ("players[].item_uses.smoke_of_deceit",),
        "item_uses.get('smoke_of_deceit', 0)",
        True,
        True,
        smoke_uses,
        "This measures uses, not purchases. purchase.smoke_of_deceit is a different statistic.",
    ),
    MetricSpec(
        "roshan_kills",
        "Roshan kills",
        "count",
        ("players[].roshan_kills",),
        "roshan_kills",
        True,
        True,
        direct("roshan_kills"),
        "OpenDota defines this as player last hits on Roshan; do not rebuild it from players[].killed.",
    ),
    MetricSpec(
        "tormentor_kills",
        "Tormentor kills",
        "count",
        ("players[].killed.npc_dota_miniboss",),
        "unavailable",
        False,
        True,
        unavailable,
        "No documented dedicated OpenDota player field exists. The internal killed map is not a reliable substitute.",
    ),
    MetricSpec(
        "courier_kills",
        "Courier kills",
        "count",
        ("players[].courier_kills",),
        "courier_kills",
        True,
        True,
        direct("courier_kills"),
    ),
    MetricSpec("stuns", "Stuns", "seconds", ("players[].stuns",), "stuns", True, True, direct("stuns")),
    MetricSpec(
        "first_blood",
        "First blood",
        "count",
        ("players[].firstblood_claimed",),
        "firstblood_claimed",
        True,
        True,
        direct("firstblood_claimed"),
        "Cross-checkable against objectives[].type == CHAT_MESSAGE_FIRSTBLOOD and player_slot.",
    ),
    MetricSpec(
        "buybacks",
        "Buybacks",
        "count",
        ("players[].buyback_count",),
        "buyback_count",
        True,
        True,
        direct("buyback_count"),
        "Cross-checkable against len(players[].buyback_log).",
    ),
)
METRICS_BY_KEY = {metric.key: metric for metric in METRICS}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(path)


def is_parsed(match: dict[str, Any]) -> bool:
    od_data = match.get("od_data")
    return isinstance(od_data, dict) and od_data.get("has_parsed") is True


def extract(metric: MetricSpec, match: dict[str, Any], player: dict[str, Any]) -> tuple[float | None, str | None]:
    if not metric.reliable:
        return None, "OpenDota cannot reliably provide this metric"
    if metric.requires_parsed_replay and not is_parsed(match):
        return None, "parsed replay data is unavailable"
    value = metric.extractor(match, player)
    if value is None:
        return None, "required source field is missing or non-numeric"
    return value, None


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * probability
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def rounded(value: float) -> int | float:
    if math.isclose(value, round(value), abs_tol=1e-9):
        return int(round(value))
    return round(value, 6)


def summarize(values: list[float], games: int, metric: MetricSpec, reasons: set[str] | None = None) -> dict[str, Any]:
    reasons = reasons or set()
    if not metric.reliable or games == 0 or len(values) != games:
        if not metric.reliable:
            reason = "OpenDota cannot reliably provide this metric"
        elif games == 0:
            reason = "player has no cached EWC matches"
        else:
            reason = "; ".join(sorted(reasons)) or "metric missing from one or more player-match payloads"
        return {
            "availability": "unavailable",
            "unit": metric.unit,
            "observed_games": len(values),
            "total": None,
            "average_per_game": None,
            "p50": None,
            "p75": None,
            "p90": None,
            "reason": reason,
        }
    total = math.fsum(values)
    return {
        "availability": "available",
        "unit": metric.unit,
        "observed_games": games,
        "total": rounded(total),
        "average_per_game": rounded(total / games),
        "p50": rounded(percentile(values, 0.50)),
        "p75": rounded(percentile(values, 0.75)),
        "p90": rounded(percentile(values, 0.90)),
    }


def load_roster(path: Path) -> tuple[dict[int, dict[str, Any]], dict[str, Any], list[str]]:
    roster = read_json(path)
    teams = roster.get("teams") if isinstance(roster, dict) else None
    if not isinstance(teams, list):
        raise ValueError("Roster config must contain a teams array.")
    warnings: list[str] = []
    if not teams:
        warnings.append("TI15 roster is still draft/empty; output contains no players.")
    elif len(teams) != 16:
        raise ValueError(f"A TI15 roster must contain exactly 16 teams; found {len(teams)}.")

    players: dict[int, dict[str, Any]] = {}
    for team in teams:
        if not isinstance(team, dict):
            raise ValueError("Each team must be an object.")
        starters = team.get("players")
        if not isinstance(starters, list) or len(starters) != 5:
            raise ValueError(f"Team {team.get('name', '<unknown>')} must contain exactly five starters.")
        positions: set[int] = set()
        for player in starters:
            if not isinstance(player, dict):
                raise ValueError("Each roster player must be an object.")
            account_id = player.get("account_id")
            position = player.get("position")
            if not isinstance(account_id, int) or account_id <= 0:
                raise ValueError("Every player must have a positive integer account_id.")
            if account_id in players:
                raise ValueError(f"Duplicate roster account_id: {account_id}")
            if position not in {1, 2, 3, 4, 5} or position in positions:
                raise ValueError(f"Team {team.get('name')} must use positions 1 through 5 exactly once.")
            positions.add(position)
            players[account_id] = {
                "account_id": account_id,
                "name": player.get("name"),
                "position": position,
                "team": team.get("name"),
                "team_id": team.get("team_id"),
            }
    return players, roster, warnings


def cached_matches(raw_dir: Path) -> tuple[list[int], list[dict[str, Any]]]:
    league_path = raw_dir / "league_19785_matches.json"
    if not league_path.exists():
        raise FileNotFoundError("League cache is missing. Run scripts/fetch-ewc.py first.")
    league_payload = read_json(league_path)
    league_ids = sorted(
        {
            int(row["match_id"])
            for row in league_payload
            if isinstance(row, dict) and isinstance(row.get("match_id"), int)
        }
    )
    matches: list[dict[str, Any]] = []
    for match_id in league_ids:
        path = raw_dir / "matches" / f"{match_id}.json"
        if not path.exists():
            continue
        match = read_json(path)
        if isinstance(match, dict) and match.get("match_id") == match_id and match.get("leagueid") == LEAGUE_ID:
            matches.append(match)
    return league_ids, matches


def build(raw_dir: Path, roster_path: Path, output_path: Path) -> dict[str, Any]:
    roster_players, roster, warnings = load_roster(roster_path)
    league_ids, matches = cached_matches(raw_dir)
    if len(matches) < len(league_ids):
        warnings.append(f"Only {len(matches)} of {len(league_ids)} league match payloads are cached.")

    games = {account_id: 0 for account_id in roster_players}
    values = {
        account_id: {metric.key: [] for metric in METRICS}
        for account_id in roster_players
    }
    reasons = {
        account_id: {metric.key: set() for metric in METRICS}
        for account_id in roster_players
    }
    for match in matches:
        match_players = match.get("players")
        if not isinstance(match_players, list):
            continue
        seen_in_match: set[int] = set()
        for player in match_players:
            if not isinstance(player, dict):
                continue
            account_id = player.get("account_id")
            if account_id not in roster_players or account_id in seen_in_match:
                continue
            seen_in_match.add(account_id)
            games[account_id] += 1
            for metric in METRICS:
                value, reason = extract(metric, match, player)
                if value is not None:
                    values[account_id][metric.key].append(value)
                elif reason:
                    reasons[account_id][metric.key].add(reason)

    output_players = []
    for account_id, roster_player in roster_players.items():
        player_games = games[account_id]
        output_players.append(
            {
                **roster_player,
                "games_played": player_games,
                "stats": {
                    metric.key: summarize(
                        values[account_id][metric.key],
                        player_games,
                        metric,
                        reasons[account_id][metric.key],
                    )
                    for metric in METRICS
                },
            }
        )
    output_players.sort(key=lambda player: (str(player["team"]), int(player["position"])))
    payload = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "provider": "OpenDota",
            "league_id": LEAGUE_ID,
            "matches_discovered": len(league_ids),
            "matches_processed": len(matches),
            "parsed_matches": sum(is_parsed(match) for match in matches),
        },
        "roster_status": roster.get("status", "unknown"),
        "warnings": warnings,
        "metric_catalog": {metric.key: metric.catalog_entry() for metric in METRICS},
        "players": output_players,
    }
    write_json(output_path, payload)
    return payload


def independent_expected(metric: MetricSpec, match: dict[str, Any], player: dict[str, Any]) -> float | None:
    if not metric.reliable:
        return None
    if metric.requires_parsed_replay and not is_parsed(match):
        return None
    if metric.key == "creep_score":
        left, right = number(player.get("last_hits")), number(player.get("denies"))
        return None if left is None or right is None else left + right
    if metric.key == "wards":
        left, right = number(player.get("obs_placed")), number(player.get("sen_placed"))
        return None if left is None or right is None else left + right
    if metric.key == "smokes":
        uses = player.get("item_uses")
        return number(uses.get("smoke_of_deceit", 0)) if isinstance(uses, dict) else None
    field_by_metric = {
        "kills": "kills",
        "deaths": "deaths",
        "assists": "assists",
        "gpm": "gold_per_min",
        "runes": "rune_pickups",
        "teamfight_participation": "teamfight_participation",
        "camps_stacked": "camps_stacked",
        "roshan_kills": "roshan_kills",
        "courier_kills": "courier_kills",
        "stuns": "stuns",
        "first_blood": "firstblood_claimed",
        "buybacks": "buyback_count",
    }
    return number(player.get(field_by_metric[metric.key]))


def same_number(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-9)


def audit(
    raw_dir: Path,
    output_path: Path,
    match_count: int,
    player_count: int,
    seed: int,
) -> dict[str, Any]:
    _league_ids, matches = cached_matches(raw_dir)
    if len(matches) < match_count:
        raise ValueError(f"Audit requires {match_count} cached matches; found {len(matches)}.")
    rng = random.Random(seed)
    selected_matches = rng.sample(matches, match_count)
    rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for match in selected_matches:
        for player in match.get("players", []):
            if isinstance(player, dict) and isinstance(player.get("account_id"), int):
                rows.append((match, player))
    account_ids = sorted({int(player["account_id"]) for _match, player in rows})
    if len(account_ids) < player_count:
        raise ValueError(f"Audit requires {player_count} unique players; found {len(account_ids)}.")
    selected_accounts: set[int] = set()
    for match in selected_matches:
        candidates = [
            int(player["account_id"])
            for player in match.get("players", [])
            if isinstance(player, dict)
            and isinstance(player.get("account_id"), int)
            and int(player["account_id"]) not in selected_accounts
        ]
        if candidates:
            selected_accounts.add(rng.choice(candidates))
    remaining = [account_id for account_id in account_ids if account_id not in selected_accounts]
    needed = player_count - len(selected_accounts)
    if needed > 0:
        selected_accounts.update(rng.sample(remaining, needed))
    selected_rows = [(match, player) for match, player in rows if player["account_id"] in selected_accounts]

    checks = 0
    player_report = []
    for account_id in sorted(selected_accounts):
        account_rows = [(match, player) for match, player in selected_rows if player["account_id"] == account_id]
        metric_report: dict[str, Any] = {}
        for metric in METRICS:
            extracted_values: list[float] = []
            for match, player in account_rows:
                actual, _reason = extract(metric, match, player)
                expected = independent_expected(metric, match, player)
                checks += 1
                if not same_number(actual, expected):
                    raise AssertionError(
                        f"Audit mismatch: match={match['match_id']} account_id={account_id} "
                        f"metric={metric.key} processed={actual} raw_expected={expected}"
                    )
                if actual is not None:
                    extracted_values.append(actual)
            summary = summarize(extracted_values, len(account_rows), metric)
            if summary["availability"] == "available":
                raw_total = math.fsum(extracted_values)
                raw_average = raw_total / len(account_rows)
                if not same_number(float(summary["total"]), rounded(raw_total)):
                    raise AssertionError(f"Audit total mismatch for account_id={account_id}, metric={metric.key}")
                if not same_number(float(summary["average_per_game"]), rounded(raw_average)):
                    raise AssertionError(f"Audit average mismatch for account_id={account_id}, metric={metric.key}")
                checks += 2
            metric_report[metric.key] = summary
        player_report.append(
            {
                "account_id": account_id,
                "name_from_opendota": account_rows[0][1].get("name") or account_rows[0][1].get("personaname"),
                "match_ids": [int(match["match_id"]) for match, _player in account_rows],
                "stats": metric_report,
            }
        )

    report = {
        "status": "passed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "matches_checked": len(selected_matches),
        "match_ids": sorted(int(match["match_id"]) for match in selected_matches),
        "players_checked": len(selected_accounts),
        "player_match_rows_checked": len(selected_rows),
        "assertions_passed": checks,
        "players": player_report,
    }
    write_json(output_path, report)
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    result.add_argument("--roster", type=Path, default=DEFAULT_ROSTER)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--audit", action="store_true", help="Randomly cross-check processed values against raw JSON.")
    result.add_argument("--audit-output", type=Path, default=DEFAULT_AUDIT_OUTPUT)
    result.add_argument("--audit-matches", type=int, default=5)
    result.add_argument("--audit-players", type=int, default=10)
    result.add_argument("--seed", type=int, default=20260807)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        payload = build(args.raw_dir, args.roster, args.output)
        print(
            f"Processed {payload['source']['matches_processed']} cached matches; "
            f"wrote {len(payload['players'])} roster players to {args.output}"
        )
        for warning in payload["warnings"]:
            print(f"warning: {warning}")
        if args.audit:
            report = audit(
                args.raw_dir,
                args.audit_output,
                args.audit_matches,
                args.audit_players,
                args.seed,
            )
            print(
                f"Audit passed: matches={report['matches_checked']}, players={report['players_checked']}, "
                f"player_match_rows={report['player_match_rows_checked']}, assertions={report['assertions_passed']}"
            )
        return 0
    except (AssertionError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
