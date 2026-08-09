"""Versioned registry for shared Fantasy scoring rulesets."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .rules import METRIC_KEYS, RULES, SCORE_DECIMAL_PLACES, FantasyRule


@dataclass(frozen=True, slots=True)
class FantasyRuleset:
    ruleset_id: str
    rules: Mapping[str, FantasyRule]
    metric_keys: tuple[str, ...]
    score_decimal_places: int


TI15_BASE_V1 = FantasyRuleset(
    ruleset_id="ti15-base-v1",
    rules=MappingProxyType(RULES),
    metric_keys=METRIC_KEYS,
    score_decimal_places=SCORE_DECIMAL_PLACES,
)

_RULESETS = {TI15_BASE_V1.ruleset_id: TI15_BASE_V1}


def get_ruleset(ruleset_id: str) -> FantasyRuleset:
    try:
        return _RULESETS[ruleset_id]
    except KeyError as error:
        raise ValueError(f"Unknown Fantasy ruleset: {ruleset_id}") from error
