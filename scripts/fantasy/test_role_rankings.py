from __future__ import annotations

import unittest

from scripts.fantasy.role_rankings import ROLE_POSITIONS, build_role_match_values, summarize_role_metric
from scripts.fantasy.rules import RULES


def member(account_id: int, name: str, position: int) -> dict[str, object]:
    return {"playerAccountId": account_id, "playerName": name, "position": position}


def row(match_id: int, raw_value: int | float | None, fantasy_score: int | float | None) -> dict[str, object]:
    available = raw_value is not None and fantasy_score is not None
    return {
        "matchId": match_id,
        "fantasy": {
            "kills": {
                "rawValue": raw_value if available else None,
                "baseFantasyScore": fantasy_score if available else None,
                "dataAvailability": "available" if available else "unavailable",
            }
        },
    }


class RoleRankingTests(unittest.TestCase):
    def test_role_definitions_are_fixed(self) -> None:
        self.assertEqual(ROLE_POSITIONS, {"core": (1, 3), "mid": (2,), "support": (4, 5)})

    def test_core_uses_same_match_values_not_individual_bests(self) -> None:
        members = [member(1, "P1", 1), member(3, "P3", 3)]
        rows = {
            1: [row(101, 10, 1070), row(102, 30, 3210)],
            3: [row(101, 40, 4280), row(102, 20, 2140)],
        }
        role_matches = build_role_match_values(members, rows, "kills")
        self.assertEqual([item["rawValue"] for item in role_matches], [25, 25])
        summary = summarize_role_metric(RULES["kills"], role_matches)
        self.assertEqual(summary["best"]["rawValue"], 25)
        self.assertEqual(summary["best"]["fantasyScore"], 2675)
        self.assertEqual(summary["best"]["matchId"], 101)
        self.assertNotEqual(summary["best"]["rawValue"], 35)

    def test_support_uses_same_match_values_not_individual_bests(self) -> None:
        members = [member(4, "P4", 4), member(5, "P5", 5)]
        rows = {
            4: [row(201, 10, 1070), row(202, 30, 3210)],
            5: [row(201, 40, 4280), row(202, 20, 2140)],
        }
        role_matches = build_role_match_values(members, rows, "kills")
        summary = summarize_role_metric(RULES["kills"], role_matches)
        self.assertEqual([item["rawValue"] for item in role_matches], [25, 25])
        self.assertEqual(summary["best"]["rawValue"], 25)
        self.assertNotEqual(summary["best"]["rawValue"], 35)

    def test_mid_is_not_divided_by_two(self) -> None:
        members = [member(2, "P2", 2)]
        rows = {2: [row(301, 10, 1070), row(302, 30, 3210)]}
        role_matches = build_role_match_values(members, rows, "kills")
        summary = summarize_role_metric(RULES["kills"], role_matches)
        self.assertEqual([item["rawValue"] for item in role_matches], [10, 30])
        self.assertEqual(summary["best"]["rawValue"], 30)
        self.assertEqual(summary["average"], {"rawValue": 20, "fantasyScore": 2140, "validGames": 2})

    def test_null_member_invalidates_entire_role_match(self) -> None:
        members = [member(1, "P1", 1), member(3, "P3", 3)]
        rows = {1: [row(401, 10, 1070)], 3: [row(401, None, None)]}
        role_matches = build_role_match_values(members, rows, "kills")
        self.assertEqual(role_matches[0]["rawValue"], None)
        self.assertEqual(role_matches[0]["fantasyScore"], None)
        self.assertEqual(role_matches[0]["dataAvailability"], "unavailable")
        self.assertEqual(summarize_role_metric(RULES["kills"], role_matches), {"best": None, "average": None})

    def test_only_exact_common_match_ids_are_joined(self) -> None:
        members = [member(1, "P1", 1), member(3, "P3", 3)]
        rows = {
            1: [row(501, 10, 1070), row(502, 20, 2140)],
            3: [row(502, 40, 4280), row(503, 30, 3210)],
        }
        role_matches = build_role_match_values(members, rows, "kills")
        self.assertEqual([item["matchId"] for item in role_matches], [502])
        self.assertEqual(role_matches[0]["rawValue"], 30)


if __name__ == "__main__":
    unittest.main()
