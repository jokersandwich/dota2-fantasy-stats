import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.fantasy.semantic_compare import (
    build_baseline,
    compare_artifacts,
    first_difference,
    legacy_compatibility_payload,
    normalize_semantics,
    semantic_sha256,
)


class SemanticCompareTests(unittest.TestCase):
    def test_approved_provenance_does_not_change_hash(self) -> None:
        legacy = {
            "schemaVersion": 1,
            "generatedAt": "before",
            "source": {"leagueId": 19785, "matchScoreFile": "legacy.json"},
            "players": [{"accountId": 1, "score": 10}],
        }
        candidate = {
            "schemaVersion": 1,
            "generatedAt": "after",
            "datasetId": "ti15-ewc-2026",
            "rosterSourceId": "ti15-2026",
            "matchSourceId": "ewc-2026-opendota",
            "rulesetId": "ti15-base-v1",
            "source": {
                "leagueId": 19785,
                "leagueIds": [19785],
                "matchScoreFile": "namespaced.json",
            },
            "players": [{"accountId": 1, "score": 10}],
        }
        self.assertEqual(semantic_sha256(legacy), semantic_sha256(candidate))

    def test_approved_roster_field_rename_matches_legacy_semantics(self) -> None:
        references_payload = {
            "fantasyMatchScores": {"matches": []},
            "playerFantasyRankings": {"source": {"ti15Players": 0}, "players": []},
            "roleFantasyRankings": {"roleUnits": []},
        }
        candidates_payload = deepcopy(references_payload)
        candidates_payload["playerFantasyRankings"]["source"] = {"rosterPlayers": 0}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            references: dict[str, Path] = {}
            candidates: dict[str, Path] = {}
            for name in references_payload:
                reference = root / f"reference-{name}.json"
                candidate = root / f"candidate-{name}.json"
                reference.write_text(json.dumps(references_payload[name]), encoding="utf-8")
                candidate.write_text(json.dumps(candidates_payload[name]), encoding="utf-8")
                references[name] = reference
                candidates[name] = candidate
            errors = compare_artifacts(build_baseline(references), references, candidates)

        self.assertEqual(errors, [])

    def test_legacy_compatibility_output_contains_only_ti15_field(self) -> None:
        converted = legacy_compatibility_payload(
            "playerFantasyRankings",
            {"source": {"rosterPlayers": 80}, "players": []},
        )
        self.assertEqual(converted["source"], {"ti15Players": 80})

    def test_generic_schema_rejects_dual_roster_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not contain source.ti15Players"):
            legacy_compatibility_payload(
                "playerFantasyRankings",
                {"source": {"rosterPlayers": 80, "ti15Players": 80}, "players": []},
            )

    def test_business_value_change_is_detected(self) -> None:
        left = normalize_semantics({"players": [{"score": 10}]})
        right = normalize_semantics({"players": [{"score": 11}]})
        difference = first_difference(left, right)
        self.assertIn("root.players[0].score", difference or "")

    def test_array_order_is_significant(self) -> None:
        self.assertNotEqual(semantic_sha256({"ids": [1, 2]}), semantic_sha256({"ids": [2, 1]}))

    def test_numeric_json_type_is_significant(self) -> None:
        difference = first_difference({"value": 1}, {"value": 1.0})
        self.assertIn("type differs", difference or "")

    def test_candidate_business_difference_blocks_publication(self) -> None:
        fixtures = {
            "fantasyMatchScores": {"matches": []},
            "playerFantasyRankings": {"source": {"ti15Players": 0}, "players": []},
            "roleFantasyRankings": {"roleUnits": []},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            references: dict[str, Path] = {}
            candidates: dict[str, Path] = {}
            for name, payload in fixtures.items():
                reference = root / f"reference-{name}.json"
                candidate = root / f"candidate-{name}.json"
                reference.write_text(json.dumps(payload), encoding="utf-8")
                candidate_payload = deepcopy(payload)
                if name == "playerFantasyRankings":
                    candidate_payload["source"] = {"rosterPlayers": 0}
                candidate.write_text(json.dumps(candidate_payload), encoding="utf-8")
                references[name] = reference
                candidates[name] = candidate
            candidates["roleFantasyRankings"].write_text(
                json.dumps({"roleUnits": [{"teamName": "Changed"}]}),
                encoding="utf-8",
            )
            errors = compare_artifacts(build_baseline(references), references, candidates)

        self.assertEqual(len(errors), 1)
        self.assertIn("roleFantasyRankings", errors[0])
        self.assertIn("semantic hash differs", errors[0])


if __name__ == "__main__":
    unittest.main()
