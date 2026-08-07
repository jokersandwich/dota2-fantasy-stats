from __future__ import annotations

import unittest

from scripts.fantasy.rules import METRIC_KEYS
from scripts.fantasy.scoring import calculate_stat_score, score_player_match


class CalculateStatScoreTests(unittest.TestCase):
    def assert_score(self, metric: str, raw_value: object, expected: int | float) -> None:
        result = calculate_stat_score(metric, raw_value)
        self.assertEqual(result["dataAvailability"], "available")
        self.assertEqual(result["baseFantasyScore"], expected)

    def test_zero_kills(self) -> None:
        self.assert_score("kills", 0, 0)

    def test_multiple_kills(self) -> None:
        self.assert_score("kills", 8, 856)

    def test_zero_deaths(self) -> None:
        self.assert_score("deaths", 0, 1950)

    def test_ten_deaths(self) -> None:
        self.assert_score("deaths", 10, 0)

    def test_more_than_ten_deaths_scores_zero(self) -> None:
        self.assert_score("deaths", 11, 0)
        self.assert_score("deaths", 25, 0)

    def test_gpm(self) -> None:
        self.assert_score("gpm", 680, 1360)

    def test_teamfight_participation_bounds(self) -> None:
        self.assert_score("teamfight_participation", 0, 0)
        self.assert_score("teamfight_participation", 1, 2124)

    def test_first_blood_true_false(self) -> None:
        self.assert_score("first_blood", True, 1934)
        self.assert_score("first_blood", False, 0)

    def test_all_multiplier_formulas(self) -> None:
        expected = {
            "kills": (2, 214),
            "creep_score": (2, 6),
            "gpm": (2, 4),
            "tower_kills": (2, 704),
            "observer_wards": (2, 234),
            "camps_stacked": (2, 468),
            "rune_pickups": (2, 282),
            "roshan_kills": (2, 2344),
            "teamfight_participation": (0.5, 1062),
            "stun_duration": (2.5, 25),
            "tormentor_kills": (2, 1758),
            "courier_kills": (2, 1406),
            "first_blood": (1, 1934),
            "smokes": (2, 586),
        }
        for metric, (raw_value, score) in expected.items():
            with self.subTest(metric=metric):
                self.assert_score(metric, raw_value, score)

    def test_unavailable_metrics_are_null(self) -> None:
        for metric in ("madstones", "watchers", "lotuses"):
            with self.subTest(metric=metric):
                result = calculate_stat_score(metric, 99)
                self.assertEqual(result["dataAvailability"], "unavailable")
                self.assertIsNone(result["rawValue"])
                self.assertIsNone(result["baseFantasyScore"])

    def test_missing_data_is_null(self) -> None:
        result = calculate_stat_score("kills", None)
        self.assertEqual(result["dataAvailability"], "unavailable")
        self.assertIsNone(result["rawValue"])
        self.assertIsNone(result["baseFantasyScore"])

    def test_negative_stun_is_quarantined_not_clamped(self) -> None:
        result = calculate_stat_score("stun_duration", -0.5835204)
        self.assertEqual(result["dataAvailability"], "unavailable")
        self.assertIsNone(result["rawValue"])
        self.assertIsNone(result["baseFantasyScore"])

    def test_out_of_range_teamfight_is_unavailable(self) -> None:
        result = calculate_stat_score("teamfight_participation", 1.01)
        self.assertEqual(result["dataAvailability"], "unavailable")
        self.assertIsNone(result["baseFantasyScore"])


class PlayerMatchScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.match = {"match_id": 123, "od_data": {"has_parsed": True}}
        self.player = {
            "account_id": 42,
            "name": "Malr1ne",
            "player_slot": 0,
            "hero_id": 1,
            "isRadiant": True,
            "kills": 8,
            "deaths": 3,
            "last_hits": 300,
            "denies": 20,
            "gold_per_min": 680,
            "tower_kills": 1,
            "obs_placed": 0,
            "camps_stacked": 2,
            "rune_pickups": 5,
            "roshans_killed": 1,
            "teamfight_participation": 0.5,
            "stuns": 4.5,
            "killed": {},
            "courier_kills": 0,
            "firstblood_claimed": 1,
            "item_uses": {},
        }

    def test_last_hits_plus_denies(self) -> None:
        result = score_player_match(self.match, self.player)
        self.assertEqual(result["stats"]["creep_score"], 320)
        self.assertEqual(result["fantasy"]["creep_score"]["baseFantasyScore"], 960)

    def test_per_metric_output_shape(self) -> None:
        result = score_player_match(self.match, self.player)
        self.assertEqual(set(result["fantasy"]), set(METRIC_KEYS))
        for item in result["fantasy"].values():
            self.assertIn("rawValue", item)
            self.assertIn("baseFantasyScore", item)
            self.assertIn("dataAvailability", item)

    def test_missing_nested_event_means_zero_when_parent_map_exists(self) -> None:
        result = score_player_match(self.match, self.player)
        self.assertEqual(result["stats"]["tormentor_kills"], 0)
        self.assertEqual(result["stats"]["smokes"], 0)
        self.assertEqual(result["fantasy"]["smokes"]["baseFantasyScore"], 0)

    def test_full_total_is_null_when_any_metric_unavailable(self) -> None:
        result = score_player_match(self.match, self.player)
        self.assertEqual(result["dataAvailability"], "partial")
        self.assertIsNone(result["baseFantasyScore"])
        self.assertGreater(result["availableBaseFantasyScore"], 0)


if __name__ == "__main__":
    unittest.main()
