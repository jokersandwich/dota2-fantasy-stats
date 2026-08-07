from __future__ import annotations

import unittest

from scripts.fantasy.rankings import summarize_raw_values


class RankingSummaryTests(unittest.TestCase):
    def test_forward_metric_uses_highest_score_and_arithmetic_mean(self) -> None:
        summary = summarize_raw_values("kills", [10, 20, 30])
        self.assertEqual(summary["best"]["rawValue"], 30)
        self.assertEqual(summary["best"]["fantasyScore"], 3210)
        self.assertEqual(summary["average"], {"rawValue": 20, "fantasyScore": 2140, "validGames": 3})

    def test_inverse_death_metric_uses_fantasy_score_not_max_raw(self) -> None:
        summary = summarize_raw_values("deaths", [2, 5, 11])
        self.assertEqual(summary["best"]["rawValue"], 2)
        self.assertEqual(summary["best"]["fantasyScore"], 1560)
        self.assertNotEqual(summary["best"]["rawValue"], 11)

    def test_inverse_tie_uses_lower_raw_then_match_id(self) -> None:
        summary = summarize_raw_values("deaths", [12, 11, 11])
        self.assertEqual(summary["best"], {"rawValue": 11, "fantasyScore": 0, "matchId": 2})

    def test_null_values_do_not_participate_in_average(self) -> None:
        summary = summarize_raw_values("kills", [10, None, 30])
        self.assertEqual(summary["best"]["rawValue"], 30)
        self.assertEqual(summary["average"], {"rawValue": 20, "fantasyScore": 2140, "validGames": 2})

    def test_all_null_returns_null_best_and_average(self) -> None:
        self.assertEqual(summarize_raw_values("kills", [None, None]), {"best": None, "average": None})

    def test_first_blood_average_is_a_ratio(self) -> None:
        summary = summarize_raw_values("first_blood", [0, 1, 0, 1])
        self.assertEqual(summary["best"]["rawValue"], 1)
        self.assertEqual(summary["average"], {"rawValue": 0.5, "fantasyScore": 967, "validGames": 4})

    def test_teamfight_average_remains_zero_to_one(self) -> None:
        summary = summarize_raw_values("teamfight_participation", [0.25, 0.75])
        self.assertEqual(summary["average"], {"rawValue": 0.5, "fantasyScore": 1062, "validGames": 2})


if __name__ == "__main__":
    unittest.main()
