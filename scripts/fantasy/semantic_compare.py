"""Capture and compare TI15-EWC Fantasy artifacts without volatile metadata."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE = ROOT / "data" / "baselines" / "ti15-ewc-2026.semantic-sha256.json"
DEFAULT_REFERENCE_PATHS = {
    "fantasyMatchScores": ROOT / "public" / "data" / "fantasy-match-scores.json",
    "playerFantasyRankings": ROOT / "data" / "processed" / "player-fantasy-rankings.json",
    "roleFantasyRankings": ROOT / "data" / "processed" / "role-fantasy-rankings.json",
}
DEFAULT_CANDIDATE_PATHS = {
    "fantasyMatchScores": ROOT
    / "data"
    / "generated"
    / "datasets"
    / "ti15-ewc-2026"
    / "fantasy-match-scores.json",
    "playerFantasyRankings": ROOT
    / "data"
    / "generated"
    / "datasets"
    / "ti15-ewc-2026"
    / "player-fantasy-rankings.json",
    "roleFantasyRankings": ROOT
    / "data"
    / "generated"
    / "datasets"
    / "ti15-ewc-2026"
    / "role-fantasy-rankings.json",
}

_VOLATILE_ROOT_KEYS = {
    "generatedAt",
    "datasetId",
    "rosterSourceId",
    "matchSourceId",
    "rulesetId",
}
_NON_BUSINESS_SOURCE_KEYS = {"matchScoreFile", "leagueIds"}
_COMPATIBILITY_TRANSFORMS = {
    "playerFantasyRankings": "source.rosterPlayers -> source.ti15Players",
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


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return f"<external>/{resolved.name}"


def normalize_semantics(value: Any, path: tuple[str | int, ...] = ()) -> Any:
    """Remove only explicitly approved volatile/provenance fields."""
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if path == () and key in _VOLATILE_ROOT_KEYS:
                continue
            if path == ("source",) and key in _NON_BUSINESS_SOURCE_KEYS:
                continue
            result[key] = normalize_semantics(child, (*path, key))
        return result
    if isinstance(value, list):
        return [normalize_semantics(child, (*path, index)) for index, child in enumerate(value)]
    return value


def legacy_reference_payload(name: str, payload: Any) -> Any:
    """Return the frozen legacy-schema view, tolerating the prior dual-field transition."""
    result = copy.deepcopy(payload)
    if name != "playerFantasyRankings" or not isinstance(result, dict):
        return result
    source = result.get("source")
    if not isinstance(source, dict) or "rosterPlayers" not in source:
        return result
    if source.get("ti15Players") != source["rosterPlayers"]:
        raise ValueError("Legacy player rankings contain conflicting ti15Players and rosterPlayers values")
    source.pop("rosterPlayers")
    return result


def legacy_compatibility_payload(name: str, payload: Any) -> Any:
    """Convert an approved generic artifact schema to its exact legacy compatibility schema."""
    result = copy.deepcopy(payload)
    if name != "playerFantasyRankings":
        return result
    if not isinstance(result, dict) or not isinstance(result.get("source"), dict):
        raise ValueError("Generic player rankings must contain a source object")
    source = result["source"]
    if "ti15Players" in source:
        raise ValueError("Generic player rankings must not contain source.ti15Players")
    roster_players = source.pop("rosterPlayers", None)
    if not isinstance(roster_players, int) or isinstance(roster_players, bool) or roster_players < 0:
        raise ValueError("Generic player rankings must contain a non-negative source.rosterPlayers")
    source["ti15Players"] = roster_players
    return result


def semantic_sha256(payload: Any) -> str:
    canonical = json.dumps(
        normalize_semantics(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def artifact_summary(name: str, payload: Mapping[str, Any]) -> dict[str, int]:
    if name == "fantasyMatchScores":
        matches = payload.get("matches")
        match_rows = matches if isinstance(matches, list) else []
        player_rows = sum(
            len(match.get("players", []))
            for match in match_rows
            if isinstance(match, dict) and isinstance(match.get("players"), list)
        )
        return {"matches": len(match_rows), "playerMatchRows": player_rows}
    if name == "playerFantasyRankings":
        players = payload.get("players")
        player_rows = players if isinstance(players, list) else []
        with_games = sum(
            isinstance(player, dict) and isinstance(player.get("gamesPlayed"), int) and player["gamesPlayed"] > 0
            for player in player_rows
        )
        return {
            "players": len(player_rows),
            "playersWithGames": with_games,
            "playersWithoutGames": len(player_rows) - with_games,
        }
    if name == "roleFantasyRankings":
        units = payload.get("roleUnits")
        role_units = units if isinstance(units, list) else []
        teams = {
            unit.get("teamName")
            for unit in role_units
            if isinstance(unit, dict) and isinstance(unit.get("teamName"), str)
        }
        return {"teams": len(teams), "roleUnits": len(role_units)}
    raise KeyError(f"Unknown artifact: {name}")


def build_baseline(paths: Mapping[str, Path]) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for name, path in paths.items():
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a JSON object")
        reference = legacy_reference_payload(name, payload)
        artifacts[name] = {
            "path": _portable_path(path),
            "semanticSha256": semantic_sha256(reference),
            "summary": artifact_summary(name, payload),
        }
    return {
        "schemaVersion": 1,
        "datasetId": "ti15-ewc-2026",
        "normalization": {
            "ignoredRootKeys": sorted(_VOLATILE_ROOT_KEYS),
            "ignoredSourceKeys": sorted(_NON_BUSINESS_SOURCE_KEYS),
            "compatibilityTransforms": _COMPATIBILITY_TRANSFORMS,
            "numericComparison": "exact-json-value",
            "arrayOrder": "significant",
        },
        "artifacts": artifacts,
    }


def _format_path(path: tuple[str | int, ...]) -> str:
    result = "root"
    for part in path:
        result += f"[{part}]" if isinstance(part, int) else f".{part}"
    return result


def first_difference(left: Any, right: Any, path: tuple[str | int, ...] = ()) -> str | None:
    if type(left) is not type(right):
        return f"{_format_path(path)} type differs: {type(left).__name__} != {type(right).__name__}"
    if isinstance(left, dict):
        left_keys = set(left)
        right_keys = set(right)
        if left_keys != right_keys:
            return (
                f"{_format_path(path)} keys differ: "
                f"missing={sorted(left_keys - right_keys)}, added={sorted(right_keys - left_keys)}"
            )
        for key in left:
            difference = first_difference(left[key], right[key], (*path, key))
            if difference:
                return difference
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{_format_path(path)} length differs: {len(left)} != {len(right)}"
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            difference = first_difference(left_item, right_item, (*path, index))
            if difference:
                return difference
        return None
    if left != right:
        return f"{_format_path(path)} differs: {left!r} != {right!r}"
    return None


def compare_artifacts(
    baseline: Mapping[str, Any],
    reference_paths: Mapping[str, Path],
    candidate_paths: Mapping[str, Path],
) -> list[str]:
    errors: list[str] = []
    baseline_artifacts = baseline.get("artifacts")
    if not isinstance(baseline_artifacts, dict):
        return ["Baseline does not contain an artifacts object"]

    for name in DEFAULT_REFERENCE_PATHS:
        expected = baseline_artifacts.get(name)
        if not isinstance(expected, dict) or not isinstance(expected.get("semanticSha256"), str):
            errors.append(f"Baseline is missing {name}")
            continue
        reference = _read_json(reference_paths[name])
        candidate = _read_json(candidate_paths[name])
        try:
            reference_view = legacy_reference_payload(name, reference)
            candidate_view = legacy_compatibility_payload(name, candidate)
        except ValueError as error:
            errors.append(f"{name}: compatibility schema error: {error}")
            continue
        reference_hash = semantic_sha256(reference_view)
        candidate_hash = semantic_sha256(candidate_view)
        expected_hash = expected["semanticSha256"]
        if reference_hash != expected_hash:
            errors.append(
                f"{name}: legacy reference changed before compatibility publication "
                f"({reference_hash} != {expected_hash})"
            )
            continue
        if candidate_hash != expected_hash:
            difference = first_difference(normalize_semantics(reference_view), normalize_semantics(candidate_view))
            errors.append(
                f"{name}: semantic hash differs ({candidate_hash} != {expected_hash}); "
                f"first difference: {difference or 'canonical JSON differs'}"
            )
    return errors


def _artifact_args(result: argparse.ArgumentParser, prefix: str, defaults: Mapping[str, Path]) -> None:
    for name, path in defaults.items():
        option = name.replace("Fantasy", "-fantasy-").replace("Scores", "-scores").replace("Rankings", "-rankings")
        result.add_argument(f"--{prefix}-{option.lower()}", dest=f"{prefix}_{name}", type=Path, default=path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    baseline = subparsers.add_parser("baseline", help="Capture current compatibility artifact hashes.")
    baseline.add_argument("--output", type=Path, default=DEFAULT_BASELINE)
    _artifact_args(baseline, "reference", DEFAULT_REFERENCE_PATHS)

    compare = subparsers.add_parser("compare", help="Compare namespaced artifacts with the frozen baseline.")
    compare.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    _artifact_args(compare, "reference", DEFAULT_REFERENCE_PATHS)
    _artifact_args(compare, "candidate", DEFAULT_CANDIDATE_PATHS)
    return result


def _paths_from_args(args: argparse.Namespace, prefix: str) -> dict[str, Path]:
    return {name: getattr(args, f"{prefix}_{name}") for name in DEFAULT_REFERENCE_PATHS}


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "baseline":
            payload = build_baseline(_paths_from_args(args, "reference"))
            _write_json(args.output, payload)
            print(f"Captured TI15-EWC semantic baseline: {_portable_path(args.output)}")
            for name, item in payload["artifacts"].items():
                print(f"  {name}: {item['semanticSha256']} {item['summary']}")
            return 0

        baseline = _read_json(args.baseline)
        errors = compare_artifacts(
            baseline,
            _paths_from_args(args, "reference"),
            _paths_from_args(args, "candidate"),
        )
        if errors:
            print("SEMANTIC_DIFFERENCE", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            return 1
        print("SEMANTIC_MATCH: all TI15-EWC business fields are exactly equal")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
