"""Central TI15 Fantasy base-scoring rules.

All scoring coefficients and formula parameters live in this module.  The
scoring engine must not embed copies of these numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


RawFormula = Literal["direct", "sum", "map_value", "unavailable"]
ScoreFormula = Literal["multiply", "death_penalty", "unavailable"]
Reliability = Literal["high", "medium", "low", "unavailable"]
BestRawDirection = Literal["higher", "lower"]

SCORE_DECIMAL_PLACES = 6


@dataclass(frozen=True, slots=True)
class FantasyRule:
    key: str
    label: str
    raw_formula: RawFormula
    score_formula: ScoreFormula
    source_paths: tuple[tuple[str, ...], ...] = ()
    points_per_unit: Decimal | None = None
    initial_score: Decimal | None = None
    penalty_per_unit: Decimal | None = None
    zero_after: Decimal | None = None
    requires_parsed_replay: bool = False
    reliability: Reliability = "high"
    unit: str = "count"
    minimum_raw: Decimal | None = Decimal("0")
    maximum_raw: Decimal | None = None
    integer_only: bool = True
    allow_boolean: bool = False
    missing_leaf_means_zero: bool = False
    unavailable_reason: str | None = None
    note: str | None = None
    ranking_key: str | None = None
    best_raw_direction: BestRawDirection = "higher"

    @property
    def output_key(self) -> str:
        return self.ranking_key or self.key


def multiplier_rule(
    key: str,
    label: str,
    source_path: tuple[str, ...],
    points: str,
    *,
    raw_formula: RawFormula = "direct",
    source_paths: tuple[tuple[str, ...], ...] | None = None,
    parsed: bool = False,
    reliability: Reliability = "high",
    unit: str = "count",
    maximum_raw: str | None = None,
    integer_only: bool = True,
    allow_boolean: bool = False,
    missing_leaf_means_zero: bool = False,
    note: str | None = None,
    ranking_key: str | None = None,
) -> FantasyRule:
    return FantasyRule(
        key=key,
        label=label,
        raw_formula=raw_formula,
        score_formula="multiply",
        source_paths=source_paths or (source_path,),
        points_per_unit=Decimal(points),
        requires_parsed_replay=parsed,
        reliability=reliability,
        unit=unit,
        maximum_raw=Decimal(maximum_raw) if maximum_raw is not None else None,
        integer_only=integer_only,
        allow_boolean=allow_boolean,
        missing_leaf_means_zero=missing_leaf_means_zero,
        note=note,
        ranking_key=ranking_key,
    )


def unavailable_rule(
    key: str,
    label: str,
    reason: str,
    *,
    note: str | None = None,
    ranking_key: str | None = None,
) -> FantasyRule:
    return FantasyRule(
        key=key,
        label=label,
        raw_formula="unavailable",
        score_formula="unavailable",
        reliability="unavailable",
        unit="unavailable",
        minimum_raw=None,
        integer_only=False,
        unavailable_reason=reason,
        note=note,
        ranking_key=ranking_key,
    )


RULES: dict[str, FantasyRule] = {
    "kills": multiplier_rule("kills", "Kills", ("kills",), "107"),
    "deaths": FantasyRule(
        key="deaths",
        label="Deaths",
        raw_formula="direct",
        score_formula="death_penalty",
        source_paths=(("deaths",),),
        initial_score=Decimal("1950"),
        penalty_per_unit=Decimal("195"),
        zero_after=Decimal("10"),
        unit="count",
        note="Score is floored at zero; values greater than 10 also score zero.",
        best_raw_direction="lower",
    ),
    "creep_score": multiplier_rule(
        "creep_score",
        "Last hits + denies",
        ("last_hits",),
        "3",
        raw_formula="sum",
        source_paths=(("last_hits",), ("denies",)),
        ranking_key="lastHitsAndDenies",
    ),
    "gpm": multiplier_rule("gpm", "GPM", ("gold_per_min",), "2", unit="gold_per_minute"),
    "madstones": unavailable_rule(
        "madstones",
        "Madstones collected",
        "OpenDota has no confirmed madstones-collected field",
        note="item_uses.madstone_bundle is only a low-reliability candidate and is not scored.",
    ),
    "tower_kills": multiplier_rule(
        "tower_kills", "Tower kills", ("tower_kills",), "352", parsed=True, ranking_key="towerKills"
    ),
    "observer_wards": multiplier_rule(
        "observer_wards",
        "Observer wards placed",
        ("obs_placed",),
        "117",
        parsed=True,
        ranking_key="observerWards",
    ),
    "camps_stacked": multiplier_rule(
        "camps_stacked", "Camps stacked", ("camps_stacked",), "234", parsed=True, ranking_key="campsStacked"
    ),
    "rune_pickups": multiplier_rule(
        "rune_pickups", "Rune pickups", ("rune_pickups",), "141", parsed=True, ranking_key="runes"
    ),
    "watchers": unavailable_rule(
        "watchers", "Watchers captured", "No watcher-capture field exists in the cached OpenDota payloads"
    ),
    "lotuses": unavailable_rule(
        "lotuses", "Lotuses harvested", "No Lotus Pool harvest field exists in the cached OpenDota payloads"
    ),
    "roshan_kills": multiplier_rule(
        "roshan_kills",
        "Roshan kills",
        ("roshans_killed",),
        "1172",
        parsed=True,
        ranking_key="roshanKills",
        note="Use roshans_killed, not the conflicting roshan_kills field.",
    ),
    "teamfight_participation": multiplier_rule(
        "teamfight_participation",
        "Teamfight participation",
        ("teamfight_participation",),
        "2124",
        parsed=True,
        unit="ratio",
        maximum_raw="1",
        integer_only=False,
        ranking_key="teamfightParticipation",
        note="OpenDota supplies a ratio in the inclusive range 0..1.",
    ),
    "stun_duration": multiplier_rule(
        "stun_duration",
        "Stun duration",
        ("stuns",),
        "10",
        parsed=True,
        reliability="medium",
        unit="seconds",
        integer_only=False,
        ranking_key="stunDuration",
        note="Negative parser anomalies are quarantined as unavailable, never clamped to zero.",
    ),
    "tormentor_kills": multiplier_rule(
        "tormentor_kills",
        "Tormentor kills",
        ("killed", "npc_dota_miniboss"),
        "879",
        raw_formula="map_value",
        parsed=True,
        reliability="medium",
        missing_leaf_means_zero=True,
        ranking_key="tormentorKills",
        note="Match totals cross-check, but individual attribution is medium reliability.",
    ),
    "courier_kills": multiplier_rule(
        "courier_kills", "Courier kills", ("courier_kills",), "703", parsed=True, ranking_key="courierKills"
    ),
    "first_blood": multiplier_rule(
        "first_blood",
        "First blood",
        ("firstblood_claimed",),
        "1934",
        parsed=True,
        maximum_raw="1",
        allow_boolean=True,
        ranking_key="firstBlood",
    ),
    "smokes": multiplier_rule(
        "smokes",
        "Smokes used",
        ("item_uses", "smoke_of_deceit"),
        "293",
        raw_formula="map_value",
        parsed=True,
        missing_leaf_means_zero=True,
    ),
}

METRIC_KEYS = tuple(RULES)
UNAVAILABLE_METRICS = tuple(key for key, rule in RULES.items() if rule.score_formula == "unavailable")
