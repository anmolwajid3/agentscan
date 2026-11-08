import unittest

from adr_pilot.report import _confirmed, _reversal_groups


class AdoptionDateTests(unittest.TestCase):
    def test_earliest_signal_is_the_coauthor_not_the_later_file(self):
        project = {
            "signal_date": "2024-06-01T00:00:00Z",
            "signal_kind": "coauthor",
            "ai_signals": [
                {"kind": "file:primary", "official": True, "date": "2026-01-01T00:00:00Z", "name": "CLAUDE.md"},
                {"kind": "coauthor", "official": True, "date": "2024-06-01T00:00:00Z", "name": "Copilot"},
            ],
            "mentions": {
                "strict": [
                    {"date": "2018-02-26T00:00:00Z", "subject": "Notify Copilot on route creation", "sha": "m1"}
                ]
            },
        }
        result = _confirmed(project)
        self.assertEqual(result["adoption_kind"], "coauthor")
        self.assertTrue(result["adoption_date"].startswith("2024-06-01"))
        self.assertEqual(result["gap_days"], 0.0)
        self.assertTrue(result["earliest_mention"].startswith("2018-02-26"))

    def test_file_before_coauthor_keeps_the_gap(self):
        project = {
            "ai_signals": [
                {"kind": "file:primary", "official": True, "date": "2024-01-01T00:00:00Z", "name": "AGENTS.md"},
                {"kind": "coauthor", "official": True, "date": "2024-06-01T00:00:00Z", "name": "Copilot"},
            ],
            "mentions": {"strict": []},
        }
        result = _confirmed(project)
        self.assertEqual(result["adoption_kind"], "file:primary")
        self.assertGreater(result["gap_days"], 90)

    def test_no_coauthor_is_missing_not_zero(self):
        project = {
            "ai_signals": [
                {"kind": "file:primary", "official": True, "date": "2026-01-01T00:00:00Z", "name": "AGENTS.md"}
            ],
            "mentions": {"strict": []},
        }
        result = _confirmed(project)
        self.assertIsNone(result["gap_days"])
        self.assertIsNone(result["strong_use_date"])
        self.assertFalse(result["confirmed"])

    def test_undated_reversal_is_not_placed_in_a_group(self):
        projects = [
            {
                "clone_ok": True,
                "likely_template": False,
                "group": "ai-eligible",
                "signal_date": "2024-01-01T00:00:00Z",
                "adrs": [
                    {"status": "superseded", "first_commit": "2023-01-01T00:00:00Z"},
                    {"status": "superseded", "first_commit": "2025-01-01T00:00:00Z"},
                    {"status": "superseded", "first_commit": None},
                    {"status": "accepted", "first_commit": "2020-01-01T00:00:00Z"},
                ],
            },
            {
                "clone_ok": True,
                "likely_template": False,
                "group": "non-ai-eligible",
                "signal_date": None,
                "adrs": [{"status": "superseded", "first_commit": "2019-01-01T00:00:00Z"}],
            },
        ]
        groups = _reversal_groups(projects)
        self.assertEqual(groups["reversals_ai_before"], 1)
        self.assertEqual(groups["reversals_ai_after"], 1)
        self.assertEqual(groups["reversals_non_ai"], 1)
        self.assertEqual(groups["reversals_undated"], 1)


if __name__ == "__main__":
    unittest.main()
