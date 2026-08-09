"""Publish validated namespaced artifacts and guarded legacy compatibility aliases."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

from .dataset_config import DatasetConfig, ROOT, load_dataset, load_validation_expectations
from .semantic_compare import (
    DEFAULT_BASELINE,
    DEFAULT_REFERENCE_PATHS,
    compare_artifacts,
    legacy_compatibility_payload,
)


LEGACY_REPORT_PATHS = {
    "dataValidation": ROOT / "DATA_VALIDATION.md",
    "rankingsValidation": ROOT / "RANKINGS_VALIDATION.md",
    "roleRankingsValidation": ROOT / "ROLE_RANKINGS_VALIDATION.md",
}


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def _atomic_write_json(payload: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    temporary.replace(destination)


def candidate_paths(config: DatasetConfig) -> dict[str, Path]:
    return {
        "fantasyMatchScores": config.paths.match_scores,
        "playerFantasyRankings": config.paths.player_rankings,
        "roleFantasyRankings": config.paths.role_rankings,
    }


def validate_expected_scope(config: DatasetConfig, candidates: Mapping[str, Path]) -> list[str]:
    expected = load_validation_expectations(config)
    match_scores = _read_json(candidates["fantasyMatchScores"])
    player_rankings = _read_json(candidates["playerFantasyRankings"])
    role_rankings = _read_json(candidates["roleFantasyRankings"])
    errors: list[str] = []

    for payload_name, payload in (
        ("fantasyMatchScores", match_scores),
        ("playerFantasyRankings", player_rankings),
        ("roleFantasyRankings", role_rankings),
    ):
        if not isinstance(payload, dict):
            errors.append(f"{payload_name} must contain a JSON object")
            continue
        for key, value in config.provenance.items():
            if payload.get(key) != value:
                errors.append(f"{payload_name}.{key} does not match dataset config")

    match_source = match_scores.get("source", {}) if isinstance(match_scores, dict) else {}
    actual_scope = {
        "matchesDiscovered": match_source.get("matchesDiscovered"),
        "matchesProcessed": match_source.get("matchesProcessed"),
        "playerMatchRows": match_source.get("playerMatchRows"),
    }
    players = player_rankings.get("players", []) if isinstance(player_rankings, dict) else []
    if not isinstance(players, list):
        players = []
    player_source = player_rankings.get("source") if isinstance(player_rankings, dict) else None
    if not isinstance(player_source, dict):
        errors.append("playerFantasyRankings.source must be an object")
    else:
        if "ti15Players" in player_source:
            errors.append("Generic playerFantasyRankings.source must not contain ti15Players")
        if player_source.get("rosterPlayers") != len(players):
            errors.append(
                "Generic playerFantasyRankings.source.rosterPlayers differs: "
                f"{player_source.get('rosterPlayers')} != {len(players)}"
            )
    players_with_games = sum(
        isinstance(player, dict) and isinstance(player.get("gamesPlayed"), int) and player["gamesPlayed"] > 0
        for player in players
    )
    units = role_rankings.get("roleUnits", []) if isinstance(role_rankings, dict) else []
    if not isinstance(units, list):
        units = []
    teams = {
        unit.get("teamName")
        for unit in units
        if isinstance(unit, dict) and isinstance(unit.get("teamName"), str)
    }
    actual_scope.update(
        {
            "rosterPlayers": len(players),
            "playersWithGames": players_with_games,
            "playersWithoutGames": len(players) - players_with_games,
            "teams": len(teams),
            "roleUnits": len(units),
        }
    )
    for key, expected_value in expected.items():
        if actual_scope.get(key) != expected_value:
            errors.append(f"Validation scope {key} differs: {actual_scope.get(key)} != {expected_value}")
    return errors


def publish(config: DatasetConfig, baseline_path: Path = DEFAULT_BASELINE) -> list[str]:
    candidates = candidate_paths(config)
    missing = [str(path) for path in candidates.values() if not path.exists()]
    missing.extend(
        str(path)
        for path in (
            config.paths.data_validation,
            config.paths.rankings_validation,
            config.paths.role_validation,
        )
        if not path.exists()
    )
    if missing:
        return [f"Missing candidate artifact: {path}" for path in missing]

    errors = validate_expected_scope(config, candidates)
    if config.dataset_id == "ti15-ewc-2026":
        baseline = _read_json(baseline_path)
        errors.extend(compare_artifacts(baseline, DEFAULT_REFERENCE_PATHS, candidates))
    if errors:
        return errors

    _atomic_copy(config.paths.role_rankings, config.paths.public_role_rankings)

    if config.dataset_id == "ti15-ewc-2026":
        for name, destination in DEFAULT_REFERENCE_PATHS.items():
            if name == "playerFantasyRankings":
                _atomic_write_json(
                    legacy_compatibility_payload(name, _read_json(candidates[name])),
                    destination,
                )
            else:
                _atomic_copy(candidates[name], destination)
        report_sources = {
            "dataValidation": config.paths.data_validation,
            "rankingsValidation": config.paths.rankings_validation,
            "roleRankingsValidation": config.paths.role_validation,
        }
        for name, destination in LEGACY_REPORT_PATHS.items():
            _atomic_copy(report_sources[name], destination)
    return []


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", help="Dataset ID; defaults to the registry default.")
    result.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        config = load_dataset(args.dataset)
        errors = publish(config, args.baseline)
        if errors:
            print("PUBLISH_BLOCKED", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            return 1
        print(f"Published validated dataset: {config.dataset_id}")
        print(f"Public Role rankings: {config.paths.public_role_rankings}")
        if config.dataset_id == "ti15-ewc-2026":
            print("Legacy TI15-EWC compatibility artifacts updated after semantic equality check")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
