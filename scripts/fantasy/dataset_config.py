"""Load and validate versioned dataset, roster-source, and match-source configs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .rulesets import FantasyRuleset, get_ruleset


ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = ROOT / "data" / "config"
DATASET_INDEX = CONFIG_ROOT / "datasets" / "index.json"
_CONFIG_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _object(payload: Any, label: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _non_negative_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def validate_config_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or _CONFIG_ID.fullmatch(value) is None:
        raise ValueError(f"{label} must contain lowercase letters, numbers, and single hyphens")
    return value


def _repo_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty repository-relative path")
    candidate = (ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as error:
        raise ValueError(f"{label} must stay inside the repository") from error
    return candidate


@dataclass(frozen=True, slots=True)
class DatasetPaths:
    generated_dir: Path
    reports_dir: Path
    public_role_rankings: Path

    @property
    def match_scores(self) -> Path:
        return self.generated_dir / "fantasy-match-scores.json"

    @property
    def player_rankings(self) -> Path:
        return self.generated_dir / "player-fantasy-rankings.json"

    @property
    def role_rankings(self) -> Path:
        return self.generated_dir / "role-fantasy-rankings.json"

    @property
    def data_validation(self) -> Path:
        return self.reports_dir / "DATA_VALIDATION.md"

    @property
    def rankings_validation(self) -> Path:
        return self.reports_dir / "RANKINGS_VALIDATION.md"

    @property
    def role_validation(self) -> Path:
        return self.reports_dir / "ROLE_RANKINGS_VALIDATION.md"


@dataclass(frozen=True, slots=True)
class RosterSource:
    roster_source_id: str
    path: Path
    tournament_code: str
    season: int
    expected_team_count: int
    required_positions: tuple[int, ...]
    account_ids_unique: bool
    team_count: int
    player_count: int


@dataclass(frozen=True, slots=True)
class MatchSource:
    match_source_id: str
    competition_code: str
    season: int
    provider_id: str
    api_base: str
    league_ids: tuple[int, ...]
    cache_namespace: str
    namespaced_raw_dir: Path
    legacy_raw_dir: Path | None
    excluded_match_ids: frozenset[int]
    expected_players_per_match: int

    def raw_dir_for_processing(self) -> Path:
        if any(_league_cache_exists(self.namespaced_raw_dir, league_id) for league_id in self.league_ids):
            return self.namespaced_raw_dir
        if self.legacy_raw_dir is not None and any(
            _league_cache_exists(self.legacy_raw_dir, league_id) for league_id in self.league_ids
        ):
            return self.legacy_raw_dir
        return self.namespaced_raw_dir


@dataclass(frozen=True, slots=True)
class DatasetConfig:
    dataset_id: str
    status: str
    roster: RosterSource
    match_source: MatchSource
    ruleset: FantasyRuleset
    validation_profile: str
    player_ranking_policy: str
    role_ranking_policy: str
    cross_dataset_intersection: bool
    paths: DatasetPaths

    @property
    def provenance(self) -> dict[str, str]:
        return {
            "datasetId": self.dataset_id,
            "rosterSourceId": self.roster.roster_source_id,
            "matchSourceId": self.match_source.match_source_id,
            "rulesetId": self.ruleset.ruleset_id,
        }


def _league_cache_exists(raw_dir: Path, league_id: int) -> bool:
    return (raw_dir / "leagues" / f"{league_id}.json").exists() or (
        raw_dir / f"league_{league_id}_matches.json"
    ).exists()


def _load_roster_source(roster_source_id: str) -> RosterSource:
    path = ROOT / "data" / "rosters" / f"{roster_source_id}.json"
    payload = _object(_read_json(path), f"Roster source {roster_source_id}")
    if payload.get("schemaVersion") != 1:
        raise ValueError(f"Roster source {roster_source_id} must use schemaVersion 1")
    if validate_config_id(payload.get("rosterSourceId"), "rosterSourceId") != roster_source_id:
        raise ValueError(f"Roster source ID does not match {path.name}")
    competition = _object(payload.get("competition"), "roster competition")
    code = competition.get("code")
    if not isinstance(code, str) or not code:
        raise ValueError("Roster competition.code must be a non-empty string")
    season = _positive_int(competition.get("season"), "roster competition.season")
    expectations = _object(payload.get("expectations"), "roster expectations")
    expected_team_count = _positive_int(expectations.get("teamCount"), "roster expectations.teamCount")
    positions = expectations.get("requiredPositions")
    if not isinstance(positions, list) or not positions or any(
        not isinstance(position, int) or isinstance(position, bool) or position <= 0 for position in positions
    ):
        raise ValueError("roster expectations.requiredPositions must contain positive integers")
    if len(set(positions)) != len(positions):
        raise ValueError("roster expectations.requiredPositions must not contain duplicates")
    account_ids_unique = expectations.get("accountIdsUnique")
    if account_ids_unique is not True:
        raise ValueError("roster expectations.accountIdsUnique must be true")

    teams = payload.get("teams")
    if not isinstance(teams, list) or len(teams) != expected_team_count:
        raise ValueError(f"Roster source must contain exactly {expected_team_count} teams")
    account_ids: list[int] = []
    for team in teams:
        players = team.get("players") if isinstance(team, dict) else None
        if not isinstance(players, list) or not players:
            raise ValueError("Every roster team must contain a players array")
        team_players: dict[int, dict[str, Any]] = {}
        players_by_position: dict[int, list[int]] = {}
        for player in players:
            if not isinstance(player, dict):
                raise ValueError("Every roster player must be an object")
            account_id = _positive_int(player.get("account_id"), "roster player account_id")
            if account_id in team_players:
                raise ValueError(f"Team {team.get('name')} contains duplicate account_id {account_id}")
            team_players[account_id] = player
            account_ids.append(account_id)
            position = player.get("position")
            if position is not None:
                validated_position = _positive_int(position, "roster player position")
                players_by_position.setdefault(validated_position, []).append(account_id)

        lineup = team.get("roleLineup")
        if lineup is None:
            for position in positions:
                candidates = players_by_position.get(position, [])
                if len(candidates) != 1:
                    raise ValueError(
                        f"Team {team.get('name')} needs one Position {position} player or an explicit roleLineup"
                    )
        else:
            lineup_payload = _object(lineup, f"Team {team.get('name')} roleLineup")
            if set(lineup_payload) != {str(position) for position in positions}:
                raise ValueError(f"Team {team.get('name')} roleLineup must configure every required position")
            selected_accounts: list[int] = []
            for position in positions:
                selected = _positive_int(
                    lineup_payload[str(position)],
                    f"Team {team.get('name')} roleLineup Position {position}",
                )
                if selected not in team_players:
                    raise ValueError(f"Team {team.get('name')} roleLineup references a non-roster account_id")
                selected_accounts.append(selected)
            if len(set(selected_accounts)) != len(selected_accounts):
                raise ValueError(f"Team {team.get('name')} roleLineup must contain unique players")
    if len(account_ids) != len(set(account_ids)):
        raise ValueError("Roster account_id values must be globally unique")

    return RosterSource(
        roster_source_id=roster_source_id,
        path=path,
        tournament_code=code,
        season=season,
        expected_team_count=expected_team_count,
        required_positions=tuple(positions),
        account_ids_unique=account_ids_unique,
        team_count=len(teams),
        player_count=len(account_ids),
    )


def _load_match_source(match_source_id: str) -> MatchSource:
    path = CONFIG_ROOT / "match-sources" / f"{match_source_id}.json"
    payload = _object(_read_json(path), f"Match source {match_source_id}")
    if payload.get("schemaVersion") != 1:
        raise ValueError(f"Match source {match_source_id} must use schemaVersion 1")
    if validate_config_id(payload.get("matchSourceId"), "matchSourceId") != match_source_id:
        raise ValueError(f"Match source ID does not match {path.name}")
    competition = _object(payload.get("competition"), "match competition")
    competition_code = competition.get("code")
    if not isinstance(competition_code, str) or not competition_code:
        raise ValueError("Match competition.code must be a non-empty string")
    season = _positive_int(competition.get("season"), "match competition.season")
    provider = _object(payload.get("provider"), "match provider")
    provider_id = provider.get("id")
    api_base = provider.get("apiBase")
    if provider_id != "OpenDota" or not isinstance(api_base, str) or not api_base.startswith("https://"):
        raise ValueError("The current match-source adapter requires an HTTPS OpenDota provider")
    league_ids = provider.get("leagueIds")
    if not isinstance(league_ids, list) or not league_ids:
        raise ValueError("provider.leagueIds must be a non-empty array")
    validated_league_ids = tuple(_positive_int(league_id, "provider league ID") for league_id in league_ids)
    if len(set(validated_league_ids)) != len(validated_league_ids):
        raise ValueError("provider.leagueIds must not contain duplicates")
    cache_namespace = validate_config_id(payload.get("cacheNamespace"), "cacheNamespace")
    if cache_namespace != match_source_id:
        raise ValueError("cacheNamespace must equal matchSourceId")
    selection = _object(payload.get("matchSelection"), "matchSelection")
    if selection.get("stages") != "all":
        raise ValueError("Only matchSelection.stages=all is currently supported")
    excluded = selection.get("excludedMatchIds")
    if not isinstance(excluded, list):
        raise ValueError("matchSelection.excludedMatchIds must be an array")
    excluded_ids = frozenset(_positive_int(match_id, "excluded match ID") for match_id in excluded)
    expectations = _object(payload.get("expectations"), "match expectations")
    expected_players = _positive_int(expectations.get("playersPerMatch"), "expectations.playersPerMatch")
    legacy_value = payload.get("legacyCachePath")
    legacy_raw_dir = _repo_path(legacy_value, "legacyCachePath") if legacy_value is not None else None
    return MatchSource(
        match_source_id=match_source_id,
        competition_code=competition_code,
        season=season,
        provider_id=provider_id,
        api_base=api_base,
        league_ids=validated_league_ids,
        cache_namespace=cache_namespace,
        namespaced_raw_dir=ROOT / "data" / "raw" / "match-sources" / cache_namespace,
        legacy_raw_dir=legacy_raw_dir,
        excluded_match_ids=excluded_ids,
        expected_players_per_match=expected_players,
    )


def default_dataset_id() -> str:
    payload = _object(_read_json(DATASET_INDEX), "dataset index")
    if payload.get("schemaVersion") != 1:
        raise ValueError("Dataset index must use schemaVersion 1")
    datasets = payload.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("Dataset index must contain a non-empty datasets array")
    validated = [validate_config_id(dataset_id, "dataset ID") for dataset_id in datasets]
    if len(set(validated)) != len(validated):
        raise ValueError("Dataset index must not contain duplicate IDs")
    default_id = validate_config_id(payload.get("defaultDatasetId"), "defaultDatasetId")
    if default_id not in validated:
        raise ValueError("defaultDatasetId must be listed in datasets")
    return default_id


def load_dataset(dataset_id: str | None = None) -> DatasetConfig:
    selected_id = validate_config_id(dataset_id or default_dataset_id(), "datasetId")
    path = CONFIG_ROOT / "datasets" / f"{selected_id}.json"
    payload = _object(_read_json(path), f"Dataset {selected_id}")
    if payload.get("schemaVersion") != 1:
        raise ValueError(f"Dataset {selected_id} must use schemaVersion 1")
    if validate_config_id(payload.get("datasetId"), "datasetId") != selected_id:
        raise ValueError(f"Dataset ID does not match {path.name}")
    status = payload.get("status")
    if status not in {"draft", "verified", "published"}:
        raise ValueError("Dataset status must be draft, verified, or published")
    roster_source_id = validate_config_id(payload.get("rosterSourceId"), "rosterSourceId")
    match_source_id = validate_config_id(payload.get("matchSourceId"), "matchSourceId")
    ruleset_id = validate_config_id(payload.get("rulesetId"), "rulesetId")
    policy = _object(payload.get("populationPolicy"), "populationPolicy")
    player_policy = policy.get("playerRankings")
    role_policy = policy.get("roleRankings")
    cross_dataset = policy.get("crossDatasetIntersection")
    if player_policy != "all-roster-participants":
        raise ValueError("playerRankings must include all roster participants")
    if role_policy != "configured-role-lineups":
        raise ValueError("roleRankings must use configured role lineups")
    if cross_dataset is not False:
        raise ValueError("crossDatasetIntersection must be false for base datasets")
    validation_profile = validate_config_id(payload.get("validationProfile"), "validationProfile")
    validation_path = CONFIG_ROOT / "validation-profiles" / f"{validation_profile}.json"
    validation_payload = _object(_read_json(validation_path), "validation profile")
    if validation_payload.get("schemaVersion") != 1 or validation_payload.get("validationProfile") != validation_profile:
        raise ValueError(f"Invalid validation profile: {validation_profile}")

    return DatasetConfig(
        dataset_id=selected_id,
        status=status,
        roster=_load_roster_source(roster_source_id),
        match_source=_load_match_source(match_source_id),
        ruleset=get_ruleset(ruleset_id),
        validation_profile=validation_profile,
        player_ranking_policy=player_policy,
        role_ranking_policy=role_policy,
        cross_dataset_intersection=cross_dataset,
        paths=DatasetPaths(
            generated_dir=ROOT / "data" / "generated" / "datasets" / selected_id,
            reports_dir=ROOT / "reports" / selected_id,
            public_role_rankings=ROOT / "public" / "data" / "datasets" / selected_id / "role-fantasy-rankings.json",
        ),
    )


def load_validation_expectations(config: DatasetConfig) -> dict[str, int]:
    path = CONFIG_ROOT / "validation-profiles" / f"{config.validation_profile}.json"
    payload = _object(_read_json(path), "validation profile")
    expected = _object(payload.get("expected"), "validation expected values")
    result = {
        key: _positive_int(value, f"validation expected.{key}")
        for key, value in expected.items()
        if key != "playersWithoutGames"
    }
    if "playersWithoutGames" in expected:
        result["playersWithoutGames"] = _non_negative_int(
            expected["playersWithoutGames"],
            "validation expected.playersWithoutGames",
        )
    return result
