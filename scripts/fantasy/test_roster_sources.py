import json
import tempfile
import unittest
from pathlib import Path

from scripts.fantasy.rankings import _load_roster
from scripts.fantasy.role_rankings import load_role_units


class RosterSourceTests(unittest.TestCase):
    def test_all_participants_are_ranked_but_role_lineup_selects_five(self) -> None:
        roster = {
            "teams": [
                {
                    "name": "Example",
                    "team_id": 1,
                    "players": [
                        {"account_id": 11, "name": "P1", "position": 1},
                        {"account_id": 12, "name": "P2", "position": 2},
                        {"account_id": 13, "name": "P3", "position": 3},
                        {"account_id": 14, "name": "P4", "position": 4},
                        {"account_id": 15, "name": "P5", "position": 5},
                        {"account_id": 16, "name": "Sub", "position": 1},
                    ],
                    "roleLineup": {"1": 11, "2": 12, "3": 13, "4": 14, "5": 15},
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "roster.json"
            path.write_text(json.dumps(roster), encoding="utf-8")
            players = _load_roster(path, expected_team_count=1, expected_player_count=6)
            units = load_role_units(path, expected_teams=1)

        self.assertEqual(len(players), 6)
        self.assertEqual(len(units), 3)
        core = next(unit for unit in units if unit["role"] == "core")
        self.assertEqual([member["playerAccountId"] for member in core["members"]], [11, 13])


if __name__ == "__main__":
    unittest.main()
