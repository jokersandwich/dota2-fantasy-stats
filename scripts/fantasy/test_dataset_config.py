import unittest
from unittest.mock import patch

from scripts.fantasy.dataset_config import default_dataset_id, load_dataset, load_validation_expectations
from scripts.fantasy.rules import RULES
from scripts.fantasy.rulesets import get_ruleset


class DatasetConfigTests(unittest.TestCase):
    def test_default_dataset_is_current_ti15(self) -> None:
        self.assertEqual(default_dataset_id(), "ti15")
        config = load_dataset()
        self.assertEqual(config.dataset_id, "ti15")
        self.assertEqual(config.roster.roster_source_id, "ti15-main-2026")
        self.assertEqual(config.match_source.match_source_id, "ti15-2026-opendota")
        self.assertEqual(config.match_source.league_ids, (19719,))

    def test_current_roster_invariants_are_configured(self) -> None:
        roster = load_dataset().roster
        self.assertEqual(roster.team_count, 16)
        self.assertEqual(roster.player_count, 80)
        self.assertEqual(roster.required_positions, (1, 2, 3, 4, 5))

    def test_current_ruleset_reuses_verified_rule_objects(self) -> None:
        ruleset = get_ruleset("ti15-base-v1")
        self.assertEqual(tuple(ruleset.rules), tuple(RULES))
        self.assertIs(ruleset.rules["kills"], RULES["kills"])

    def test_ti14_composes_independent_sources_with_shared_ruleset(self) -> None:
        config = load_dataset("ti14")
        self.assertEqual(config.dataset_id, "ti14")
        self.assertEqual(config.roster.roster_source_id, "ti14-2025")
        self.assertEqual(config.match_source.match_source_id, "ti14-2025-opendota")
        self.assertEqual(config.match_source.league_ids, (18324,))
        self.assertEqual(config.ruleset.ruleset_id, "ti15-base-v1")
        self.assertEqual(config.roster.player_count, 80)
        self.assertEqual(len(config.match_source.manifest_match_ids or ()), 144)

    def test_ti14_first_blood_override_is_manifest_bounded(self) -> None:
        config = load_dataset("ti14")
        expected_ids = {8446311496, 8457152687, 8457241577}
        actual_ids = set(config.metric_availability_overrides["first_blood"])
        self.assertEqual(actual_ids, expected_ids)
        self.assertTrue(actual_ids.issubset(set(config.match_source.manifest_match_ids or ())))

    def test_validation_profile_matches_frozen_scope(self) -> None:
        expected = load_validation_expectations(load_dataset())
        self.assertEqual(expected["matchesProcessed"], 109)
        self.assertEqual(expected["rosterPlayers"], 80)
        self.assertEqual(expected["roleUnits"], 48)

    def test_validation_profile_allows_zero_players_without_games(self) -> None:
        config = load_dataset()
        with patch(
            "scripts.fantasy.dataset_config._read_json",
            return_value={"expected": {"playersWithoutGames": 0}},
        ):
            expected = load_validation_expectations(config)
        self.assertEqual(expected, {"playersWithoutGames": 0})

    def test_other_expected_counts_remain_strictly_positive(self) -> None:
        config = load_dataset()
        with patch(
            "scripts.fantasy.dataset_config._read_json",
            return_value={"expected": {"rosterPlayers": 0}},
        ):
            with self.assertRaisesRegex(ValueError, "positive integer"):
                load_validation_expectations(config)


if __name__ == "__main__":
    unittest.main()
